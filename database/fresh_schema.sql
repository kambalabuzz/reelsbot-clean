-- =====================================================
-- ReelsBot Fresh Database Schema
-- Clean installation without migration dependencies
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. SERIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS series (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    niche TEXT DEFAULT 'entertainment',
    art_style TEXT DEFAULT 'cinematic',
    voice TEXT DEFAULT 'adam',
    schedule TEXT,
    total_episodes INTEGER DEFAULT 0,
    active_episodes INTEGER DEFAULT 0,
    failed_episodes INTEGER DEFAULT 0,
    last_episode_at TIMESTAMPTZ,
    next_episode_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 2. EPISODES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id UUID REFERENCES series(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    video_id TEXT,
    topic TEXT NOT NULL,
    status TEXT DEFAULT 'pending',

    -- Content
    script JSONB,
    image_urls TEXT[],
    audio_url TEXT,
    video_url TEXT,

    -- Configuration
    config JSONB DEFAULT '{}'::JSONB,

    -- Assembly tracking
    assembly_job_id UUID,
    assembly_progress INTEGER DEFAULT 0,
    assembly_stage TEXT,
    assembly_log TEXT,
    assembly_started_at TIMESTAMPTZ,
    assembly_completed_at TIMESTAMPTZ,

    -- Error tracking
    error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ
);

-- =====================================================
-- 3. DIRECTOR VIDEOS TABLE
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

-- =====================================================
-- 4. ASSEMBLY JOBS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS assembly_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Job payload
    payload JSONB NOT NULL,

    -- Locking mechanism
    locked_at TIMESTAMPTZ,
    locked_by TEXT,

    -- Error tracking
    last_error TEXT,

    -- Retry mechanism
    next_run_at TIMESTAMPTZ,

    -- Source tracking
    source_type TEXT DEFAULT 'director',
    source_id UUID,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =====================================================
-- 5. SOCIAL ACCOUNTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    account_id TEXT,
    account_name TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, platform, account_id)
);

-- =====================================================
-- 6. INDEXES
-- =====================================================

-- Series indexes
CREATE INDEX IF NOT EXISTS idx_series_user_id ON series(user_id);

