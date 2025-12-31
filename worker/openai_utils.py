# openai_utils.py
"""
OpenAI API utilities for story generation and image creation.
Updated to support niche-specific prompts.
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
IMG_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")


# =============================================================================
# NICHE PROMPTS
# =============================================================================

NICHE_SYSTEM_PROMPTS = {
    "true_crime": (
        "You are writing a short, fast-paced true crime narration "
        "for a 45-60 second vertical video. Focus on unsolved cases, "
        "mysterious disappearances, or chilling criminal cases."
    ),
    "horror": (
        "You are writing a short, spine-chilling horror narration "
        "for a 45-60 second vertical video. Focus on creepy encounters, "
        "unexplained phenomena, or terrifying true stories."
    ),
    "mystery": (
        "You are writing a short, intriguing mystery narration "
        "for a 45-60 second vertical video. Focus on unsolved puzzles, "
        "strange occurrences, or baffling historical mysteries."
    ),
    "history": (
        "You are writing a short, engaging historical narration "
        "for a 45-60 second vertical video. Focus on fascinating "
        "historical events, forgotten stories, or surprising facts."
    ),
    "conspiracy": (
        "You are writing a short, thought-provoking narration about "
        "conspiracy theories for a 45-60 second vertical video. "
        "Present theories objectively and let viewers decide."
    ),
    "paranormal": (
        "You are writing a short, eerie paranormal narration "
        "for a 45-60 second vertical video. Focus on ghost sightings, "
        "UFO encounters, or unexplained supernatural events."
    ),
    "sci_fi": (
        "You are writing a short, mind-bending sci-fi narration "
        "for a 45-60 second vertical video. Focus on futuristic concepts, "
        "space mysteries, or technological what-ifs."
    ),
    "motivation": (
        "You are writing a short, powerful motivational narration "
        "for a 45-60 second vertical video. Focus on success stories, "
        "life lessons, or inspiring transformations."
    ),
    "finance": (
        "You are writing a short, insightful finance narration "
        "for a 45-60 second vertical video. Focus on money tips, "
        "investment stories, or financial lessons."
    ),
    "tech": (
        "You are writing a short, fascinating tech narration "
        "for a 45-60 second vertical video. Focus on emerging technology, "
        "AI developments, or tech industry stories."
    ),
}


# =============================================================================
# HELPERS
# =============================================================================

def safe_filename(text: str, max_len: int = 80) -> str:
    """Turn an arbitrary prompt/topic into a filesystem-safe slug."""
    text = text.strip().lower().replace(" ", "_")
    keep = []
    for ch in text:
        if ch.isalnum() or ch in "._-":
            keep.append(ch)
        else:
            keep.append("_")
    slug = "".join(keep)
    if len(slug) > max_len:
        slug = slug[:max_len]
    return slug or "item"


def _beats_cache_path(topic: str, beats: int, niche: str = "true_crime") -> Path:
    cache_dir = Path("cache") / "beats"
    cache_dir.mkdir(parents=True, exist_ok=True)
    slug = safe_filename(f"{niche}_{topic}_{beats}")
    return cache_dir / f"{slug}.json"


def _extract_json_block(raw: str) -> str:
    """Handle models that wrap JSON in ```json ... ``` fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        inner = "\n".join(lines[1:-1])
        raw = inner.strip()

    start_candidates = [raw.find("["), raw.find("{")]
    start_candidates = [i for i in start_candidates if i != -1]
    if not start_candidates:
        return raw
    start = min(start_candidates)

    end_bracket = raw.rfind("]")
    end_brace = raw.rfind("}")
    end_candidates = [x for x in [end_bracket, end_brace] if x != -1]
    if not end_candidates:
        return raw
    end = max(end_candidates) + 1

    return raw[start:end]


# =============================================================================
# STORY BEATS GENERATION
# =============================================================================

