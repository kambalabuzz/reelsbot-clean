# models.py
"""
SQLAlchemy database models for ReelsBot SaaS.
These define the structure for users, series, episodes, etc.
"""

from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, Enum, JSON, Float
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# =============================================================================
# ENUMS (matching config.py)
# =============================================================================

class TierEnum(str, PyEnum):
    FREE = "free"
    HOBBY = "hobby"
    DAILY = "daily"
    PRO = "pro"


class EpisodeStatus(str, PyEnum):
    PENDING = "pending"
    GENERATING = "generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    POSTED = "posted"


class PostStatus(str, PyEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# USER
# =============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # Auth (from Clerk or similar)
    clerk_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    
    # Subscription
    tier = Column(Enum(TierEnum), default=TierEnum.FREE)
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    
    # Usage tracking
    episodes_this_month = Column(Integer, default=0)
    usage_reset_date = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    series = relationship("Series", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user")


# =============================================================================
# SERIES
# =============================================================================

class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Basic info
    name = Column(String(255))
    description = Column(Text, nullable=True)
    
    # Content settings (stored as JSON for flexibility)
    niche = Column(String(50), default="true_crime")
    beats_per_episode = Column(Integer, default=12)
    
    # Style settings
    art_style = Column(String(50), default="comic_dark")
    custom_art_prompt = Column(Text, nullable=True)
    voice = Column(String(50), default="alloy")
    caption_style = Column(String(50), default="red_highlight")
    motion_effect = Column(String(50), default="ken_burns")
    
    # Music
    music_track_id = Column(Integer, ForeignKey("music_tracks.id"), nullable=True)
    
    # Posting schedule
    post_frequency = Column(String(50), default="manual")
    post_time = Column(String(10), default="18:00")  # HH:MM format
    
    # Platform flags
    post_to_tiktok = Column(Boolean, default=False)
    post_to_youtube = Column(Boolean, default=False)
    post_to_instagram = Column(Boolean, default=False)
    
    # Watermark
    add_watermark = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="series")
    episodes = relationship("Episode", back_populates="series")
    music_track = relationship("MusicTrack")


# =============================================================================
# EPISODE
# =============================================================================

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("series.id"), index=True)
    
    # Content
    topic = Column(String(500))
    script_text = Column(Text, nullable=True)
    beats_json = Column(JSON, nullable=True)  # Store generated beats
    
    # Style overrides (nullable = use series default)
    caption_style_override = Column(String(50), nullable=True)
    voice_override = Column(String(50), nullable=True)
    art_style_override = Column(String(50), nullable=True)
    
    # Generated assets (cloud storage URLs)
    audio_url = Column(String(500), nullable=True)
    images_json = Column(JSON, nullable=True)  # List of image URLs
    raw_video_url = Column(String(500), nullable=True)
    final_video_url = Column(String(500), nullable=True)
    alignment_json = Column(JSON, nullable=True)
    
    # Metadata
    duration_seconds = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=True)
    
    # Status
    status = Column(Enum(EpisodeStatus), default=EpisodeStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    series = relationship("Series", back_populates="episodes")
    posts = relationship("Post", back_populates="episode")


# =============================================================================
# SOCIAL ACCOUNTS
# =============================================================================

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Platform
    platform = Column(String(50))  # "tiktok", "youtube", "instagram"
    
    # OAuth tokens (encrypted in production!)
    access_token = Column(Text)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Account info
    platform_user_id = Column(String(255))
    platform_username = Column(String(255))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="social_accounts")


# =============================================================================
# POSTS (tracking what's been posted where)
# =============================================================================

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), index=True)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), index=True)
    
    # Platform-specific
    platform = Column(String(50))
    platform_post_id = Column(String(255), nullable=True)
    platform_url = Column(String(500), nullable=True)
    
    # Status
    status = Column(Enum(PostStatus), default=PostStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    scheduled_for = Column(DateTime, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    episode = relationship("Episode", back_populates="posts")
    social_account = relationship("SocialAccount")


# =============================================================================
# MUSIC TRACKS
# =============================================================================

class MusicTrack(Base):
    __tablename__ = "music_tracks"

    id = Column(Integer, primary_key=True, index=True)
    
    # Info
    name = Column(String(255))
    artist = Column(String(255), nullable=True)
    
    # Storage
    file_url = Column(String(500))
    duration_seconds = Column(Float)
    
    # Categorization
    mood = Column(String(50))  # "dark", "upbeat", "dramatic", etc.
    genre = Column(String(50))
    
    # Licensing
    is_royalty_free = Column(Boolean, default=True)
    license_info = Column(Text, nullable=True)
    
    # Availability
    is_active = Column(Boolean, default=True)
    available_tiers = Column(JSON, default=["free", "hobby", "daily", "pro"])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# ART STYLES (custom user styles)
# =============================================================================

class CustomArtStyle(Base):
    __tablename__ = "custom_art_styles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    name = Column(String(255))
    prompt = Column(Text)
    
    # Reference image (optional)
    reference_image_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# =============================================================================
# RENDER JOBS (for queue management)
# =============================================================================

class RenderJob(Base):
    __tablename__ = "render_jobs"

    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"), index=True)
    
    # Job tracking
    celery_task_id = Column(String(255), nullable=True)
    priority = Column(Integer, default=5)  # 1-10, higher = more priority
    
    # Status
    status = Column(String(50), default="pending")
    progress_percent = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
