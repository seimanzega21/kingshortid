#!/usr/bin/env python3
"""
R2 CLEANUP & AUDIT TOOL
========================
1. Abort stuck multipart uploads
2. Audit R2 contents vs database
3. Report missing/incomplete dramas

Usage:
  python r2_cleanup_audit.py              # Audit only (dry run)
  python r2_cleanup_audit.py --cleanup    # Abort stuck uploads + audit
"""
import os, sys, json, requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# ── Config ──
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
BACKEND_URL = "http://localhost:3001/api"

def get_s3():
    import boto3
    return boto3.client("s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto"
    )

# ── 1. ABORT STUCK MULTIPART UPLOADS ──
def abort_stuck_uploads(s3, dry_run=True):
    print("\n" + "=" * 60)
    print("  STEP 1: CHECK STUCK MULTIPART UPLOADS")
    print("=" * 60)

    try:
        response = s3.list_multipart_uploads(Bucket=R2_BUCKET)
        uploads = response.get("Uploads", [])
    except Exception as e:
        print(f"  ⚠️ Error listing multipart uploads: {e}")
        return 0

    if not uploads:
        print("  ✅ No stuck multipart uploads found!")
        return 0

    print(f"  Found {len(uploads)} stuck multipart upload(s):\n")
    for u in uploads:
        key = u["Key"]
        upload_id = u["UploadId"]
        initiated = u.get("Initiated", "?")
        print(f"  ❌ {key}")
        print(f"     Upload ID: {upload_id[:20]}... | Started: {initiated}")

        if not dry_run:
            try:
                s3.abort_multipart_upload(
                    Bucket=R2_BUCKET,
                    Key=key,
                    UploadId=upload_id
                )
                print(f"     ✅ ABORTED")
            except Exception as e:
                print(f"     ⚠️ Failed to abort: {e}")
        else:
            print(f"     ⏸️ DRY RUN — use --cleanup to abort")

    return len(uploads)

# ── 2. LIST ALL R2 OBJECTS ──
def list_r2_objects(s3):
    print("\n" + "=" * 60)
    print("  STEP 2: SCANNING R2 CONTENTS")
    print("=" * 60)

    all_objects = []
    continuation_token = None

    while True:
        kwargs = {"Bucket": R2_BUCKET, "Prefix": "melolo/", "MaxKeys": 1000}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = s3.list_objects_v2(**kwargs)
        contents = response.get("Contents", [])
        all_objects.extend(contents)

        if response.get("IsTruncated"):
            continuation_token = response.get("NextContinuationToken")
        else:
            break

    print(f"  Found {len(all_objects)} objects in R2 (melolo/ prefix)")
    return all_objects

# ── 3. ORGANIZE BY DRAMA ──
def organize_by_drama(objects):
    dramas = defaultdict(lambda: {"episodes": [], "cover": False, "total_size": 0})

    for obj in objects:
        key = obj["Key"]  # e.g. "melolo/slug/ep001.mp4" or "melolo/slug/cover.jpg"
        parts = key.split("/")
        if len(parts) < 3:
            continue

        slug = parts[1]
        filename = parts[2]
        size = obj.get("Size", 0)

        dramas[slug]["total_size"] += size

        if filename.startswith("cover") or filename.endswith((".jpg", ".jpeg", ".png", ".webp")):
            dramas[slug]["cover"] = True
        elif filename.endswith(".mp4"):
            dramas[slug]["episodes"].append(filename)

    return dict(dramas)

# ── 4. GET DATABASE DRAMAS ──
def get_db_dramas():
    print("\n" + "=" * 60)
    print("  STEP 3: FETCHING DATABASE DRAMAS")
    print("=" * 60)

    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=9999&includeInactive=true", timeout=15)
        if r.status_code == 200:
            data = r.json()
            dramas = data if isinstance(data, list) else data.get("dramas", [])
            print(f"  Found {len(dramas)} dramas in database")
            return dramas
        else:
            print(f"  ⚠️ Backend returned {r.status_code}")
            return []
    except Exception as e:
        print(f"  ⚠️ Backend error: {e}")
        return []

