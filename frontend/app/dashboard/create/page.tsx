"use client";

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Wand2,
  Play,
  Download,
  Share2,
  Loader2,
  CheckCircle,
  Image,
  Mic,
  ChevronRight,
  Zap,
  TrendingUp,
  ListChecks,
  Radio,
  Music2,
  PlayCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import { getApiBase } from "@/lib/api";

const VOICE_OPTIONS = [
  { id: "adam", name: "Adam", desc: "Deep and authoritative", gender: "male" },
  { id: "john", name: "John", desc: "Natural storyteller", gender: "male" },
  { id: "marcus", name: "Marcus", desc: "Dark and mysterious", gender: "male" },
  { id: "alex", name: "Alex", desc: "Neutral, versatile", gender: "neutral" },
  { id: "sarah", name: "Sarah", desc: "Warm and engaging", gender: "female" },
  { id: "emma", name: "Emma", desc: "Calm and soothing", gender: "female" },
];

const ART_STYLES = [
  { id: "cinematic", name: "Cinematic", preview: "🎬" },
  { id: "anime", name: "Anime", preview: "🎨" },
  { id: "comic", name: "Dark Comic", preview: "📓" },
  { id: "realistic", name: "Realistic", preview: "📸" },
  { id: "horror", name: "Horror", preview: "👻" },
  { id: "cyberpunk", name: "Cyberpunk", preview: "🌃" },
];

const NICHES = [
  "horror",
  "mystery",
  "true_crime",
  "motivation",
  "finance",
  "tech",
  "history",
  "science",
  "entertainment",
];

const BGM_LIBRARY = [
  { id: "orion_dark_mystery", name: "Orion's Dark Mystery" },
  { id: "orion_cinematic_pulse", name: "Orion's Cinematic Pulse" },
  { id: "orion_uplift", name: "Orion's Uplift" },
];

const CAPTION_STYLES = [
  { id: "red_highlight", name: "Red Highlight" },
  { id: "karaoke", name: "Karaoke" },
  { id: "beast", name: "Beast" },
  { id: "bold_stroke", name: "Bold Stroke" },
  { id: "sleek", name: "Sleek" },
  { id: "majestic", name: "Majestic" },
  { id: "elegant", name: "Elegant" },
  { id: "neon", name: "Neon" },
  { id: "fire", name: "Fire" },
  { id: "hormozi", name: "Hormozi" },
  { id: "storyteller", name: "Storyteller" },
];

const PLACEHOLDER = "https://via.placeholder.com/1080x1920/1a1a2e/ffffff?text=Scene";

type GenerationStep = "idle" | "script" | "voice" | "images" | "assembly" | "done";

