"use client";

import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { Play, Pause, Check, Upload, Music } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRef, useState } from "react";
import { musicTracks } from "@/data/media";

const moodColors: Record<string, string> = {
  "Upbeat": "bg-yellow-500/20 text-yellow-500",
  "Suspense": "bg-orange-500/20 text-orange-500",
  "Calm": "bg-green-500/20 text-green-500",
  "Epic": "bg-purple-500/20 text-purple-500",
  "Dark": "bg-gray-500/20 text-gray-400",
  "Horror": "bg-red-500/20 text-red-500",
  "Uplifting": "bg-blue-500/20 text-blue-500",
  "Mystery": "bg-indigo-500/20 text-indigo-500",
};

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step3Music({ formData, updateFormData }: Props) {
  const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset");
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const stop = () => {
    audioRef.current?.pause();
    audioRef.current = null;
    setPlayingId(null);
  };

  const play = (url?: string, id?: string) => {
    if (!url) return;
    stop();
    const audio = new Audio(url);
    audioRef.current = audio;
    setPlayingId(id || null);
    audio.onended = stop;
    audio.play().catch(() => stop());
  };

  const toggleTrack = (trackId: string) => {
    const current = formData.musicTracks || [];
    if (current.includes(trackId)) {
      updateFormData({ musicTracks: current.filter((id) => id !== trackId) });
    } else {
      updateFormData({ musicTracks: [...current, trackId] });
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Background Music</h2>
        <p className="text-muted-foreground">
          Choose songs for your videos. We'll pick a random one for each video.
        </p>
        <span className="inline-block mt-2 text-xs bg-muted px-2 py-1 rounded">Optional</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={activeTab === "preset" ? "default" : "outline"}
          onClick={() => setActiveTab("preset")}
          className="gap-2"
        >
          <Music className="h-4 w-4" />
          Preset Music
        </Button>
        <Button
          variant={activeTab === "custom" ? "default" : "outline"}
          onClick={() => setActiveTab("custom")}
          className="gap-2"
        >
          <Upload className="h-4 w-4" />
          Custom
        </Button>
      </div>

      {activeTab === "preset" ? (
        <div className="space-y-3">
          {musicTracks.map((track) => {
            const isSelected = formData.musicTracks?.includes(track.id);
            return (
              <button
                key={track.id}
                onClick={() => toggleTrack(track.id)}
                className={cn(
                  "w-full flex items-center gap-4 p-4 rounded-xl border-2 text-left transition-all",
                  isSelected
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                )}
              >
                <div
                  className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    moodColors[track.mood] || "bg-muted"
                  )}
                >
                  <Music className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{track.name}</span>
                    <span className={cn("text-xs px-2 py-0.5 rounded-full", moodColors[track.mood])}>
                      {track.mood}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">{track.description}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (playingId === track.id) {
                      stop();
                    } else {
                      play(track.sampleUrl, track.id);
                    }
                  }}
                >
                  {playingId === track.id ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
                {isSelected && (
                  <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                    <Check className="h-4 w-4 text-primary-foreground" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      ) : (
        <div className="border-2 border-dashed rounded-xl p-12 text-center">
          <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="font-semibold mb-2">Upload Custom Music</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Drag and drop your audio file here, or click to browse
          </p>
          <Button variant="outline">Choose File</Button>
          <p className="text-xs text-muted-foreground mt-4">
            Supports MP3, WAV, M4A (max 10MB)
          </p>
        </div>
      )}

      {formData.musicTracks && formData.musicTracks.length > 0 && (
        <p className="text-sm text-muted-foreground mt-4">
          {formData.musicTracks.length} track(s) selected
        </p>
      )}
    </div>
  );
}
