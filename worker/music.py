# music.py
"""
Background music library management.
Supports preset tracks and custom user uploads.
"""

import os
import random
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from config import MusicMood


@dataclass
class MusicTrack:
    """Represents a music track."""
    id: str
    name: str
    mood: MusicMood
    description: str
    file_path: str
    duration_seconds: float = 0
    is_custom: bool = False
    user_id: Optional[str] = None


# =============================================================================
# PRESET MUSIC LIBRARY
# =============================================================================

# These are placeholder entries - you'll add actual royalty-free tracks
PRESET_TRACKS = [
    MusicTrack(
        id="happy_rhythm",
        name="Happy Rhythm",
        mood=MusicMood.HAPPY,
        description="Upbeat and energetic, perfect for positive content",
        file_path="assets/music/presets/happy_rhythm.mp3",
    ),
    MusicTrack(
        id="quiet_storm",
        name="Quiet Before Storm",
        mood=MusicMood.SUSPENSE,
        description="Building tension and anticipation for dramatic reveals",
        file_path="assets/music/presets/quiet_storm.mp3",
    ),
    MusicTrack(
        id="peaceful_vibes",
        name="Peaceful Vibes",
        mood=MusicMood.CALM,
        description="Calm and soothing background for relaxed storytelling",
        file_path="assets/music/presets/peaceful_vibes.mp3",
    ),
    MusicTrack(
        id="brilliant_symphony",
        name="Brilliant Symphony",
        mood=MusicMood.EPIC,
        description="Orchestral and majestic for epic storytelling",
        file_path="assets/music/presets/brilliant_symphony.mp3",
    ),
    MusicTrack(
        id="breathing_shadows",
        name="Breathing Shadows",
        mood=MusicMood.MYSTERIOUS,
        description="Mysterious and eerie ambiance for suspenseful videos",
        file_path="assets/music/presets/breathing_shadows.mp3",
    ),
    MusicTrack(
        id="dark_descent",
        name="Dark Descent",
        mood=MusicMood.DARK,
        description="Dark and ominous for horror and true crime",
        file_path="assets/music/presets/dark_descent.mp3",
    ),
    MusicTrack(
        id="heart_racing",
        name="Heart Racing",
        mood=MusicMood.ENERGETIC,
        description="High energy for action-packed content",
        file_path="assets/music/presets/heart_racing.mp3",
    ),
    MusicTrack(
        id="emotional_journey",
        name="Emotional Journey",
        mood=MusicMood.SAD,
        description="Melancholic and emotional for touching stories",
        file_path="assets/music/presets/emotional_journey.mp3",
    ),
    MusicTrack(
        id="rise_up",
        name="Rise Up",
        mood=MusicMood.UPLIFTING,
        description="Inspiring and uplifting for motivational content",
        file_path="assets/music/presets/rise_up.mp3",
    ),
    MusicTrack(
        id="final_hour",
        name="Final Hour",
        mood=MusicMood.DRAMATIC,
        description="Intense and dramatic for climactic moments",
        file_path="assets/music/presets/final_hour.mp3",
    ),
]


# Cache directory for custom uploads
CUSTOM_MUSIC_DIR = Path("assets/music/custom")


