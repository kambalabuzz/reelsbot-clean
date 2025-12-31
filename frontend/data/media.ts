// Central catalog for voices, music tracks, and art style previews.
// Drop your files into frontend/public/media/... using the file names below.

export type Voice = {
  id: string;
  name: string;
  gender: "Male" | "Female" | "Neutral";
  description: string;
  language: string; // ISO code like en, es, hi
  sampleUrl?: string; // e.g. /media/voices/en/adam_en.mp3
};

export type MusicTrack = {
  id: string;
  name: string;
  mood: string;
  description: string;
  sampleUrl?: string; // e.g. /media/music/happy_rhythm.mp3
};

export type ArtStyle = {
  id: string;
  name: string;
  description: string;
  previewEmoji?: string;
  previewUrl?: string; // e.g. /media/art/painting.jpg
};

const voiceBase = [
  {
    id: "adam",
    name: "Adam",
    gender: "Male" as const,
    description: "Deep and authoritative storyteller.",
  },
  {
    id: "john",
    name: "John",
    gender: "Male" as const,
    description: "The perfect storyteller. Very realistic and natural.",
  },
  {
    id: "marcus",
    name: "Marcus",
    gender: "Male" as const,
    description: "Deep and mysterious. Perfect for true crime and horror.",
  },
  {
    id: "alex",
    name: "Alex",
    gender: "Neutral" as const,
    description: "Neutral and versatile. Works for any content type.",
  },
  {
    id: "sarah",
    name: "Sarah",
    gender: "Female" as const,
    description: "Warm and engaging. Great for lifestyle and motivation.",
  },
  {
    id: "emma",
    name: "Emma",
    gender: "Female" as const,
    description: "Soft and soothing. Perfect for calm, relaxing content.",
  },
];

const languageCodes = ["en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh", "ru", "ar", "hi"] as const;

export const voices: Voice[] = languageCodes.flatMap((lang) =>
  voiceBase.map((v) => ({
    ...v,
    language: lang,
    sampleUrl: `/media/voices/${lang}/${v.id}_${lang}.mp3`,
  }))
);

export const musicTracks: MusicTrack[] = [
  { id: "happy_rhythm", name: "Happy Rhythm", mood: "Upbeat", description: "Upbeat and energetic, perfect for positive content", sampleUrl: "/media/music/happy_rhythm.mp3" },
  { id: "quiet_before_storm", name: "Quiet Before Storm", mood: "Suspense", description: "Building tension and anticipation for dramatic reveals", sampleUrl: "/media/music/quiet_before_storm.mp3" },
  { id: "peaceful_vibes", name: "Peaceful Vibes", mood: "Calm", description: "Calm and soothing background for relaxed storytelling", sampleUrl: "/media/music/peaceful_vibes.mp3" },
  { id: "brilliant_symphony", name: "Brilliant Symphony", mood: "Epic", description: "Orchestral and majestic for epic storytelling", sampleUrl: "/media/music/brilliant_symphony.mp3" },
  { id: "breathing_shadows", name: "Breathing Shadows", mood: "Dark", description: "Mysterious and eerie ambiance for suspenseful videos", sampleUrl: "/media/music/breathing_shadows.mp3" },
  { id: "dark_descent", name: "Dark Descent", mood: "Horror", description: "Deep, ominous tones for horror and true crime", sampleUrl: "/media/music/dark_descent.mp3" },
  { id: "rising_hero", name: "Rising Hero", mood: "Uplifting", description: "Triumphant and inspiring, great for success stories", sampleUrl: "/media/music/rising_hero.mp3" },
  { id: "hidden_secrets", name: "Hidden Secrets", mood: "Mystery", description: "Intriguing and curious, perfect for mysteries", sampleUrl: "/media/music/hidden_secrets.mp3" },
];

export const artStyles: ArtStyle[] = [
  { id: "comic", name: "Comic", description: "Classic comic book style", previewEmoji: "🎨", previewUrl: "/media/art/comic.jpg" },
  { id: "creepy_comic", name: "Creepy Comic", description: "Dark horror comic aesthetic", previewEmoji: "👻", previewUrl: "/media/art/creepy_comic.jpg" },
  { id: "painting", name: "Painting", description: "Classical oil painting style", previewEmoji: "🖼️", previewUrl: "/media/art/painting.jpg" },
  { id: "ghibli", name: "Ghibli", description: "Studio Ghibli anime style", previewEmoji: "🌸", previewUrl: "/media/art/ghibli.jpg" },
  { id: "anime", name: "Anime", description: "Modern anime illustration", previewEmoji: "⚡", previewUrl: "/media/art/anime.jpg" },
  { id: "dark_fantasy", name: "Dark Fantasy", description: "Gothic fantasy art", previewEmoji: "🏰", previewUrl: "/media/art/dark_fantasy.jpg" },
  { id: "lego", name: "Lego", description: "LEGO minifigure style", previewEmoji: "🧱", previewUrl: "/media/art/lego.jpg" },
  { id: "polaroid", name: "Polaroid", description: "Vintage photo aesthetic", previewEmoji: "📷", previewUrl: "/media/art/polaroid.jpg" },
  { id: "disney", name: "Disney", description: "Disney/Pixar 3D animation", previewEmoji: "✨", previewUrl: "/media/art/disney.jpg" },
  { id: "realistic", name: "Realism", description: "Photorealistic digital art", previewEmoji: "📸", previewUrl: "/media/art/realistic.jpg" },
  { id: "fantastic", name: "Fantastic", description: "Surreal fantasy realism", previewEmoji: "🌊", previewUrl: "/media/art/fantastic.jpg" },
  { id: "noir", name: "Noir", description: "Film noir black & white", previewEmoji: "🎬", previewUrl: "/media/art/noir.jpg" },
  { id: "cyberpunk", name: "Cyberpunk", description: "Neon-lit futuristic", previewEmoji: "🌃", previewUrl: "/media/art/cyberpunk.jpg" },
  { id: "watercolor", name: "Watercolor", description: "Soft watercolor painting", previewEmoji: "💧", previewUrl: "/media/art/watercolor.jpg" },
  { id: "pixel_art", name: "Pixel Art", description: "Retro 16-bit gaming", previewEmoji: "👾", previewUrl: "/media/art/pixel_art.jpg" },
  { id: "claymation", name: "Claymation", description: "Stop-motion clay style", previewEmoji: "🎭", previewUrl: "/media/art/claymation.jpg" },
  { id: "minimalist", name: "Minimalist", description: "Clean minimal design", previewEmoji: "⬜", previewUrl: "/media/art/minimalist.jpg" },
  { id: "vaporwave", name: "Vaporwave", description: "80s retro aesthetic", previewEmoji: "🌴", previewUrl: "/media/art/vaporwave.jpg" },
  { id: "steampunk", name: "Steampunk", description: "Victorian machinery", previewEmoji: "⚙️", previewUrl: "/media/art/steampunk.jpg" },
  { id: "lofi", name: "Lo-Fi", description: "Cozy lofi aesthetic", previewEmoji: "🎧", previewUrl: "/media/art/lofi.jpg" },
];