export default function AIDirectorPage() {
  const apiBase = useMemo(() => getApiBase(), []);
  const [topic, setTopic] = useState("");
  const [voice, setVoice] = useState("adam");
  const [artStyle, setArtStyle] = useState("cinematic");
  const [niche, setNiche] = useState("entertainment");
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState<GenerationStep>("idle");
  const [result, setResult] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [includeCaptions, setIncludeCaptions] = useState(true);
  const [captionStyle, setCaptionStyle] = useState("karaoke");
  const [bgmMode, setBgmMode] = useState<"random" | "library" | "custom" | "none">("random");
  const [bgmTrackId, setBgmTrackId] = useState<string | null>(BGM_LIBRARY[0]?.id ?? null);
  const [bgmCustomUrl, setBgmCustomUrl] = useState("");
  const [history, setHistory] = useState<any[]>([]);
  const [hasLoadedHistory, setHasLoadedHistory] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [progressText, setProgressText] = useState("Idle");
  const [assemblyMessage, setAssemblyMessage] = useState("");
  const [assemblyAvailable, setAssemblyAvailable] = useState(true);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);

  const hasAssets = useMemo(() => !!result && Array.isArray(result.image_urls) && result.image_urls.length > 0, [result]);
  const hasVideo = useMemo(() => !!result?.video_url, [result]);

  // localStorage key for persisting generation state
  const STORAGE_KEY = "ai-director-generation-state";

  const steps = [
    { id: "script", label: "Writing Script", icon: Sparkles },
    { id: "voice", label: "Generating Voice", icon: Mic },
    { id: "images", label: "Creating Visuals", icon: Image },
    { id: "assembly", label: "Assembling Video", icon: Play },
  ];

  // Save generation state to localStorage
  const saveGenerationState = (videoId: string, step: GenerationStep, data?: any) => {
    const state = {
      videoId,
      step,
      topic,
      timestamp: Date.now(),
      data,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    setActiveVideoId(videoId);
  };

  // Clear generation state from localStorage
  const clearGenerationState = () => {
    localStorage.removeItem(STORAGE_KEY);
    setActiveVideoId(null);
  };

  // Load and resume generation state on mount
  useEffect(() => {
    const savedState = localStorage.getItem(STORAGE_KEY);
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        const age = Date.now() - state.timestamp;

        // Only resume if less than 10 minutes old
        if (age < 10 * 60 * 1000) {
          setTopic(state.topic || "");
          setActiveVideoId(state.videoId);
          setIsGenerating(true);
          setCurrentStep(state.step);

          if (state.data) {
            setResult(state.data);
            setProgressText(state.data.video_url ? "Video ready" : "Processing...");
          }

          // Resume polling for this video
          if (state.videoId) {
            void pollVideoStatus(state.videoId);
          }

          toast.info("Resumed previous generation");
        } else {
          // State too old, clear it
          clearGenerationState();
        }
      } catch (e) {
        console.error("Failed to restore state:", e);
        clearGenerationState();
      }
    }
  }, [apiBase]);

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error("Please enter a topic");
      return;
    }
    if (!apiBase) {
      toast.error("API URL not configured.");
      return;
    }

    setIsGenerating(true);
    setResult(null);
    setProgressText("Starting...");

    try {
      // Simulate step progression (real API would send progress updates)
      setCurrentStep("script");
      await new Promise((r) => setTimeout(r, 1500));

      setCurrentStep("voice");
      await new Promise((r) => setTimeout(r, 1500));

      setCurrentStep("images");
      setProgressText("Generating visuals...");

      const response = await fetch(`${apiBase}/api/generate-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic,
          voice,
          art_style: artStyle,
          niche,
          beats_count: 8,
          include_captions: includeCaptions,
          caption_style: captionStyle,
          bgm_mode: bgmMode,
          bgm_track_id: bgmMode === "library" ? bgmTrackId : null,
          bgm_custom_url: bgmMode === "custom" ? bgmCustomUrl : null,
          assemble: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || errorData.error || "Generation failed";
        throw new Error(errorMessage);
      }

      const data = await response.json();

      // Save state with video data
      saveGenerationState(data.video_id, "assembly", data);

      setCurrentStep("assembly");
      setProgressText("Assembling video...");
      await new Promise((r) => setTimeout(r, 1000));

      setCurrentStep("done");
      setResult(data);
      setProgressText(data.video_url ? "Video ready" : "Assets ready");
      setAssemblyMessage(data.message || "");
      setAssemblyAvailable(data.assembly_available ?? true);
      toast.success(data.video_url ? "Video ready!" : "Assets generated!");

      if (!data.video_url && data.video_id) {
        // Poll status until video is ready or timeout
        void pollVideoStatus(data.video_id);
      } else if (data.video_url) {
        // Video is complete, clear saved state
        clearGenerationState();
      }

      void fetchHistory();
    } catch (error) {
      console.error(error);
      const errorMessage = error instanceof Error ? error.message : "Generation failed. Please try again.";

      // Show user-friendly messages for common errors
      if (errorMessage.includes("quota") || errorMessage.includes("insufficient_quota")) {
        toast.error("OpenAI API quota exceeded. Please check your API billing at platform.openai.com");
      } else if (errorMessage.includes("429")) {
        toast.error("Rate limit exceeded. Please wait a moment and try again.");
      } else {
        toast.error(errorMessage);
      }

      // Clear state on error
      clearGenerationState();
    } finally {
      setIsGenerating(false);
      setCurrentStep("idle");
    }
  };

  const pollVideoStatus = async (videoId: string) => {
    const start = Date.now();
    const timeout = 1000 * 60 * 10; // Increased to 10 minutes

    while (Date.now() - start < timeout) {
      try {
        const res = await fetch(`${apiBase}/api/video/${videoId}`);
        if (res.ok) {
          const data = await res.json();

          // Update progress text with actual status
          const statusText = data.assembly_stage || data.status || "processing";
          setProgressText(`${statusText}... ${data.assembly_progress || 0}%`);
          setAssemblyAvailable(data.assembly_available ?? true);

          // Update result with latest data
          setResult((prev: any) => ({ ...(prev || {}), ...data }));

          // Update saved state
          if (data.status === "assembling") {
            saveGenerationState(videoId, "assembly", data);
          }

          if (data.video_url) {
            // Video is complete!
            setCurrentStep("done");
            setProgressText("Video ready!");
            toast.success("Video ready!");
            clearGenerationState();
            setIsGenerating(false);
            return;
          }

          if (data.status === "assembly_failed" || data.status === "failed") {
            setProgressText("Assembly failed");
            toast.error(data.assembly_log || "Video assembly failed");
            clearGenerationState();
            setIsGenerating(false);
            return;
          }

          if (data.message) setAssemblyMessage(data.message);
        }
      } catch (e) {
        console.error("Poll error:", e);
      }

      // Poll every 3 seconds
      await new Promise((r) => setTimeout(r, 3000));
    }

    // Timeout reached - keep state saved so user can come back
    setProgressText("Assembly still running; navigate away and come back to check progress");
    setIsGenerating(false);
  };

  const fetchHistory = async () => {
    try {
      if (!apiBase) return;
      const res = await fetch(`${apiBase}/api/videos`);
      if (!res.ok) return;
      const data = await res.json();
      setHistory(data || []);
      setHasLoadedHistory(true);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (!hasLoadedHistory) {
      void fetchHistory();
    }
  }, [hasLoadedHistory]);

  const handleDownload = async () => {
    if (!result) return;
    if (hasVideo && result.video_url) {
      window.open(result.video_url, "_blank");
      return;
    }
    if (!hasAssets) {
      toast.error("No assets to download yet.");
      return;
    }
    setDownloading(true);
    try {
      const zip = new JSZip();
      // Add script
      if (result.script) {
        zip.file("script.json", JSON.stringify(result.script, null, 2));
      }
      // Add images
      const imageFolder = zip.folder("images");
      if (imageFolder) {
        await Promise.all(
          result.image_urls.map(async (url: string, idx: number) => {
            try {
              const resp = await fetch(url);
              const blob = await resp.blob();
              const ext = blob.type.split("/")[1] || "jpg";
              imageFolder.file(`scene_${idx + 1}.${ext}`, blob);
            } catch (e) {
              console.error("Image download failed", e);
            }
          })
        );
      }
      // Add audio if present
      if (result.audio_url) {
        try {
          const resp = await fetch(result.audio_url);
          const blob = await resp.blob();
          zip.file("voiceover.mp3", blob);
        } catch (e) {
          console.error("Audio download failed", e);
        }
      }
      const content = await zip.generateAsync({ type: "blob" });
      saveAs(content, `assets-${result.video_id || "video"}.zip`);
    } catch (e) {
      console.error(e);
      toast.error("Download failed. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  const handleShare = async () => {
    if (!result) return;
    const shareUrl = result.video_url || window.location.href;
    setSharing(true);
    try {
      if (navigator.share) {
        await navigator.share({
          title: result.script?.title || "AI Director video",
          text: "Check out this AI-generated video",
          url: shareUrl,
        });
      } else {
        await navigator.clipboard.writeText(shareUrl);
        toast.success("Link copied to clipboard");
      }
    } catch (e) {
      console.error(e);
      toast.error("Share failed.");
    } finally {
      setSharing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-purple-900/20 to-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        {isGenerating && (
          <div className="text-center text-gray-300 mb-4 text-sm">
            {progressText} • This usually takes 20-60 seconds depending on AI load.
          </div>
        )}
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="inline-flex items-center gap-2 bg-purple-500/20 px-4 py-2 rounded-full mb-4">
            <Zap className="w-4 h-4 text-purple-400" />
            <span className="text-purple-300 text-sm font-medium">AI Director Mode</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">One Click. Viral Video.</h1>
          <p className="text-gray-400">Describe your video idea and let AI handle everything.</p>
          {assemblyAvailable === false && (
            <p className="text-xs text-yellow-400 mt-2">
              Server cannot assemble video (ffmpeg/storage missing). Assets will be returned instead.
            </p>
          )}
        </motion.div>

        {/* Main Input Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 mb-6"
        >
          <div className="mb-4">
            <label className="text-white font-medium mb-2 block">What's your video about?</label>
            <Textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., The scariest abandoned hospital in America that nobody talks about..."
              className="bg-gray-900/50 border-gray-700 text-white min-h-[100px] text-lg"
              disabled={isGenerating}
            />
          </div>

          {/* Quick Style Selection */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* Voice */}
            <div>
              <label className="text-gray-400 text-sm mb-2 block">Voice</label>
              <div className="grid grid-cols-2 gap-2">
                {VOICE_OPTIONS.map((v) => (
                  <button
                    key={v.id}
                    onClick={() => setVoice(v.id)}
                    disabled={isGenerating}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      voice === v.id
                        ? "border-purple-500 bg-purple-500/20 text-white"
                        : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                    }`}
                  >
                    <div className="font-medium text-sm">{v.name}</div>
                    <div className="text-xs opacity-60">{v.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Art Style */}
            <div>
              <label className="text-gray-400 text-sm mb-2 block">Visual Style</label>
              <div className="grid grid-cols-3 gap-2">
                {ART_STYLES.map((style) => (
                  <button
                    key={style.id}
                    onClick={() => setArtStyle(style.id)}
                    disabled={isGenerating}
                    className={`p-3 rounded-lg border text-center transition-all ${
                      artStyle === style.id
                        ? "border-purple-500 bg-purple-500/20 text-white"
                        : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                    }`}
                  >
                    <div className="text-2xl mb-1">{style.preview}</div>
                    <div className="text-xs">{style.name}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Advanced Options Toggle */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-gray-400 text-sm flex items-center gap-1 mb-4 hover:text-white transition-colors"
          >
            <ChevronRight className={`w-4 h-4 transition-transform ${showAdvanced ? "rotate-90" : ""}`} />
            Advanced options
          </button>

          <AnimatePresence>
            {showAdvanced && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="mb-4 overflow-hidden"
              >
                <div className="grid grid-cols-3 gap-4">
                  <div className="col-span-3">
                    <p className="text-gray-300 text-sm mb-2 flex items-center gap-2">
                      <ListChecks className="w-4 h-4" /> Niche presets
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      {NICHES.map((n) => (
                        <button
                          key={n}
                          onClick={() => setNiche(n)}
                          disabled={isGenerating}
                          className={`p-2 rounded-lg border text-sm transition-all ${
                            niche === n
                              ? "border-purple-500 bg-purple-500/20 text-white"
                              : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                          }`}
                        >
                          {n.replace("_", " ")}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="col-span-3 mt-4">
                    <p className="text-gray-300 text-sm mb-2 flex items-center gap-2">
                      <Radio className="w-4 h-4" /> Captions
                    </p>
                    <div className="flex items-center gap-3 mb-3">
                      <button
                        onClick={() => setIncludeCaptions(!includeCaptions)}
                        disabled={isGenerating}
                        className={`px-3 py-2 rounded-lg border text-sm transition-all ${
                          includeCaptions
                            ? "border-purple-500 bg-purple-500/20 text-white"
                            : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                        }`}
                      >
                        {includeCaptions ? "Captions ON" : "Captions OFF"}
                      </button>
                    </div>
                    {includeCaptions && (
                      <div className="grid grid-cols-5 gap-2">
                        {CAPTION_STYLES.map((style) => (
                          <button
                            key={style.id}
                            onClick={() => setCaptionStyle(style.id)}
                            disabled={isGenerating}
                            className={`p-2 rounded-lg border text-xs transition-all ${
                              captionStyle === style.id
                                ? "border-purple-500 bg-purple-500/20 text-white"
                                : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                            }`}
                          >
                            {style.name}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="col-span-3 mt-2">
                    <p className="text-gray-300 text-sm mb-2 flex items-center gap-2">
                      <Music2 className="w-4 h-4" /> Background music
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      {["random", "library", "custom", "none"].map((mode) => (
                        <button
                          key={mode}
                          onClick={() => setBgmMode(mode as any)}
                          disabled={isGenerating}
                          className={`p-3 rounded-lg border text-left transition-all ${
                            bgmMode === mode
                              ? "border-purple-500 bg-purple-500/20 text-white"
                              : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                          }`}
                        >
                          <div className="font-medium text-sm capitalize">
                            {mode === "random" ? "Random (Orion's picks)" : mode}
                          </div>
                          <div className="text-xs opacity-60">
                            {mode === "random" && "Auto-pick from Orion's library"}
                            {mode === "library" && "Choose one of our curated tracks"}
                            {mode === "custom" && "Paste your own music URL"}
                            {mode === "none" && "No music"}
                          </div>
                        </button>
                      ))}
                    </div>

                    {bgmMode === "library" && (
                      <div className="grid grid-cols-3 gap-2 mt-2">
                        {BGM_LIBRARY.map((track) => (
                          <button
                            key={track.id}
                            onClick={() => setBgmTrackId(track.id)}
                            disabled={isGenerating}
                            className={`p-2 rounded-lg border text-xs transition-all ${
                              bgmTrackId === track.id
                                ? "border-purple-500 bg-purple-500/20 text-white"
                                : "border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600"
                            }`}
                          >
                            {track.name}
                          </button>
                        ))}
                      </div>
                    )}

                    {bgmMode === "custom" && (
                      <div className="mt-2">
                        <Input
                          placeholder="https://your-music-url.mp3"
                          value={bgmCustomUrl}
                          onChange={(e) => setBgmCustomUrl(e.target.value)}
                          disabled={isGenerating}
                          className="bg-gray-900/50 border-gray-700 text-white"
                        />
                        <p className="text-xs text-gray-500 mt-1">We accept direct links to mp3 files.</p>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Generate Button */}
          <Button
            onClick={handleGenerate}
            disabled={isGenerating || !topic.trim()}
            className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
          >
            {isGenerating ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Creating your video...
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Wand2 className="w-5 h-5" />
                Generate Video
              </span>
            )}
          </Button>
        </motion.div>

        {/* Progress Steps */}
        <AnimatePresence>
          {isGenerating && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6 mb-6"
            >
              <div className="flex justify-between">
                {steps.map((step, index) => {
                  const Icon = step.icon;
                  const isActive = currentStep === step.id;
                  const isComplete = steps.findIndex((s) => s.id === currentStep) > index;

                  return (
                    <div key={step.id} className="flex flex-col items-center flex-1">
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${
                          isComplete
                            ? "bg-green-500"
                            : isActive
                              ? "bg-purple-500 animate-pulse"
                              : "bg-gray-700"
                        }`}
                      >
                        {isComplete ? (
                          <CheckCircle className="w-6 h-6 text-white" />
                        ) : isActive ? (
                          <Loader2 className="w-6 h-6 text-white animate-spin" />
                        ) : (
                          <Icon className="w-6 h-6 text-gray-400" />
                        )}
                      </div>
                      <span className={`text-sm ${isActive || isComplete ? "text-white" : "text-gray-500"}`}>
                        {step.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6"
            >
              <div className="flex items-center gap-2 text-green-400 mb-4">
                <CheckCircle className="w-5 h-5" />
                <span className="font-medium">
                  {result.video_url ? "Video Ready!" : "Assets Generated Successfully!"}
                </span>
              </div>

              {result.video_url && (
                <div className="mb-6">
                  <h3 className="text-white font-medium mb-2 flex items-center gap-2">
                    <PlayCircle className="w-5 h-5" />
                    Preview
                  </h3>
                  <video
                    controls
                    className="w-full rounded-lg border border-gray-700"
                    src={result.video_url}
                  />
                </div>
              )}
              {!result.video_url && assemblyMessage && (
                <div className="mb-4 text-sm text-yellow-400">
                  {assemblyMessage}
                </div>
              )}

              {/* Script Preview */}
              <div className="mb-6">
                <h3 className="text-white font-medium mb-2">Script</h3>
                <div className="bg-gray-900/50 rounded-lg p-4 text-gray-300 text-sm">
                  <p className="text-purple-400 font-medium mb-2">Hook: {result.script?.hook}</p>
                  {result.script?.beats?.map((beat: any, i: number) => (
                    <p key={i} className="mb-1">
                      {beat.line}
                    </p>
                  ))}
                  <p className="text-purple-400 font-medium mt-2">CTA: {result.script?.cta}</p>
                </div>
              </div>

              {/* Generated Images */}
              <div className="mb-6">
                <h3 className="text-white font-medium mb-2">Generated Scenes</h3>
                <div className="grid grid-cols-4 gap-2">
                  {(result.image_urls || []).map((url: string, i: number) => (
                    <img
                      key={i}
                      src={url || `${PLACEHOLDER}+${i + 1}`}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = `${PLACEHOLDER}+${i + 1}`;
                      }}
                      alt={`Scene ${i + 1}`}
                      className="rounded-lg aspect-[9/16] object-cover w-full bg-gray-900"
                    />
                  ))}
                  {/* Fill missing slots to avoid layout gaps */}
                  {Array.from({ length: Math.max(0, 8 - (result.image_urls?.length || 0)) }).map((_, idx) => (
                    <img
                      key={`ph-${idx}`}
                      src={`${PLACEHOLDER}+${(result.image_urls?.length || 0) + idx + 1}`}
                      alt="Placeholder"
                      className="rounded-lg aspect-[9/16] object-cover w-full bg-gray-900"
                    />
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <Button
                  className="flex-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-60"
                  onClick={handleDownload}
                  disabled={downloading || (!hasAssets && !hasVideo)}
                >
                  {downloading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                  {hasVideo ? "Download Video" : "Download Assets"}
                </Button>
                <Button
                  variant="outline"
                  className="flex-1 border-gray-600 disabled:opacity-60"
                  onClick={handleShare}
                  disabled={sharing || (!hasVideo && !hasAssets)}
                >
                  {sharing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Share2 className="w-4 h-4 mr-2" />}
                  Share
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Trending Topics Suggestion */}
        {!isGenerating && !result && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="mt-6">
            <div className="flex items-center gap-2 text-gray-400 mb-3">
              <TrendingUp className="w-4 h-4" />
              <span className="text-sm">Trending topics</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                "Abandoned places nobody knows about",
                "Dark psychology tricks",
                "Historical mysteries unsolved",
                "Money secrets of millionaires",
                "Scary stories from Reddit",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setTopic(suggestion)}
                  className="px-3 py-1.5 rounded-full bg-gray-800 text-gray-300 text-sm hover:bg-gray-700 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* History */}
        {history.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6"
          >
            <div className="flex items-center gap-2 text-gray-200 mb-4">
              <ListChecks className="w-4 h-4" />
              <span className="font-medium text-sm">Your recent videos</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {history.map((item) => (
                <a
                  key={item.id || item.video_id}
                  href={`/dashboard/videos/${item.video_id}`}
                  className="p-3 rounded-lg border border-gray-700 bg-gray-900/40 hover:border-purple-500 transition-colors"
                >
                  <div className="text-sm text-white font-medium truncate">{item.topic}</div>
                  <div className="text-xs text-gray-400">Status: {item.status}</div>
                  <div className="text-xs text-gray-500">{item.video_url ? "Video ready" : "Assets only"}</div>
                </a>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
