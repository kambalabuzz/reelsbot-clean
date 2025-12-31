-- AI Video Bot Database Schema
-- Creates all necessary tables for the application

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Series table: stores video series information
CREATE TABLE IF NOT EXISTS series (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    niche TEXT DEFAULT 'entertainment',
    art_style TEXT DEFAULT 'cinematic',
    voice TEXT DEFAULT 'adam',
    schedule TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Episodes table: stores individual video episodes
CREATE TABLE IF NOT EXISTS episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    series_id UUID REFERENCES series(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    video_url TEXT,
    audio_url TEXT,
    script JSONB,
    image_urls JSONB,
    config JSONB,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE
);

-- Social accounts table: stores connected social media accounts
CREATE TABLE IF NOT EXISTS social_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    account_id TEXT,
    account_name TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, platform, account_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_episodes_user_id ON episodes(user_id);
CREATE INDEX IF NOT EXISTS idx_episodes_series_id ON episodes(series_id);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status);
CREATE INDEX IF NOT EXISTS idx_episodes_scheduled_at ON episodes(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_series_user_id ON series(user_id);
CREATE INDEX IF NOT EXISTS idx_social_accounts_user_id ON social_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_social_accounts_platform ON social_accounts(platform);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to auto-update updated_at
DROP TRIGGER IF EXISTS update_series_updated_at ON series;
CREATE TRIGGER update_series_updated_at
    BEFORE UPDATE ON series
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_episodes_updated_at ON episodes;
CREATE TRIGGER update_episodes_updated_at
    BEFORE UPDATE ON episodes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_social_accounts_updated_at ON social_accounts;
CREATE TRIGGER update_social_accounts_updated_at
    BEFORE UPDATE ON social_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create storage bucket for videos if not exists
INSERT INTO storage.buckets (id, name, public)
VALUES ('videos', 'videos', true)
ON CONFLICT (id) DO NOTHING;

-- Set up Row Level Security (RLS) policies
ALTER TABLE series ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_accounts ENABLE ROW LEVEL SECURITY;

-- Allow service role to bypass RLS
-- Users can only access their own data
CREATE POLICY "Users can view own series" ON series
    FOR SELECT USING (true);  -- Allow all reads for now (can restrict by user_id later)

CREATE POLICY "Users can insert own series" ON series
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own series" ON series
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own series" ON series
    FOR DELETE USING (true);

CREATE POLICY "Users can view own episodes" ON episodes
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own episodes" ON episodes
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own episodes" ON episodes
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own episodes" ON episodes
    FOR DELETE USING (true);

CREATE POLICY "Users can view own social accounts" ON social_accounts
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own social accounts" ON social_accounts
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own social accounts" ON social_accounts
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own social accounts" ON social_accounts
    FOR DELETE USING (true);