def generate_story_beats(
    topic: str, 
    beats: int = 12,
    niche: str = "true_crime"
) -> List[Dict]:
    """
    Generate story beats for a topic.
    
    Args:
        topic: The subject/story to cover
        beats: Number of beats (scenes) to generate
        niche: Content niche for tone/style
    
    Returns:
        List of dicts: [{"line": "...", "visual": "..."}, ...]
    """
    cache_path = _beats_cache_path(topic, beats, niche)
    if cache_path.exists():
        print(f"[cache] Reusing story beats for {topic!r}")
        return json.loads(cache_path.read_text())

    print(f"[openai] Generating {beats} story beats for {topic!r} (niche: {niche})")

    # Get niche-specific system prompt
    system_prompt = NICHE_SYSTEM_PROMPTS.get(niche, NICHE_SYSTEM_PROMPTS["true_crime"])

    prompt = f"""
{system_prompt}

Topic: "{topic}"

Return EXACTLY a JSON array of {beats} objects.
Each object must have:

  - "line": one short narration line (spoken text, punchy and engaging)
  - "visual": one visual scene description (for an illustration or frame)

Guidelines:
- Start with a hook that grabs attention
- Build tension throughout
- End with a memorable conclusion or cliffhanger
- Keep each line under 15 words
- Make visuals cinematic and specific

Example format:

[
  {{"line": "In 1978, something terrifying was discovered in the basement.", "visual": "Dark basement with a single flickering lightbulb, dusty shelves"}},
  ...
]

NO explanation, NO commentary, ONLY JSON.
""".strip()

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You output ONLY valid JSON, no prose. You are an expert short-form video scriptwriter."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        temperature=0.8,
    )

    raw = resp.choices[0].message.content or ""
    raw_json = _extract_json_block(raw)

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        raise RuntimeError(f"OpenAI did not return valid JSON:\n{raw}")

    if not isinstance(data, list):
        raise RuntimeError("Story beats JSON must be a list.")

    cleaned = []
    for item in data:
        line = str(item.get("line", "")).strip()
        visual = str(item.get("visual", "")).strip()
        if not line:
            continue
        cleaned.append({"line": line, "visual": visual})

    if not cleaned:
        raise RuntimeError("No valid beats produced by OpenAI.")

    cache_path.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    return cleaned


# =============================================================================
# IMAGE GENERATION
# =============================================================================

def generate_images(
    prompt: str,
    out_dir: str = "media_cache",
    n: int = 1,
    uniq: Optional[str] = None,
    size: str = "1024x1024",
) -> list[str]:
    """
    Generate (or reuse cached) images for a given visual prompt.

    Args:
        prompt: Full text prompt (style + scene)
        out_dir: Directory where images are stored
        n: How many images to return
        uniq: Extra key (e.g., 'beat_01') to force per-beat uniqueness
        size: Image size (1024x1024, 1024x1792, 1792x1024)
    
    Returns:
        List of file paths to generated images
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Base key from prompt
    base = safe_filename(prompt)

    # Extra disambiguation
    if uniq:
        base = f"{base}_{uniq}"
    else:
        h = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
        base = f"{base}_{h}"

    existing_paths: list[Path] = []

    # Check for cached images
    for i in range(1, n + 1):
        p = out_path / f"{base}_{i:02d}.png"
        if p.exists():
            existing_paths.append(p)

    if len(existing_paths) >= n:
        print(f"[cache] Reusing {n} cached image(s)")
        return [str(p) for p in existing_paths[:n]]

    # Generate new images
    to_generate = n - len(existing_paths)
    print(f"[openai] Generating {to_generate} image(s)…")

    resp = client.images.generate(
        model=IMG_MODEL,
        prompt=prompt,
        size=size,
        n=to_generate,
    )

    new_paths: list[Path] = []
    start_idx = len(existing_paths) + 1

    for j, img in enumerate(resp.data, start=start_idx):
        b64 = img.b64_json
        raw = base64.b64decode(b64)

        fname = f"{base}_{j:02d}.png"
        path = out_path / fname

        with path.open("wb") as f:
            f.write(raw)

        new_paths.append(path)

    all_paths = existing_paths + new_paths
    return [str(p) for p in all_paths[:n]]


# =============================================================================
# TOPIC SUGGESTIONS
# =============================================================================

def suggest_topics(niche: str, count: int = 5) -> List[str]:
    """
    Generate topic suggestions for a given niche.
    Useful for users who need content ideas.
    """
    system_prompt = NICHE_SYSTEM_PROMPTS.get(niche, NICHE_SYSTEM_PROMPTS["true_crime"])
    
    prompt = f"""
{system_prompt}

Generate {count} unique, specific topic ideas that would make great short-form videos.
Each topic should be:
- Specific enough to be a single episode
- Intriguing and click-worthy
- Not too broad or generic

Return ONLY a JSON array of strings, no other text.

Example: ["The Dyatlov Pass Incident", "The Lead Masks of Vintem Hill", ...]
"""

    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You output ONLY valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
    )

    raw = resp.choices[0].message.content or ""
    raw_json = _extract_json_block(raw)
    
    try:
        topics = json.loads(raw_json)
        return topics[:count]
    except json.JSONDecodeError:
        return []
