-- =====================================================
-- ReelsBot Database Migration V2 (FIXED)
-- Separates Director Mode videos from Series episodes
-- Clean architecture for scalability
-- =====================================================

-- =====================================================
-- 1. DIRECTOR VIDEOS TABLE
-- One-off videos created in Director Mode
-- =====================================================
CREATE TABLE IF NOT EXISTS director_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    video_id TEXT UNIQUE NOT NULL,
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generating',

    -- Script and content
    script JSONB,

    -- Assets
    image_urls TEXT[],
    audio_url TEXT,
    video_url TEXT,

    -- Configuration
    config JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Assembly tracking
    assembly_job_id UUID,
    assembly_progress INTEGER DEFAULT 0,
    assembly_stage TEXT,
    assembly_log TEXT,
    assembly_started_at TIMESTAMPTZ,
    assembly_completed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for director_videos
CREATE INDEX IF NOT EXISTS idx_director_videos_user_id ON director_videos(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_director_videos_video_id ON director_videos(video_id);
CREATE INDEX IF NOT EXISTS idx_director_videos_status ON director_videos(status, created_at DESC);

-- =====================================================
-- 2. ADD MISSING COLUMNS TO EPISODES
-- =====================================================
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS video_id TEXT;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS assembly_job_id UUID;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS assembly_progress INTEGER DEFAULT 0;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS assembly_stage TEXT;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS assembly_log TEXT;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS assembly_started_at TIMESTAMPTZ;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS assembly_completed_at TIMESTAMPTZ;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}'::JSONB;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS script JSONB;
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS image_urls TEXT[];
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS audio_url TEXT;

-- Create unique index on video_id for episodes
CREATE UNIQUE INDEX IF NOT EXISTS idx_episodes_video_id ON episodes(video_id) WHERE video_id IS NOT NULL;

-- =====================================================
-- 3. ADD MISSING COLUMNS TO SERIES
-- =====================================================
ALTER TABLE series ADD COLUMN IF NOT EXISTS total_episodes INTEGER DEFAULT 0;
ALTER TABLE series ADD COLUMN IF NOT EXISTS active_episodes INTEGER DEFAULT 0;
ALTER TABLE series ADD COLUMN IF NOT EXISTS failed_episodes INTEGER DEFAULT 0;
ALTER TABLE series ADD COLUMN IF NOT EXISTS last_episode_at TIMESTAMPTZ;
ALTER TABLE series ADD COLUMN IF NOT EXISTS next_episode_at TIMESTAMPTZ;

-- Indexes for episodes
CREATE INDEX IF NOT EXISTS idx_episodes_series_id ON episodes(series_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status, created_at DESC);

-- =====================================================
-- 4. ASSEMBLY JOBS TABLE (Enhanced)
-- =====================================================
ALTER TABLE assembly_jobs ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'director';
ALTER TABLE assembly_jobs ADD COLUMN IF NOT EXISTS source_id UUID;

-- Index for assembly jobs
CREATE INDEX IF NOT EXISTS idx_assembly_jobs_source ON assembly_jobs(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_assembly_jobs_status_priority ON assembly_jobs(status, priority DESC, created_at ASC)
    WHERE status IN ('pending', 'retry');

-- =====================================================
-- 5. MIGRATE EXISTING DATA
-- =====================================================

-- Step 1: Create video_id for episodes that don't have one
UPDATE episodes
SET video_id = gen_random_uuid()::text
WHERE video_id IS NULL;

-- Step 2: Insert existing videos into director_videos (non-series videos only)
INSERT INTO director_videos (
    id,
    user_id,
    video_id,
    topic,
    status,
    script,
    image_urls,
    audio_url,
    video_url,
    config,
    assembly_progress,
    assembly_stage,
    assembly_log,
    assembly_started_at,
    assembly_completed_at,
    created_at,
    updated_at
)
SELECT
    gen_random_uuid(),
    COALESCE(user_id, 'demo_user'),
    video_id,
    COALESCE(topic, 'Untitled'),
    COALESCE(status, 'completed'),
    script,
    image_urls,
    audio_url,
    video_url,
    COALESCE(config, '{}'::jsonb),
    COALESCE(assembly_progress, 0),
    assembly_stage,
    assembly_log,
    assembly_started_at,
    assembly_completed_at,
    created_at,
    updated_at
FROM videos
WHERE NOT EXISTS (
    SELECT 1 FROM episodes WHERE episodes.video_id = videos.video_id
)
ON CONFLICT (video_id) DO NOTHING;

-- Step 3: Update episodes with data from videos table (where video_id matches)
UPDATE episodes e
SET
    video_url = v.video_url,
    script = v.script,
    image_urls = v.image_urls,
    audio_url = v.audio_url,
    config = COALESCE(v.config, '{}'::jsonb),
    assembly_progress = COALESCE(v.assembly_progress, 0),
    assembly_stage = v.assembly_stage,
    assembly_log = v.assembly_log,
    assembly_started_at = v.assembly_started_at,
    assembly_completed_at = v.assembly_completed_at
FROM videos v
WHERE e.video_id IS NOT NULL
  AND e.video_id = v.video_id;

-- Step 4: Update assembly_jobs with source info
UPDATE assembly_jobs aj
SET
    source_type = CASE
        WHEN EXISTS (SELECT 1 FROM episodes WHERE video_id = aj.video_id) THEN 'episode'
        ELSE 'director'
    END,
    source_id = CASE
        WHEN EXISTS (SELECT 1 FROM episodes WHERE video_id = aj.video_id)
        THEN (SELECT id FROM episodes WHERE video_id = aj.video_id LIMIT 1)
        ELSE (SELECT id FROM director_videos WHERE video_id = aj.video_id LIMIT 1)
    END
WHERE aj.source_type IS NULL OR aj.source_id IS NULL;

-- Step 5: Update series statistics
UPDATE series s
SET
    total_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = s.id),
    active_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = s.id AND status IN ('completed', 'generating')),
    failed_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = s.id AND status = 'failed'),
    last_episode_at = (SELECT MAX(created_at) FROM episodes WHERE series_id = s.id)
