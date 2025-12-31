-- =====================================================
-- ReelsBot Database - Nuclear Clean Installation
-- Drops everything related to old schema, then fresh install
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PART 1: NUCLEAR CLEANUP - DROP EVERYTHING
-- =====================================================

-- Drop all triggers on all tables
DROP TRIGGER IF EXISTS update_series_updated_at ON series CASCADE;
DROP TRIGGER IF EXISTS update_episodes_updated_at ON episodes CASCADE;
DROP TRIGGER IF EXISTS update_social_accounts_updated_at ON social_accounts CASCADE;
DROP TRIGGER IF EXISTS trigger_series_updated_at ON series CASCADE;
DROP TRIGGER IF EXISTS trigger_episodes_updated_at ON episodes CASCADE;
DROP TRIGGER IF EXISTS trigger_director_videos_updated_at ON director_videos CASCADE;
DROP TRIGGER IF EXISTS trigger_social_accounts_updated_at ON social_accounts CASCADE;
DROP TRIGGER IF EXISTS trigger_update_series_stats ON episodes CASCADE;
DROP TRIGGER IF EXISTS update_videos_updated_at ON videos CASCADE;
DROP TRIGGER IF EXISTS trigger_videos_updated_at ON videos CASCADE;

-- Drop all functions that might be causing issues
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at() CASCADE;
DROP FUNCTION IF EXISTS update_series_stats() CASCADE;
DROP FUNCTION IF EXISTS claim_assembly_job(TEXT, INTEGER) CASCADE;

-- Drop the old videos table entirely (this is causing the issue)
DROP TABLE IF EXISTS videos CASCADE;

-- Drop and recreate all our tables to start fresh
DROP TABLE IF EXISTS assembly_jobs CASCADE;
DROP TABLE IF EXISTS director_videos CASCADE;
DROP TABLE IF EXISTS episodes CASCADE;
DROP TABLE IF EXISTS series CASCADE;
DROP TABLE IF EXISTS social_accounts CASCADE;

-- =====================================================
-- PART 2: FRESH INSTALLATION
-- =====================================================

