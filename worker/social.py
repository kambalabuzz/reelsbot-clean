# social.py
"""
Social media posting module.
Handles OAuth and posting to TikTok, Instagram, YouTube.
"""

import os
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum

import requests
from dotenv import load_dotenv

load_dotenv()


class Platform(str, Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"


@dataclass
class SocialAccount:
    """Connected social media account."""
    platform: Platform
    user_id: str
    username: str
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_active: bool = True


@dataclass
class PostResult:
    """Result of a post attempt."""
    success: bool
    platform: Platform
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None


# =============================================================================
# BASE POSTER
# =============================================================================

class SocialPoster(ABC):
    """Abstract base class for social media posters."""
    
    def __init__(self, account: SocialAccount):
        self.account = account
    
    @abstractmethod
    def post_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] = None,
    ) -> PostResult:
        """Post a video to the platform."""
        pass
    
    @abstractmethod
    def refresh_token(self) -> bool:
        """Refresh the OAuth token if needed."""
        pass
    
    @abstractmethod
    def verify_connection(self) -> bool:
        """Verify the account connection is still valid."""
        pass


# =============================================================================
# TIKTOK
# =============================================================================

class TikTokPoster(SocialPoster):
    """
    TikTok video poster using TikTok API.
    
    Requires:
    - TikTok for Developers app
    - OAuth 2.0 access token with video.upload scope
    """
    
    API_BASE = "https://open.tiktokapis.com/v2"
    
    def post_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] = None,
    ) -> PostResult:
        """Post video to TikTok."""
        try:
            # Step 1: Initialize upload
            init_url = f"{self.API_BASE}/post/publish/video/init/"
            headers = {
                "Authorization": f"Bearer {self.account.access_token}",
                "Content-Type": "application/json",
            }
            
            # Get file size
            video_size = Path(video_path).stat().st_size
            
            init_data = {
                "post_info": {
                    "title": title[:150],  # TikTok limit
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_stitch": False,
                    "disable_comment": False,
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_size,
                    "chunk_size": video_size,
                    "total_chunk_count": 1,
                }
            }
            
            init_resp = requests.post(init_url, headers=headers, json=init_data)
            
            if init_resp.status_code != 200:
                return PostResult(
                    success=False,
                    platform=Platform.TIKTOK,
                    error_message=f"Init failed: {init_resp.text}"
                )
            
            init_result = init_resp.json()
            upload_url = init_result["data"]["upload_url"]
            publish_id = init_result["data"]["publish_id"]
            
            # Step 2: Upload video
            with open(video_path, "rb") as f:
                video_data = f.read()
            
            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{video_size-1}/{video_size}",
            }
            
            upload_resp = requests.put(upload_url, headers=upload_headers, data=video_data)
            
            if upload_resp.status_code not in [200, 201]:
                return PostResult(
                    success=False,
                    platform=Platform.TIKTOK,
                    error_message=f"Upload failed: {upload_resp.text}"
                )
            
            return PostResult(
                success=True,
                platform=Platform.TIKTOK,
                post_id=publish_id,
                post_url=f"https://www.tiktok.com/@{self.account.username}",
            )
            
        except Exception as e:
            return PostResult(
                success=False,
                platform=Platform.TIKTOK,
                error_message=str(e)
            )
    
    def refresh_token(self) -> bool:
        """Refresh TikTok OAuth token."""
        if not self.account.refresh_token:
            return False
        
        try:
            url = "https://open.tiktokapis.com/v2/oauth/token/"
            data = {
                "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
                "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
                "grant_type": "refresh_token",
                "refresh_token": self.account.refresh_token,
            }
            
            resp = requests.post(url, data=data)
            if resp.status_code == 200:
                tokens = resp.json()
                self.account.access_token = tokens["access_token"]
                self.account.refresh_token = tokens.get("refresh_token", self.account.refresh_token)
                return True
        except:
            pass
        
        return False
    
    def verify_connection(self) -> bool:
        """Verify TikTok connection."""
        try:
            url = f"{self.API_BASE}/user/info/"
            headers = {"Authorization": f"Bearer {self.account.access_token}"}
            resp = requests.get(url, headers=headers)
            return resp.status_code == 200
        except:
            return False


# =============================================================================
# YOUTUBE
# =============================================================================

