# captions.py
"""
TikTok/Reels-style karaoke captions with multiple style presets.

Styles:
- red_highlight: Red glowing text on current word, white for others
- karaoke: Purple box highlight on current word (classic TikTok)
- beast: Bold italic white with black stroke (MrBeast style)
- majestic: Clean white with subtle shadow
- bold_stroke: Heavy black outline, filled white
- sleek: Subtle gray gradient, current word pops
- elegant: Thin serif-style, understated
- neon: Glowing cyberpunk style
- fire: Orange/red gradient highlight
- hormozi: Alex Hormozi style big yellow pops
"""

from pathlib import Path
import subprocess
import json
from typing import Literal

# =============================================================================
# STYLE DEFINITIONS
# =============================================================================

STYLES = {
    # -------------------------------------------------------------------------
    # RED HIGHLIGHT - Red glow on active word, white others
    # -------------------------------------------------------------------------
    "red_highlight": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,85,&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,-1,0,0,0,100,100,2,0,1,6,4,5,40,40,800,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H004040FF&",  # Bright red (BGR)
        "normal_color": "\\c&H00FFFFFF&",      # White
        "highlight_extra": "\\blur2",           # Glow effect
    },

    # -------------------------------------------------------------------------
    # KARAOKE - Purple/blue box behind current word (TikTok classic)
    # -------------------------------------------------------------------------
    "karaoke": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,85,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,5,0,5,40,40,800,0
Style: BoxHighlight,Montserrat Black,85,&H00FFFFFF,&H000000FF,&H00FF5500,&H00FF5500,-1,0,0,0,100,100,2,0,3,12,0,5,40,40,800,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "",
        "normal_color": "",
        "highlight_extra": "",
        "use_box_style": True,  # Special flag for box-based highlighting
    },

    # -------------------------------------------------------------------------
    # BEAST - MrBeast style: chunky, bold, white with heavy black stroke
    # -------------------------------------------------------------------------
    "beast": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Impact,90,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,-1,0,0,105,100,1,0,1,6,3,5,40,40,380,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H0000FFFF&",   # Yellow
        "normal_color": "\\c&H00FFFFFF&",      # White
        "highlight_extra": "\\fscx115\\fscy115",  # Scale up active word
    },

    # -------------------------------------------------------------------------
    # MAJESTIC - Clean, elegant white with soft shadow
    # -------------------------------------------------------------------------
    "majestic": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Georgia,72,&H00FFFFFF,&H000000FF,&H00222222,&H88000000,-1,0,0,0,100,100,3,0,1,3,4,5,40,40,400,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H00AAFFFF&",   # Light gold
        "normal_color": "\\c&H00FFFFFF&",      # White
        "highlight_extra": "",
    },

    # -------------------------------------------------------------------------
    # BOLD STROKE - Heavy outline, very readable
    # -------------------------------------------------------------------------
    "bold_stroke": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,82,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,8,0,5,40,40,400,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H0000D4FF&\\bord10",  # Orange with thicker border
        "normal_color": "\\c&H00FFFFFF&",
        "highlight_extra": "",
    },

    # -------------------------------------------------------------------------
    # SLEEK - Modern, minimal, gray context words
    # -------------------------------------------------------------------------
    "sleek": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Helvetica Neue,68,&H00CCCCCC,&H000000FF,&H00333333,&H00000000,-1,0,0,0,100,100,1,0,1,3,2,5,40,40,420,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H00FFFFFF&",   # Bright white pops
        "normal_color": "\\c&H00888888&",      # Dimmed gray
        "highlight_extra": "\\fscx108\\fscy108",
    },

    # -------------------------------------------------------------------------
    # ELEGANT - Thin, sophisticated serif
    # -------------------------------------------------------------------------
    "elegant": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Times New Roman,66,&H00DDDDDD,&H000000FF,&H00111111,&H66000000,0,0,0,0,100,100,2,0,1,2,3,5,40,40,420,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H00FFFFFF&\\i1",  # White + italic
        "normal_color": "\\c&H00AAAAAA&",
        "highlight_extra": "",
    },

    # -------------------------------------------------------------------------
    # NEON - Glowing cyberpunk style
    # -------------------------------------------------------------------------
    "neon": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,76,&H00FFAAFF,&H000000FF,&H00FF00FF,&H00000000,-1,0,0,0,100,100,2,0,1,4,0,5,40,40,400,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H00FFFF00&\\blur3",  # Cyan with glow
        "normal_color": "\\c&H00FFAAFF&",             # Pink
        "highlight_extra": "",
    },

    # -------------------------------------------------------------------------
    # FIRE - Orange/red active word
    # -------------------------------------------------------------------------
    "fire": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,80,&H00FFFFFF,&H000000FF,&H00000044,&H00000000,-1,0,0,0,100,100,1,0,1,5,2,5,40,40,400,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H000088FF&",   # Orange
        "normal_color": "\\c&H00FFFFFF&",
        "highlight_extra": "\\blur1\\fscx110\\fscy110",
    },

    # -------------------------------------------------------------------------
    # HORMOZI - Alex Hormozi style: Yellow highlight, stacked words
    # -------------------------------------------------------------------------
    "hormozi": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,85,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,3,5,40,40,400,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H0000FFFF&",   # Yellow
        "normal_color": "\\c&H00FFFFFF&",
        "highlight_extra": "\\fscx120\\fscy120",  # Big pop on active word
        "words_per_line": 2,  # Fewer words, more impact
    },

    # -------------------------------------------------------------------------
    # STORYTELLER - Mystery/Documentary style: Clean yellow highlight, 1-2 words
    # Inspired by Dyatlov Pass mystery videos - center-aligned, high readability
    # -------------------------------------------------------------------------
    "storyteller": {
        "header": """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat Black,110,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,8,0,5,40,40,650,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""",
        "highlight_color": "\\c&H0000FFFF&",   # Yellow (#FFFF00 in BGR)
        "normal_color": "\\c&H00FFFFFF&",      # White
        "highlight_extra": "",                  # No scaling, clean transition
        "words_per_line": 2,                   # 1-2 words at a time for pacing
    },
}

