-- Migration 0002: Add video_url_540p column to episodes table
-- Run this on production PostgreSQL to enable 540p quality support

ALTER TABLE episodes ADD COLUMN IF NOT EXISTS video_url_540p text;

-- Verify the column was added
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'episodes' AND column_name = 'video_url_540p';