-- Episodes indexes
CREATE INDEX IF NOT EXISTS idx_episodes_user_id ON episodes(user_id);
CREATE INDEX IF NOT EXISTS idx_episodes_series_id ON episodes(series_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_scheduled_at ON episodes(scheduled_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_episodes_video_id ON episodes(video_id) WHERE video_id IS NOT NULL;

-- Director videos indexes
CREATE INDEX IF NOT EXISTS idx_director_videos_user_id ON director_videos(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_director_videos_video_id ON director_videos(video_id);
CREATE INDEX IF NOT EXISTS idx_director_videos_status ON director_videos(status, created_at DESC);

-- Assembly jobs indexes
CREATE INDEX IF NOT EXISTS idx_assembly_jobs_video_id ON assembly_jobs(video_id);
CREATE INDEX IF NOT EXISTS idx_assembly_jobs_source ON assembly_jobs(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_assembly_jobs_status_priority ON assembly_jobs(status, priority DESC, created_at ASC)
    WHERE status IN ('pending', 'retry');

-- Social accounts indexes
CREATE INDEX IF NOT EXISTS idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform);

-- =====================================================
-- 7. FUNCTIONS
-- =====================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update series statistics
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

-- Claim assembly job (atomic locking)
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
-- 8. TRIGGERS
-- =====================================================

-- Series updated_at trigger
DROP TRIGGER IF EXISTS trigger_series_updated_at ON series;
CREATE TRIGGER trigger_series_updated_at
    BEFORE UPDATE ON series
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Episodes updated_at trigger
DROP TRIGGER IF EXISTS trigger_episodes_updated_at ON episodes;
CREATE TRIGGER trigger_episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Director videos updated_at trigger
DROP TRIGGER IF EXISTS trigger_director_videos_updated_at ON director_videos;
CREATE TRIGGER trigger_director_videos_updated_at
    BEFORE UPDATE ON director_videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Social accounts updated_at trigger
DROP TRIGGER IF EXISTS trigger_social_accounts_updated_at ON social_accounts;
CREATE TRIGGER trigger_social_accounts_updated_at
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Series stats trigger
DROP TRIGGER IF EXISTS trigger_update_series_stats ON episodes;
CREATE TRIGGER trigger_update_series_stats
    AFTER INSERT OR UPDATE OR DELETE ON episodes
    FOR EACH ROW
    EXECUTE FUNCTION update_series_stats();

-- =====================================================
-- 9. ROW LEVEL SECURITY
-- =====================================================

ALTER TABLE series ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE director_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;

-- Series policies
DROP POLICY IF EXISTS "Users can view own series" ON series;
CREATE POLICY "Users can view own series" ON series FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own series" ON series;
CREATE POLICY "Users can insert own series" ON series FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own series" ON series;
CREATE POLICY "Users can update own series" ON series FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own series" ON series;
CREATE POLICY "Users can delete own series" ON series FOR DELETE USING (true);

-- Episodes policies
DROP POLICY IF EXISTS "Users can view own episodes" ON episodes;
CREATE POLICY "Users can view own episodes" ON episodes FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own episodes" ON episodes;
CREATE POLICY "Users can insert own episodes" ON episodes FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own episodes" ON episodes;
CREATE POLICY "Users can update own episodes" ON episodes FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own episodes" ON episodes;
CREATE POLICY "Users can delete own episodes" ON episodes FOR DELETE USING (true);

-- Director videos policies
DROP POLICY IF EXISTS "Users can view own director videos" ON director_videos;
CREATE POLICY "Users can view own director videos" ON director_videos FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own director videos" ON director_videos;
CREATE POLICY "Users can insert own director videos" ON director_videos FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own director videos" ON director_videos;
CREATE POLICY "Users can update own director videos" ON director_videos FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own director videos" ON director_videos;
CREATE POLICY "Users can delete own director videos" ON director_videos FOR DELETE USING (true);

-- Social accounts policies
DROP POLICY IF EXISTS "Users can view own social accounts" ON social_accounts;
CREATE POLICY "Users can view own social accounts" ON social_accounts FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert own social accounts" ON social_accounts;
CREATE POLICY "Users can insert own social accounts" ON social_accounts FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Users can update own social accounts" ON social_accounts;
CREATE POLICY "Users can update own social accounts" ON social_accounts FOR UPDATE USING (true);

DROP POLICY IF EXISTS "Users can delete own social accounts" ON social_accounts;
CREATE POLICY "Users can delete own social accounts" ON social_accounts FOR DELETE USING (true);

-- =====================================================
-- 10. GRANT PERMISSIONS
-- =====================================================
GRANT ALL ON series TO authenticated, anon, service_role;
GRANT ALL ON episodes TO authenticated, anon, service_role;
GRANT ALL ON director_videos TO authenticated, anon, service_role;
GRANT ALL ON assembly_jobs TO authenticated, anon, service_role;
GRANT ALL ON social_accounts TO authenticated, anon, service_role;

-- =====================================================
-- 11. STORAGE BUCKET
-- =====================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('videos', 'videos', true)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 12. FORCE POSTGREST RELOAD
-- =====================================================
NOTIFY pgrst, 'reload schema';

-- =====================================================
-- VERIFICATION
-- =====================================================
SELECT 'Schema installation complete!' as status;
SELECT 'Series: ' || COUNT(*)::text as count FROM series;
SELECT 'Episodes: ' || COUNT(*)::text as count FROM episodes;
SELECT 'Director Videos: ' || COUNT(*)::text as count FROM director_videos;
SELECT 'Assembly Jobs: ' || COUNT(*)::text as count FROM assembly_jobs;
SELECT 'Social Accounts: ' || COUNT(*)::text as count FROM social_accounts;
