# music_library.py
"""
Background music library with preset tracks and custom upload support.
Similar to FacelessReels' music selection system.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from pathlib import Path
import os
import shutil
import hashlib


class MusicMood(str, Enum):
    """Music mood categories"""
    HAPPY = "happy"
    DARK = "dark"
    SUSPENSE = "suspense"
    EPIC = "epic"
    CALM = "calm"
    ENERGETIC = "energetic"
    SAD = "sad"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"
    DRAMATIC = "dramatic"
    ROMANTIC = "romantic"
    PEACEFUL = "peaceful"


@dataclass
class MusicTrack:
    """Represents a music track in the library"""
    id: str
    name: str
    description: str
    mood: MusicMood
    file_path: Optional[str] = None  # Local path
    url: Optional[str] = None  # Remote URL
    duration_seconds: Optional[float] = None
    artist: Optional[str] = None
    is_custom: bool = False  # User uploaded
    preview_url: Optional[str] = None  # For UI preview


# =============================================================================
# PRESET MUSIC LIBRARY
# =============================================================================

PRESET_TRACKS = [
    # Happy/Upbeat
    MusicTrack(
        id="happy_rhythm",
        name="Happy Rhythm",
        description="Upbeat and energetic, perfect for positive content",
        mood=MusicMood.HAPPY,
    ),
    MusicTrack(
        id="summer_vibes",
        name="Summer Vibes",
        description="Cheerful and carefree, great for lifestyle content",
        mood=MusicMood.HAPPY,
    ),
    
    # Suspense/Dark
    MusicTrack(
        id="quiet_before_storm",
        name="Quiet Before Storm",
        description="Building tension and anticipation for dramatic reveals",
        mood=MusicMood.SUSPENSE,
    ),
    MusicTrack(
        id="breathing_shadows",
        name="Breathing Shadows",
        description="Mysterious and eerie ambiance for suspenseful videos",
        mood=MusicMood.MYSTERIOUS,
    ),
    MusicTrack(
        id="dark_descent",
        name="Dark Descent",
        description="Deep, ominous tones for horror and true crime",
        mood=MusicMood.DARK,
    ),
    MusicTrack(
        id="nightmare_fuel",
        name="Nightmare Fuel",
        description="Unsettling atmosphere for creepy content",
        mood=MusicMood.DARK,
    ),
    
    # Calm/Peaceful
    MusicTrack(
        id="peaceful_vibes",
        name="Peaceful Vibes",
        description="Calm and soothing background for relaxed storytelling",
        mood=MusicMood.PEACEFUL,
    ),
    MusicTrack(
        id="gentle_morning",
        name="Gentle Morning",
        description="Soft and warm, ideal for wholesome content",
        mood=MusicMood.CALM,
    ),
    MusicTrack(
        id="meditation_flow",
        name="Meditation Flow",
        description="Tranquil ambient sounds for mindfulness content",
        mood=MusicMood.CALM,
    ),
    
    # Epic/Dramatic
    MusicTrack(
        id="brilliant_symphony",
        name="Brilliant Symphony",
        description="Orchestral and majestic for epic storytelling",
        mood=MusicMood.EPIC,
    ),
    MusicTrack(
        id="rising_hero",
        name="Rising Hero",
        description="Triumphant and inspiring, great for success stories",
        mood=MusicMood.EPIC,
    ),
    MusicTrack(
        id="dramatic_tension",
        name="Dramatic Tension",
        description="Building intensity for climactic moments",
        mood=MusicMood.DRAMATIC,
    ),
    
    # Energetic
    MusicTrack(
        id="power_surge",
        name="Power Surge",
        description="High energy beats for action-packed content",
        mood=MusicMood.ENERGETIC,
    ),
    MusicTrack(
        id="unstoppable",
        name="Unstoppable",
        description="Driving rhythm for motivational videos",
        mood=MusicMood.ENERGETIC,
    ),
    
    # Mysterious
    MusicTrack(
        id="hidden_secrets",
        name="Hidden Secrets",
        description="Intriguing and curious, perfect for mysteries",
        mood=MusicMood.MYSTERIOUS,
    ),
    MusicTrack(
        id="ancient_whispers",
        name="Ancient Whispers",
        description="Ethereal tones for paranormal and conspiracy content",
        mood=MusicMood.MYSTERIOUS,
    ),
    
    # Sad/Emotional
    MusicTrack(
        id="tears_in_rain",
        name="Tears in Rain",
        description="Melancholic and emotional for touching stories",
        mood=MusicMood.SAD,
    ),
    MusicTrack(
        id="bittersweet_memories",
        name="Bittersweet Memories",
        description="Nostalgic and wistful for reflective content",
        mood=MusicMood.SAD,
    ),
    
    # Uplifting
    MusicTrack(
        id="new_beginnings",
        name="New Beginnings",
        description="Hopeful and optimistic for inspirational content",
        mood=MusicMood.UPLIFTING,
    ),
    MusicTrack(
        id="chase_your_dreams",
        name="Chase Your Dreams",
        description="Motivating and encouraging for success stories",
        mood=MusicMood.UPLIFTING,
    ),
]


# =============================================================================
# MUSIC LIBRARY CLASS
# =============================================================================

class MusicLibrary:
    """Manages preset and custom music tracks"""
    
    def __init__(self, music_dir: str = "assets/music"):
        self.music_dir = Path(music_dir)
        self.custom_dir = self.music_dir / "custom"
        self.preset_dir = self.music_dir / "presets"
        
        # Create directories
        self.music_dir.mkdir(parents=True, exist_ok=True)
        self.custom_dir.mkdir(exist_ok=True)
        self.preset_dir.mkdir(exist_ok=True)
        
        # Index preset tracks
        self._presets = {t.id: t for t in PRESET_TRACKS}
        self._scan_local_files()
    
    def _scan_local_files(self):
        """Scan directories for actual music files and link to tracks"""
        # Scan presets
        for track in PRESET_TRACKS:
            for ext in [".mp3", ".wav", ".m4a"]:
                path = self.preset_dir / f"{track.id}{ext}"
                if path.exists():
                    track.file_path = str(path)
                    break
        
        # Scan custom uploads
        self._custom_tracks = []
        for f in self.custom_dir.glob("*"):
            if f.suffix.lower() in [".mp3", ".wav", ".m4a"]:
                track = MusicTrack(
                    id=f"custom_{f.stem}",
                    name=f.stem.replace("_", " ").title(),
                    description="Custom uploaded track",
                    mood=MusicMood.CALM,  # Default mood
                    file_path=str(f),
                    is_custom=True,
                )
                self._custom_tracks.append(track)
    
    def get_track(self, track_id: str) -> Optional[MusicTrack]:
        """Get a track by ID"""
        if track_id in self._presets:
            return self._presets[track_id]
        
        for track in self._custom_tracks:
            if track.id == track_id:
                return track
        
        return None
    
    def get_tracks_by_mood(self, mood: MusicMood) -> List[MusicTrack]:
        """Get all tracks matching a mood"""
        tracks = [t for t in PRESET_TRACKS if t.mood == mood]
        tracks += [t for t in self._custom_tracks if t.mood == mood]
        return tracks
    
    def get_all_presets(self) -> List[MusicTrack]:
        """Get all preset tracks"""
        return PRESET_TRACKS.copy()
    
    def get_custom_tracks(self) -> List[MusicTrack]:
        """Get all custom uploaded tracks"""
        return self._custom_tracks.copy()
    
    def get_random_track(self, mood: Optional[MusicMood] = None) -> Optional[MusicTrack]:
        """Get a random track, optionally filtered by mood"""
        import random
        
        if mood:
            tracks = self.get_tracks_by_mood(mood)
        else:
            tracks = [t for t in PRESET_TRACKS if t.file_path]
            tracks += [t for t in self._custom_tracks if t.file_path]
        
        # Only return tracks that have actual files
        tracks_with_files = [t for t in tracks if t.file_path and Path(t.file_path).exists()]
        
        if not tracks_with_files:
            # Fallback: any file in music dir
            all_files = list(self.music_dir.glob("**/*.mp3"))
            all_files += list(self.music_dir.glob("**/*.wav"))
            all_files += list(self.music_dir.glob("**/*.m4a"))
            
            if all_files:
                chosen = random.choice(all_files)
                return MusicTrack(
                    id=f"random_{chosen.stem}",
                    name=chosen.stem,
                    description="",
                    mood=MusicMood.CALM,
                    file_path=str(chosen),
                )
            return None
        
        return random.choice(tracks_with_files)
    
    def upload_custom(self, file_path: str, name: Optional[str] = None) -> MusicTrack:
        """
        Upload a custom music file.
        
        Args:
            file_path: Path to the music file
            name: Display name (defaults to filename)
        
        Returns:
            MusicTrack object for the uploaded file
        """
        src = Path(file_path)
        if not src.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate unique ID
        with open(src, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        
        # Copy to custom directory
        dest_name = f"{src.stem}_{file_hash}{src.suffix}"
        dest = self.custom_dir / dest_name
        shutil.copy2(src, dest)
        
        # Create track
        display_name = name or src.stem.replace("_", " ").title()
        track = MusicTrack(
            id=f"custom_{file_hash}",
            name=display_name,
            description="Custom uploaded track",
            mood=MusicMood.CALM,
            file_path=str(dest),
            is_custom=True,
        )
        
        self._custom_tracks.append(track)
        return track
    
    def delete_custom(self, track_id: str) -> bool:
        """Delete a custom track"""
        for i, track in enumerate(self._custom_tracks):
            if track.id == track_id:
                if track.file_path and Path(track.file_path).exists():
                    Path(track.file_path).unlink()
                self._custom_tracks.pop(i)
                return True
        return False
    
    def list_moods(self) -> List[dict]:
        """Get list of moods with track counts"""
        mood_counts = {}
        for mood in MusicMood:
            count = len(self.get_tracks_by_mood(mood))
            if count > 0:
                mood_counts[mood] = {
                    "id": mood.value,
                    "name": mood.value.replace("_", " ").title(),
                    "count": count,
                }
        return list(mood_counts.values())


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_music_for_niche(niche: str) -> MusicMood:
    """Suggest a music mood based on content niche"""
    niche_moods = {
        "true_crime": MusicMood.SUSPENSE,
        "horror": MusicMood.DARK,
        "mystery": MusicMood.MYSTERIOUS,
        "history": MusicMood.EPIC,
        "conspiracy": MusicMood.MYSTERIOUS,
        "paranormal": MusicMood.DARK,
        "sci_fi": MusicMood.EPIC,
        "motivation": MusicMood.UPLIFTING,
        "finance": MusicMood.ENERGETIC,
        "tech": MusicMood.ENERGETIC,
    }
    return niche_moods.get(niche, MusicMood.CALM)


# Global instance
_library = None

def get_library() -> MusicLibrary:
    """Get the global music library instance"""
    global _library
    if _library is None:
        _library = MusicLibrary()
    return _library


if __name__ == "__main__":
    # Test the library
    lib = get_library()
    
    print("=== PRESET TRACKS ===")
    for track in lib.get_all_presets():
        status = "✓" if track.file_path else "✗"
        print(f"  [{status}] {track.name} ({track.mood.value})")
    
    print("\n=== MOODS ===")
    for mood in lib.list_moods():
        print(f"  {mood['name']}: {mood['count']} tracks")
    
    print("\n=== RANDOM TRACK ===")
    track = lib.get_random_track()
    if track:
        print(f"  {track.name}: {track.file_path}")
    else:
        print("  No tracks available - add music files to assets/music/")