WHERE EXISTS (SELECT 1 FROM episodes WHERE series_id = s.id);

-- =====================================================
-- 6. UPDATE CLAIM FUNCTION FOR NEW SCHEMA
-- =====================================================
CREATE OR REPLACE FUNCTION claim_assembly_job(
    worker_id TEXT,
    lock_seconds INTEGER DEFAULT 900
)
RETURNS TABLE (
    id UUID,
    video_id TEXT,
    status TEXT,
    priority INTEGER,
    attempts INTEGER,
    max_attempts INTEGER,
    payload JSONB,
    locked_at TIMESTAMPTZ,
    locked_by TEXT,
    last_error TEXT,
    next_run_at TIMESTAMPTZ,
    source_type TEXT,
    source_id UUID,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_job_id UUID;
BEGIN
    -- Find and lock a job atomically
    SELECT aj.id INTO v_job_id
    FROM assembly_jobs aj
    WHERE aj.status IN ('pending', 'retry')
        AND (aj.next_run_at IS NULL OR aj.next_run_at <= NOW())
        AND (aj.locked_at IS NULL OR aj.locked_at < NOW() - (lock_seconds || ' seconds')::INTERVAL)
    ORDER BY aj.priority DESC, aj.created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    -- Update and return the job if found
    IF v_job_id IS NOT NULL THEN
        RETURN QUERY
        UPDATE assembly_jobs aj
        SET
            status = 'running',
            locked_by = worker_id,
            locked_at = NOW(),
            updated_at = NOW()
        WHERE aj.id = v_job_id
        RETURNING
            aj.id,
            aj.video_id,
            aj.status,
            aj.priority,
            aj.attempts,
            aj.max_attempts,
            aj.payload,
            aj.locked_at,
            aj.locked_by,
            aj.last_error,
            aj.next_run_at,
            aj.source_type,
            aj.source_id,
            aj.created_at,
            aj.updated_at;
    END IF;
END;
$$;

-- =====================================================
-- 7. TRIGGERS FOR AUTO-UPDATING STATISTICS
-- =====================================================

-- Update series statistics on episode changes
CREATE OR REPLACE FUNCTION update_series_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE series
        SET
            total_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = NEW.series_id),
            active_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = NEW.series_id AND status IN ('completed', 'generating')),
            failed_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = NEW.series_id AND status = 'failed'),
            last_episode_at = (SELECT MAX(created_at) FROM episodes WHERE series_id = NEW.series_id),
            updated_at = NOW()
        WHERE id = NEW.series_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE series
        SET
            total_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = OLD.series_id),
            active_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = OLD.series_id AND status IN ('completed', 'generating')),
            failed_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = OLD.series_id AND status = 'failed'),
            last_episode_at = (SELECT MAX(created_at) FROM episodes WHERE series_id = OLD.series_id),
            updated_at = NOW()
        WHERE id = OLD.series_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_series_stats ON episodes;
CREATE TRIGGER trigger_update_series_stats
    AFTER INSERT OR UPDATE OR DELETE ON episodes
    FOR EACH ROW
    EXECUTE FUNCTION update_series_stats();

-- Auto-update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_director_videos_updated_at ON director_videos;
CREATE TRIGGER trigger_director_videos_updated_at
    BEFORE UPDATE ON director_videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trigger_episodes_updated_at ON episodes;
CREATE TRIGGER trigger_episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- =====================================================
-- 8. GRANT PERMISSIONS
-- =====================================================
GRANT ALL ON director_videos TO authenticated, anon, service_role;
GRANT ALL ON episodes TO authenticated, anon, service_role;
GRANT ALL ON series TO authenticated, anon, service_role;
GRANT ALL ON assembly_jobs TO authenticated, anon, service_role;

-- =====================================================
-- 9. FORCE POSTGREST RELOAD
-- =====================================================
NOTIFY pgrst, 'reload schema';

-- =====================================================
-- VERIFICATION
-- =====================================================
SELECT 'Migration Complete!' as status;
SELECT 'Director Videos: ' || COUNT(*)::text as count FROM director_videos;
SELECT 'Episodes: ' || COUNT(*)::text as count FROM episodes;
SELECT 'Series: ' || COUNT(*)::text as count FROM series;
SELECT 'Assembly Jobs: ' || COUNT(*)::text as count FROM assembly_jobs;
