#!/usr/bin/env python3
"""
One-time migration script to add video_url_540p column to episodes table.
This is a VPS-side script — run it on the production VPS.

Usage: python3 /tmp/add_540p_column.py
"""

import subprocess
import sys

DB_CONTAINER = "b9ea5fe215a0"

def run_psql(sql, description=""):
    """Run SQL via docker exec psql."""
    cmd = [
        "docker", "exec", "-i", DB_CONTAINER,
        "psql", "-U", "postgres", "-c", sql
    ]
    print(f"\n{'='*50}")
    if description:
        print(f"[{description}]")
    print(f"SQL: {sql}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    error = result.stderr.strip()
    
    if output:
        print(f"Output: {output}")
    if error:
        print(f"Error: {error}", file=sys.stderr)
    
    return result.returncode == 0, output

def main():
    print("Starting migration: Add video_url_540p column to episodes table")
    
    # Step 1: Check if column already exists
    success, output = run_psql(
        "SELECT column_name FROM information_schema.columns WHERE table_name='episodes' AND column_name='video_url_540p';",
        "Check if column exists"
    )
    
    if 'video_url_540p' in output:
        print("\n✓ Column video_url_540p ALREADY EXISTS!")
        
        # Show how many episodes already have 540p
        run_psql(
            "SELECT COUNT(*) as total, COUNT(video_url_540p) as with_540p FROM episodes WHERE is_active = true;",
            "Count 540p coverage"
        )
        return
    
    # Step 2: Add the column
    print("\nColumn does not exist. Adding it now...")
    success, output = run_psql(
        "ALTER TABLE episodes ADD COLUMN video_url_540p text;",
        "Add column"
    )
    
    if not success:
        print("FAILED to add column! Check error above.")
        sys.exit(1)
    
    # Step 3: Verify
    success, output = run_psql(
        "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='episodes' AND column_name='video_url_540p';",
        "Verify column added"
    )
    
    if 'video_url_540p' in output:
        print("\n✅ SUCCESS! Column video_url_540p has been added to episodes table.")
        print("\nNext steps:")
        print("  1. The backfill script (/tmp/backfill_540p_mass.py) should now be able to store 540p URLs")
        print("  2. If backfill is done, re-run it to patch already-processed episodes")
        print("  3. Or restart backfill from checkpoint")
    else:
        print("\n❌ Column not found after ALTER. Something went wrong.")
        sys.exit(1)

if __name__ == '__main__':
    main()
