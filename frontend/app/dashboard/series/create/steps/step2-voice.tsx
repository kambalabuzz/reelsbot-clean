"use client";

import { useRef, useState } from "react";
import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { Play, Pause, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { voices } from "@/data/media";

const languages = [
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "es", name: "Spanish", flag: "🇪🇸" },
  { code: "fr", name: "French", flag: "🇫🇷" },
  { code: "de", name: "German", flag: "🇩🇪" },
  { code: "it", name: "Italian", flag: "🇮🇹" },
  { code: "pt", name: "Portuguese", flag: "🇧🇷" },
  { code: "ja", name: "Japanese", flag: "🇯🇵" },
  { code: "ko", name: "Korean", flag: "🇰🇷" },
  { code: "zh", name: "Chinese", flag: "🇨🇳" },
  { code: "ru", name: "Russian", flag: "🇷🇺" },
  { code: "ar", name: "Arabic", flag: "🇸🇦" },
  { code: "hi", name: "Hindi", flag: "🇮🇳" },
];

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step2Voice({ formData, updateFormData }: Props) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const availableVoices = voices.filter((v) => v.language === formData.language);
  const fallbackVoices = voices.filter((v) => v.language === "en");
  const displayVoices = availableVoices.length ? availableVoices : fallbackVoices;

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

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Language & Voice</h2>
        <p className="text-muted-foreground">
          Choose the language and voice style for your videos
        </p>
      </div>

      {/* Language Selection */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Language</h3>
        <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => updateFormData({ language: lang.code })}
              className={cn(
                "flex items-center gap-2 p-3 rounded-lg border transition-all",
                formData.language === lang.code
                  ? "border-primary bg-primary/10"
                  : "border-border hover:border-primary/50 hover:bg-muted/50"
              )}
            >
              <span className="text-xl">{lang.flag}</span>
              <span className="text-sm font-medium">{lang.name}</span>
              {formData.language === lang.code && (
                <Check className="h-4 w-4 text-primary ml-auto" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Voice Selection */}
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Voice Style (Built-in)</h3>
          <div className="grid md:grid-cols-2 gap-4">
            {displayVoices.map((voice) => (
              <button
                key={voice.id}
                onClick={() => updateFormData({ voice: voice.id })}
                className={cn(
                  "flex items-start gap-4 p-4 rounded-xl border-2 text-left transition-all",
                  formData.voice === voice.id
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                )}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold">{voice.name}</span>
                    <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
                      {voice.gender}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {voice.description}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="flex-shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (playingId === voice.id) {
                      stop();
                    } else {
                      play(voice.sampleUrl, voice.id);
                    }
                  }}
                >
                  {playingId === voice.id ? (
                    <Pause className="h-4 w-4" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                </Button>
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          {/* ElevenLabs picker disabled for now */}
        </div>
      </div>
    </div>
  );
}