# ── 5. CROSS-REFERENCE AUDIT ──
def audit(r2_dramas, db_dramas):
    print("\n" + "=" * 60)
    print("  STEP 4: CROSS-REFERENCE AUDIT")
    print("=" * 60)

    # Build slug lookup from DB
    def slugify(text):
        import re
        s = re.sub(r'[^a-z0-9\s-]', '', text.lower())
        return re.sub(r'[\s-]+', '-', s).strip('-')

    db_by_slug = {}
    for d in db_dramas:
        slug = slugify(d.get("title", ""))
        db_by_slug[slug] = d

    # Dramas in R2 but not in DB
    r2_only = []
    for slug in r2_dramas:
        if slug not in db_by_slug:
            r2_only.append(slug)

    # Dramas in DB but not in R2
    db_only = []
    for slug, drama in db_by_slug.items():
        if slug not in r2_dramas:
            db_only.append(drama)

    # Dramas in both — check episode count match
    mismatched = []
    matched = 0
    for slug in r2_dramas:
        if slug in db_by_slug:
            r2_ep_count = len(r2_dramas[slug]["episodes"])
            db_ep_count = db_by_slug[slug].get("totalEpisodes", 0)
            if r2_ep_count < db_ep_count:
                mismatched.append({
                    "title": db_by_slug[slug].get("title", slug),
                    "slug": slug,
                    "r2_eps": r2_ep_count,
                    "db_eps": db_ep_count,
                    "missing": db_ep_count - r2_ep_count,
                    "has_cover": r2_dramas[slug]["cover"],
                })
            else:
                matched += 1

    # Print results
    print(f"\n  ✅ Matched (R2 ≥ DB): {matched}")

    if mismatched:
        print(f"\n  ⚠️ Episode Mismatch (R2 < DB): {len(mismatched)}")
        mismatched.sort(key=lambda x: x["missing"], reverse=True)
        for m in mismatched[:20]:
            print(f"     {m['title']}: R2={m['r2_eps']} vs DB={m['db_eps']} (missing {m['missing']} eps)")

    if r2_only:
        print(f"\n  📦 In R2 but NOT in DB: {len(r2_only)}")
        for slug in sorted(r2_only)[:15]:
            info = r2_dramas[slug]
            print(f"     {slug}: {len(info['episodes'])} eps, cover={'✅' if info['cover'] else '❌'}")

    if db_only:
        print(f"\n  🗄️ In DB but NOT in R2: {len(db_only)}")
        for d in sorted(db_only, key=lambda x: x.get("title", ""))[:15]:
            print(f"     {d.get('title', '?')}: {d.get('totalEpisodes', 0)} eps")

    # Summary
    total_r2_eps = sum(len(d["episodes"]) for d in r2_dramas.values())
    total_r2_size_gb = sum(d["total_size"] for d in r2_dramas.values()) / (1024**3)
    total_db_eps = sum(d.get("totalEpisodes", 0) for d in db_dramas)

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  R2: {len(r2_dramas)} dramas, {total_r2_eps} episodes, {total_r2_size_gb:.1f} GB")
    print(f"  DB: {len(db_dramas)} dramas, {total_db_eps} episodes")
    print(f"  Matched: {matched} | Mismatched: {len(mismatched)} | R2-only: {len(r2_only)} | DB-only: {len(db_only)}")

    return {
        "matched": matched,
        "mismatched": mismatched,
        "r2_only": r2_only,
        "db_only": db_only,
    }

# ── MAIN ──
def main():
    do_cleanup = "--cleanup" in sys.argv

    print("=" * 60)
    print("  R2 CLEANUP & AUDIT TOOL")
    print(f"  Mode: {'CLEANUP + AUDIT' if do_cleanup else 'AUDIT ONLY (dry run)'}")
    print("=" * 60)

    s3 = get_s3()

    # Step 1: Abort stuck uploads
    stuck = abort_stuck_uploads(s3, dry_run=not do_cleanup)

    # Step 2: Scan R2
    objects = list_r2_objects(s3)
    r2_dramas = organize_by_drama(objects)
    print(f"  Organized into {len(r2_dramas)} drama folders")

    # Step 3: Get DB
    db_dramas = get_db_dramas()

    # Step 4: Audit
    if db_dramas:
        results = audit(r2_dramas, db_dramas)

        # Save report
        report = {
            "stuck_uploads": stuck,
            "r2_dramas_count": len(r2_dramas),
            "db_dramas_count": len(db_dramas),
            "matched": results["matched"],
            "mismatched_count": len(results["mismatched"]),
            "mismatched": results["mismatched"],
            "r2_only": results["r2_only"],
            "db_only_titles": [d.get("title", "?") for d in results["db_only"]],
        }
        with open("r2_audit_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  📄 Report saved: r2_audit_report.json")

    print(f"\n{'=' * 60}")
    if not do_cleanup and stuck > 0:
        print(f"  ⚠️ Run with --cleanup to abort {stuck} stuck uploads")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