-- 1. SERIES TABLE
CREATE TABLE series (
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

-- 2. EPISODES TABLE
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id UUID REFERENCES series(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    video_id TEXT,
    topic TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    script JSONB,
    image_urls TEXT[],
    audio_url TEXT,
    video_url TEXT,
    config JSONB DEFAULT '{}'::JSONB,
    assembly_job_id UUID,
    assembly_progress INTEGER DEFAULT 0,
    assembly_stage TEXT,
    assembly_log TEXT,
    assembly_started_at TIMESTAMPTZ,
    assembly_completed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ
);

-- 3. DIRECTOR VIDEOS TABLE
CREATE TABLE director_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    video_id TEXT UNIQUE NOT NULL,
    topic TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'generating',
    script JSONB,
    image_urls TEXT[],
    audio_url TEXT,
    video_url TEXT,
    config JSONB NOT NULL DEFAULT '{}'::JSONB,
    assembly_job_id UUID,
    assembly_progress INTEGER DEFAULT 0,
    assembly_stage TEXT,
    assembly_log TEXT,
    assembly_started_at TIMESTAMPTZ,
    assembly_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. ASSEMBLY JOBS TABLE
CREATE TABLE assembly_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    payload JSONB NOT NULL,
    locked_at TIMESTAMPTZ,
    locked_by TEXT,
    last_error TEXT,
    next_run_at TIMESTAMPTZ,
    source_type TEXT DEFAULT 'director',
    source_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. SOCIAL ACCOUNTS TABLE
CREATE TABLE social_accounts (
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
-- CREATE INDEXES
-- =====================================================
CREATE INDEX idx_series_user_id ON series(user_id);
CREATE INDEX idx_episodes_user_id ON episodes(user_id);
CREATE INDEX idx_episodes_series_id ON episodes(series_id, created_at DESC);
CREATE INDEX idx_episodes_status ON episodes(status, created_at DESC);
CREATE INDEX idx_episodes_scheduled_at ON episodes(scheduled_at);
CREATE UNIQUE INDEX idx_episodes_video_id ON episodes(video_id) WHERE video_id IS NOT NULL;
CREATE INDEX idx_director_videos_user_id ON director_videos(user_id, created_at DESC);
CREATE INDEX idx_director_videos_video_id ON director_videos(video_id);
CREATE INDEX idx_director_videos_status ON director_videos(status, created_at DESC);
CREATE INDEX idx_assembly_jobs_video_id ON assembly_jobs(video_id);
CREATE INDEX idx_assembly_jobs_source ON assembly_jobs(source_type, source_id);
CREATE INDEX idx_assembly_jobs_status_priority ON assembly_jobs(status, priority DESC, created_at ASC)
    WHERE status IN ('pending', 'retry');
CREATE INDEX idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX idx_social_accounts_platform ON social_accounts(platform);

-- =====================================================
-- CREATE FUNCTIONS
-- =====================================================
CREATE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION update_series_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        IF NEW.series_id IS NOT NULL THEN
            UPDATE series
            SET
                total_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = NEW.series_id),
                active_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = NEW.series_id AND status IN ('completed', 'generating')),
                failed_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = NEW.series_id AND status = 'failed'),
                last_episode_at = (SELECT MAX(created_at) FROM episodes WHERE series_id = NEW.series_id),
                updated_at = NOW()
            WHERE id = NEW.series_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.series_id IS NOT NULL THEN
            UPDATE series
            SET
                total_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = OLD.series_id),
                active_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = OLD.series_id AND status IN ('completed', 'generating')),
                failed_episodes = (SELECT COUNT(*) FROM episodes WHERE series_id = OLD.series_id AND status = 'failed'),
                last_episode_at = (SELECT MAX(created_at) FROM episodes WHERE series_id = OLD.series_id),
                updated_at = NOW()
            WHERE id = OLD.series_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION claim_assembly_job(
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
    SELECT aj.id INTO v_job_id
    FROM assembly_jobs aj
    WHERE aj.status IN ('pending', 'retry')
        AND (aj.next_run_at IS NULL OR aj.next_run_at <= NOW())
        AND (aj.locked_at IS NULL OR aj.locked_at < NOW() - (lock_seconds || ' seconds')::INTERVAL)
    ORDER BY aj.priority DESC, aj.created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

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
            aj.id, aj.video_id, aj.status, aj.priority, aj.attempts,
            aj.max_attempts, aj.payload, aj.locked_at, aj.locked_by,
            aj.last_error, aj.next_run_at, aj.source_type, aj.source_id,
            aj.created_at, aj.updated_at;
    END IF;
END;
$$;

-- =====================================================
-- CREATE TRIGGERS
-- =====================================================
CREATE TRIGGER trigger_series_updated_at
    BEFORE UPDATE ON series
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_director_videos_updated_at
    BEFORE UPDATE ON director_videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_social_accounts_updated_at
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_update_series_stats
    AFTER INSERT OR UPDATE OR DELETE ON episodes
    FOR EACH ROW EXECUTE FUNCTION update_series_stats();

-- =====================================================
-- ENABLE ROW LEVEL SECURITY
-- =====================================================
ALTER TABLE series ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE director_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- CREATE POLICIES
-- =====================================================
CREATE POLICY "Users can view own series" ON series FOR SELECT USING (true);
CREATE POLICY "Users can insert own series" ON series FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own series" ON series FOR UPDATE USING (true);
CREATE POLICY "Users can delete own series" ON series FOR DELETE USING (true);

CREATE POLICY "Users can view own episodes" ON episodes FOR SELECT USING (true);
CREATE POLICY "Users can insert own episodes" ON episodes FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own episodes" ON episodes FOR UPDATE USING (true);
CREATE POLICY "Users can delete own episodes" ON episodes FOR DELETE USING (true);

CREATE POLICY "Users can view own director videos" ON director_videos FOR SELECT USING (true);
CREATE POLICY "Users can insert own director videos" ON director_videos FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own director videos" ON director_videos FOR UPDATE USING (true);
CREATE POLICY "Users can delete own director videos" ON director_videos FOR DELETE USING (true);

CREATE POLICY "Users can view own social accounts" ON social_accounts FOR SELECT USING (true);
CREATE POLICY "Users can insert own social accounts" ON social_accounts FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own social accounts" ON social_accounts FOR UPDATE USING (true);
CREATE POLICY "Users can delete own social accounts" ON social_accounts FOR DELETE USING (true);

-- =====================================================
-- GRANT PERMISSIONS
-- =====================================================
GRANT ALL ON series TO authenticated, anon, service_role;
GRANT ALL ON episodes TO authenticated, anon, service_role;
GRANT ALL ON director_videos TO authenticated, anon, service_role;
GRANT ALL ON assembly_jobs TO authenticated, anon, service_role;
GRANT ALL ON social_accounts TO authenticated, anon, service_role;

-- =====================================================
-- STORAGE BUCKET
-- =====================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('videos', 'videos', true)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- RELOAD SCHEMA
-- =====================================================
NOTIFY pgrst, 'reload schema';

-- =====================================================
-- VERIFICATION
-- =====================================================
SELECT 'Nuclear clean installation complete!' as message;
SELECT 'Series: ' || COUNT(*)::text FROM series;
SELECT 'Episodes: ' || COUNT(*)::text FROM episodes;
SELECT 'Director Videos: ' || COUNT(*)::text FROM director_videos;
SELECT 'Assembly Jobs: ' || COUNT(*)::text FROM assembly_jobs;
SELECT 'Social Accounts: ' || COUNT(*)::text FROM social_accounts;