# Default style
DEFAULT_STYLE = "red_highlight"


def _fmt(t: float) -> str:
    """Format time as H:MM:SS.CC for ASS format."""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int((t - int(t)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _group_words_into_chunks(words: list, max_words: int = 4) -> list:
    """
    Group words into display chunks of max_words each.
    Returns list of chunks, where each chunk is a list of word dicts.
    """
    chunks = []
    current_chunk = []

    for w in words:
        current_chunk.append(w)
        if len(current_chunk) >= max_words:
            chunks.append(current_chunk)
            current_chunk = []

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def build_ass_from_alignment(
    words_json: str,
    ass_out: str,
    style: str = DEFAULT_STYLE,
    words_per_chunk: int = 2
):
    """
    Build TikTok-style karaoke captions from word alignment JSON.

    Args:
        words_json: Path to JSON file with word timings
        ass_out: Output path for ASS subtitle file
        style: Caption style preset (red_highlight, karaoke, beast, etc.)
        words_per_chunk: How many words to show at once (default: 2)
    """
    words = json.loads(Path(words_json).read_text())

    if not words:
        Path(ass_out).write_text(STYLES[DEFAULT_STYLE]["header"], encoding="utf-8")
        return ass_out

    # Get style config
    if style not in STYLES:
        print(f"[captions] Unknown style '{style}', using '{DEFAULT_STYLE}'")
        style = DEFAULT_STYLE

    cfg = STYLES[style]
    header = cfg["header"]

    # Override words_per_chunk if style specifies it
    if "words_per_line" in cfg:
        words_per_chunk = cfg["words_per_line"]

    # Group words into chunks
    chunks = _group_words_into_chunks(words, max_words=words_per_chunk)

    body = []

    # Check if using box-style highlighting (karaoke style)
    use_box = cfg.get("use_box_style", False)

    if use_box:
        # BOX STYLE: Show all words, but highlighted word uses BoxHighlight style
        for chunk in chunks:
            for i, current_word in enumerate(chunk):
                word_start = current_word["start"]
                word_end = current_word["end"]

                # Build text - all words shown, current one will be on different layer
                all_words = " ".join(w["word"].strip().upper() for w in chunk)

                # Base layer - all words in default style
                start_str = _fmt(word_start)
                end_str = _fmt(word_end)

                # Find position of current word for box
                words_before = chunk[:i]
                current_text = current_word["word"].strip().upper()

                # Show all words on base layer
                body.append(
                    f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{all_words}"
                )

                # Highlight just the current word with box style
                # We use positioning to overlay just that word
                body.append(
                    f"Dialogue: 1,{start_str},{end_str},BoxHighlight,,0,0,0,,{current_text}"
                )
    else:
        # INLINE COLOR STYLE: Color changes within the text
        highlight_color = cfg["highlight_color"]
        normal_color = cfg["normal_color"]
        highlight_extra = cfg.get("highlight_extra", "")

        for chunk in chunks:
            for i, current_word in enumerate(chunk):
                word_start = current_word["start"]
                word_end = current_word["end"]

                # Build the display text with inline color overrides
                parts = []
                for j, w in enumerate(chunk):
                    word_text = w["word"].strip().upper()
                    if j == i:
                        # Current word - highlighted with extras
                        parts.append(f"{{{highlight_color}{highlight_extra}}}{word_text}{{\\r}}")
                    else:
                        # Other words - normal color
                        parts.append(f"{{{normal_color}}}{word_text}{{\\r}}")

                display_text = " ".join(parts)

                start_str = _fmt(word_start)
                end_str = _fmt(word_end)

                body.append(
                    f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{display_text}"
                )

    full_ass = header + "\n".join(body)
    Path(ass_out).write_text(full_ass, encoding="utf-8")

    print(f"[captions] Generated {len(body)} subtitle events with style '{style}'")
    return ass_out


def build_ass_word_by_word(
    words_json: str,
    ass_out: str,
    style: str = "beast"
):
    """
    Alternative: Show ONE word at a time with pop animation.
    Good for fast-paced, high-energy content.
    """
    words = json.loads(Path(words_json).read_text())

    cfg = STYLES.get(style, STYLES["beast"])
    header = cfg["header"]

    body = []

    for w in words:
        word = w["word"].strip().upper()
        start = _fmt(w["start"])
        end = _fmt(w["end"])

        # Pop animation: scale up then back
        anim = "{\\fscx85\\fscy85\\t(0,60,\\fscx110\\fscy110)\\t(60,120,\\fscx100\\fscy100)}"

        body.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{anim}{word}"
        )

    Path(ass_out).write_text(header + "\n".join(body), encoding="utf-8")
    print(f"[captions] Generated {len(body)} word-by-word events")
    return ass_out


def list_styles() -> list[str]:
    """Return list of available style names."""
    return list(STYLES.keys())


def burn_captions(input_video: str, ass_path: str, output_video: str):
    """Burn ASS subtitles onto video using ffmpeg."""

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "copy",
        output_video,
    ]

    print(f"[captions] Burning ASS onto video…")
    print(f"[captions] Style file: {ass_path}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[captions] FFmpeg error, trying subtitles filter…")
        print(f"[captions] stderr: {result.stderr[:500]}")

        # Fallback to subtitles filter
        cmd_alt = [
            "ffmpeg",
            "-y",
            "-i", input_video,
            "-vf", f"subtitles={ass_path}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "copy",
            output_video,
        ]
        subprocess.run(cmd_alt, check=True)

    print(f"[captions] Done → {output_video}")


# =============================================================================
# CLI
# =============================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python captions.py <words.json> <output.ass> [style]")
        print(f"\nAvailable styles: {', '.join(list_styles())}")
        sys.exit(1)

    words_json = sys.argv[1]
    ass_out = sys.argv[2]
    style = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_STYLE

    print(f"[captions] Building ASS with style: {style}")
    build_ass_from_alignment(words_json, ass_out, style=style)