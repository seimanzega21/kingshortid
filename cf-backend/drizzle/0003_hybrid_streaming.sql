ALTER TABLE "dramas" ADD COLUMN "provider_name" text;
ALTER TABLE "dramas" ADD COLUMN "source_movie_id" text;
ALTER TABLE "dramas" ADD COLUMN "real_views" integer DEFAULT 0 NOT NULL;

ALTER TABLE "episodes" ADD COLUMN "source_episode_id" text;
ALTER TABLE "episodes" ALTER COLUMN "video_url" DROP NOT NULL;