class MusicLibrary:
    """Manages the music library."""
    
    def __init__(self):
        self._preset_tracks = {t.id: t for t in PRESET_TRACKS}
        CUSTOM_MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_preset_tracks(self) -> List[MusicTrack]:
        """Get all preset tracks."""
        return PRESET_TRACKS
    
    def get_tracks_by_mood(self, mood: MusicMood) -> List[MusicTrack]:
        """Get all tracks matching a mood."""
        return [t for t in PRESET_TRACKS if t.mood == mood]
    
    def get_track_by_id(self, track_id: str) -> Optional[MusicTrack]:
        """Get a specific track by ID."""
        return self._preset_tracks.get(track_id)
    
    def get_random_track(self, mood: Optional[MusicMood] = None) -> Optional[MusicTrack]:
        """Get a random track, optionally filtered by mood."""
        if mood:
            tracks = self.get_tracks_by_mood(mood)
        else:
            tracks = PRESET_TRACKS
        
        if not tracks:
            return None
        return random.choice(tracks)
    
    def save_custom_track(
        self, 
        file_bytes: bytes, 
        filename: str, 
        user_id: str,
        mood: MusicMood = MusicMood.DARK,
    ) -> MusicTrack:
        """
        Save a custom uploaded music track.
        
        Returns:
            MusicTrack object for the saved file
        """
        # Generate unique ID from content hash
        content_hash = hashlib.md5(file_bytes).hexdigest()[:12]
        track_id = f"custom_{user_id}_{content_hash}"
        
        # Ensure valid extension
        ext = Path(filename).suffix.lower()
        if ext not in [".mp3", ".wav", ".m4a", ".ogg"]:
            ext = ".mp3"
        
        # Save file
        file_path = CUSTOM_MUSIC_DIR / f"{track_id}{ext}"
        file_path.write_bytes(file_bytes)
        
        track = MusicTrack(
            id=track_id,
            name=Path(filename).stem,
            mood=mood,
            description="Custom uploaded track",
            file_path=str(file_path),
            is_custom=True,
            user_id=user_id,
        )
        
        print(f"[music] Saved custom track: {file_path}")
        return track
    
    def get_user_custom_tracks(self, user_id: str) -> List[MusicTrack]:
        """Get all custom tracks for a user."""
        tracks = []
        prefix = f"custom_{user_id}_"
        
        for f in CUSTOM_MUSIC_DIR.glob("*"):
            if f.stem.startswith(prefix):
                tracks.append(MusicTrack(
                    id=f.stem,
                    name=f.stem.replace(prefix, ""),
                    mood=MusicMood.DARK,  # Default, could store in metadata
                    description="Custom uploaded track",
                    file_path=str(f),
                    is_custom=True,
                    user_id=user_id,
                ))
        
        return tracks
    
    def delete_custom_track(self, track_id: str, user_id: str) -> bool:
        """Delete a custom track (must belong to user)."""
        if not track_id.startswith(f"custom_{user_id}_"):
            return False
        
        for f in CUSTOM_MUSIC_DIR.glob(f"{track_id}.*"):
            f.unlink()
            print(f"[music] Deleted custom track: {f}")
            return True
        
        return False


def get_music_for_series(
    mood: Optional[MusicMood] = None,
    track_id: Optional[str] = None,
    custom_path: Optional[str] = None,
    fallback_dir: str = "assets/music",
) -> Optional[str]:
    """
    Get the music file path for video assembly.
    
    Priority:
    1. Custom path if provided
    2. Specific track ID
    3. Random track matching mood
    4. Random from fallback directory
    
    Returns:
        Path to music file, or None
    """
    # Custom path takes priority
    if custom_path and Path(custom_path).exists():
        return custom_path
    
    library = MusicLibrary()
    
    # Try specific track
    if track_id:
        track = library.get_track_by_id(track_id)
        if track and Path(track.file_path).exists():
            return track.file_path
    
    # Try mood-based
    if mood:
        track = library.get_random_track(mood)
        if track and Path(track.file_path).exists():
            return track.file_path
    
    # Fallback to directory
    fallback = Path(fallback_dir)
    if fallback.is_dir():
        files = list(fallback.glob("*.mp3")) + list(fallback.glob("*.wav"))
        if files:
            return str(random.choice(files))
    
    return None


# =============================================================================
# CLI for testing
# =============================================================================
if __name__ == "__main__":
    library = MusicLibrary()
    
    print("\n=== PRESET MUSIC LIBRARY ===\n")
    for track in library.get_preset_tracks():
        print(f"  [{track.mood.value:12}] {track.name}")
        print(f"                {track.description}")
        print()
    
    print("\n=== TRACKS BY MOOD ===\n")
    for mood in MusicMood:
        tracks = library.get_tracks_by_mood(mood)
        print(f"  {mood.value}: {len(tracks)} tracks")
