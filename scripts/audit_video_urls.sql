-- ============================================================
--  KINGSHORT VIDEO URL AUDIT
--  Jalankan di VPS: docker exec -i <postgres_container> psql -U postgres -d kingshort
-- ============================================================

-- 1. TOTAL EPISODE AKTIF
SELECT COUNT(*) AS total_active_episodes
FROM episodes
WHERE is_active = true;

-- 2. EPISODE DARI R2 KITA (stream.shortlovers.id)
SELECT COUNT(*) AS r2_episodes
FROM episodes
WHERE is_active = true
  AND (
    video_url LIKE '%shortlovers.id%'
    OR video_url LIKE '%.r2.dev%'
    OR video_url LIKE '%.r2.cloudflarestorage.com%'
  );

-- 3. EPISODE DARI SERVER EXTERNAL (bukan R2 kita)
SELECT COUNT(*) AS external_episodes
FROM episodes
WHERE is_active = true
  AND video_url NOT LIKE '%shortlovers.id%'
  AND video_url NOT LIKE '%.r2.dev%'
  AND video_url NOT LIKE '%.r2.cloudflarestorage.com%';

-- 4. DRAMA MANA SAJA YANG MASIH PUNYA EXTERNAL URL
SELECT d.title,
       COUNT(e.id)             AS external_ep_count,
       SUBSTRING(MIN(e.video_url), 1, 80) AS sample_url
FROM episodes e
JOIN dramas d ON d.id = e.drama_id
WHERE e.is_active = true
  AND e.video_url NOT LIKE '%shortlovers.id%'
  AND e.video_url NOT LIKE '%.r2.dev%'
  AND e.video_url NOT LIKE '%.r2.cloudflarestorage.com%'
GROUP BY d.title
ORDER BY external_ep_count DESC;

-- ============================================================
--  AUDIT 540p
-- ============================================================

-- 5. EPISODE YANG PUNYA 540p
SELECT COUNT(*) AS episodes_with_540p
FROM episodes
WHERE is_active = true
  AND video_url_540p IS NOT NULL
  AND video_url_540p != '';

-- 6. EPISODE TANPA 540p
SELECT COUNT(*) AS episodes_without_540p
FROM episodes
WHERE is_active = true
  AND (video_url_540p IS NULL OR video_url_540p = '');

-- 7. DRAMA DENGAN SEMUA EPISODE SUDAH ADA 540p VS BELUM
SELECT
  SUM(CASE WHEN has_540 THEN 1 ELSE 0 END) AS dramas_with_540p,
  SUM(CASE WHEN NOT has_540 THEN 1 ELSE 0 END) AS dramas_without_540p
FROM (
  SELECT drama_id,
         BOOL_AND(video_url_540p IS NOT NULL AND video_url_540p != '') AS has_540
  FROM episodes
  WHERE is_active = true
  GROUP BY drama_id
) sub;

-- 8. LIST DRAMA YANG BELUM ADA 540p SAMA SEKALI
SELECT d.title, COUNT(e.id) AS episode_count
FROM dramas d
JOIN episodes e ON e.drama_id = d.id
WHERE e.is_active = true
  AND d.id NOT IN (
    SELECT DISTINCT drama_id FROM episodes
    WHERE is_active = true
      AND video_url_540p IS NOT NULL AND video_url_540p != ''
  )
GROUP BY d.title
ORDER BY episode_count DESC;