class YouTubePoster(SocialPoster):
    """
    YouTube Shorts poster using YouTube Data API.
    
    Requires:
    - Google Cloud project with YouTube Data API enabled
    - OAuth 2.0 access token with youtube.upload scope
    """
    
    API_BASE = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
    
    def post_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] = None,
    ) -> PostResult:
        """Post video to YouTube as a Short."""
        try:
            tags = tags or []
            
            # Add #Shorts tag for YouTube Shorts
            if "Shorts" not in tags:
                tags.append("Shorts")
            
            # Video metadata
            metadata = {
                "snippet": {
                    "title": title[:100],
                    "description": description + "\n\n#Shorts",
                    "tags": tags[:500],  # YouTube tag limit
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.account.access_token}",
                "Content-Type": "application/json",
            }
            
            # Step 1: Start resumable upload
            init_url = f"{self.UPLOAD_URL}?uploadType=resumable&part=snippet,status"
            init_resp = requests.post(init_url, headers=headers, json=metadata)
            
            if init_resp.status_code != 200:
                return PostResult(
                    success=False,
                    platform=Platform.YOUTUBE,
                    error_message=f"Init failed: {init_resp.text}"
                )
            
            upload_url = init_resp.headers.get("Location")
            
            # Step 2: Upload video
            with open(video_path, "rb") as f:
                video_data = f.read()
            
            upload_headers = {
                "Authorization": f"Bearer {self.account.access_token}",
                "Content-Type": "video/mp4",
            }
            
            upload_resp = requests.put(upload_url, headers=upload_headers, data=video_data)
            
            if upload_resp.status_code not in [200, 201]:
                return PostResult(
                    success=False,
                    platform=Platform.YOUTUBE,
                    error_message=f"Upload failed: {upload_resp.text}"
                )
            
            result = upload_resp.json()
            video_id = result["id"]
            
            return PostResult(
                success=True,
                platform=Platform.YOUTUBE,
                post_id=video_id,
                post_url=f"https://youtube.com/shorts/{video_id}",
            )
            
        except Exception as e:
            return PostResult(
                success=False,
                platform=Platform.YOUTUBE,
                error_message=str(e)
            )
    
    def refresh_token(self) -> bool:
        """Refresh Google OAuth token."""
        if not self.account.refresh_token:
            return False
        
        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "grant_type": "refresh_token",
                "refresh_token": self.account.refresh_token,
            }
            
            resp = requests.post(url, data=data)
            if resp.status_code == 200:
                tokens = resp.json()
                self.account.access_token = tokens["access_token"]
                return True
        except:
            pass
        
        return False
    
    def verify_connection(self) -> bool:
        """Verify YouTube connection."""
        try:
            url = f"{self.API_BASE}/channels?part=id&mine=true"
            headers = {"Authorization": f"Bearer {self.account.access_token}"}
            resp = requests.get(url, headers=headers)
            return resp.status_code == 200
        except:
            return False


# =============================================================================
# INSTAGRAM
# =============================================================================

class InstagramPoster(SocialPoster):
    """
    Instagram Reels poster using Facebook Graph API.
    
    Requires:
    - Facebook Developer app with Instagram API
    - Instagram Business/Creator account connected to Facebook Page
    - OAuth token with instagram_content_publish scope
    """
    
    API_BASE = "https://graph.facebook.com/v18.0"
    
    def post_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] = None,
    ) -> PostResult:
        """Post video to Instagram as a Reel."""
        try:
            # Instagram requires video to be hosted at a URL
            # In production, you'd upload to a CDN first
            # For now, we'll return a placeholder
            
            # Step 1: Create media container
            container_url = f"{self.API_BASE}/{self.account.user_id}/media"
            
            # Combine title and description with hashtags
            caption = f"{title}\n\n{description}"
            if tags:
                caption += "\n\n" + " ".join(f"#{tag}" for tag in tags[:30])
            
            container_data = {
                "media_type": "REELS",
                "video_url": "VIDEO_URL_HERE",  # Need CDN URL
                "caption": caption[:2200],
                "access_token": self.account.access_token,
            }
            
            # This is a simplified version - real implementation needs:
            # 1. Upload video to a CDN
            # 2. Create container with video URL
            # 3. Wait for processing
            # 4. Publish the container
            
            return PostResult(
                success=False,
                platform=Platform.INSTAGRAM,
                error_message="Instagram posting requires video CDN hosting. Not yet implemented."
            )
            
        except Exception as e:
            return PostResult(
                success=False,
                platform=Platform.INSTAGRAM,
                error_message=str(e)
            )
    
    def refresh_token(self) -> bool:
        """Refresh Instagram/Facebook token."""
        # Long-lived tokens last 60 days, need to refresh before expiry
        try:
            url = f"{self.API_BASE}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": os.getenv("FACEBOOK_APP_ID"),
                "client_secret": os.getenv("FACEBOOK_APP_SECRET"),
                "fb_exchange_token": self.account.access_token,
            }
            
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                tokens = resp.json()
                self.account.access_token = tokens["access_token"]
                return True
        except:
            pass
        
        return False
    
    def verify_connection(self) -> bool:
        """Verify Instagram connection."""
        try:
            url = f"{self.API_BASE}/{self.account.user_id}"
            params = {"access_token": self.account.access_token}
            resp = requests.get(url, params=params)
            return resp.status_code == 200
        except:
            return False


# =============================================================================
# FACTORY
# =============================================================================

def get_poster(account: SocialAccount) -> SocialPoster:
    """Get the appropriate poster for a platform."""
    posters = {
        Platform.TIKTOK: TikTokPoster,
        Platform.YOUTUBE: YouTubePoster,
        Platform.INSTAGRAM: InstagramPoster,
    }
    
    poster_class = posters.get(account.platform)
    if not poster_class:
        raise ValueError(f"Unknown platform: {account.platform}")
    
    return poster_class(account)


def post_to_all(
    video_path: str,
    title: str,
    description: str,
    accounts: list[SocialAccount],
    tags: list[str] = None,
) -> list[PostResult]:
    """Post video to all connected accounts."""
    results = []
    
    for account in accounts:
        if not account.is_active:
            continue
        
        poster = get_poster(account)
        
        # Refresh token if needed
        if account.token_expires_at and datetime.utcnow() > account.token_expires_at:
            poster.refresh_token()
        
        result = poster.post_video(video_path, title, description, tags)
        results.append(result)
        
        print(f"[social] {account.platform.value}: {'✓' if result.success else '✗'} {result.error_message or result.post_url or ''}")
    
    return results


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    print("Social posting module loaded.")
    print("\nSupported platforms:")
    for p in Platform:
        print(f"  - {p.value}")
    
    print("\nRequired environment variables:")
    print("  TikTok:    TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET")
    print("  YouTube:   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET")
    print("  Instagram: FACEBOOK_APP_ID, FACEBOOK_APP_SECRET")
