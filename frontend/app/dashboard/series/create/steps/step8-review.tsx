"use client";

import { SeriesFormData } from "../page";
import { Check, Edit2 } from "lucide-react";
import { Button } from "@/components/ui/button";

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

const niches: Record<string, string> = {
  true_crime: "True Crime",
  horror: "Horror",
  history: "History",
  mystery: "Mystery",
  conspiracy: "Conspiracy",
  paranormal: "Paranormal",
  sci_fi: "Sci-Fi",
  motivation: "Motivation",
  finance: "Finance",
  tech: "Tech",
};

const artStyles: Record<string, string> = {
  comic: "Comic",
  creepy_comic: "Creepy Comic",
  painting: "Painting",
  ghibli: "Ghibli",
  anime: "Anime",
  dark_fantasy: "Dark Fantasy",
  lego: "Lego",
  polaroid: "Polaroid",
  disney: "Disney",
  realistic: "Realism",
};

const voices: Record<string, string> = {
  adam: "Adam",
  john: "John",
  marcus: "Marcus",
  alex: "Alex",
  sarah: "Sarah",
  emma: "Emma",
};

const captionStyles: Record<string, string> = {
  red_highlight: "Red Highlight",
  karaoke: "Karaoke",
  beast: "Beast",
  bold_stroke: "Bold Stroke",
  sleek: "Sleek",
  majestic: "Majestic",
  elegant: "Elegant",
  neon: "Neon",
  fire: "Fire",
  hormozi: "Hormozi",
};

const durations: Record<string, string> = {
  short: "15-30 seconds",
  medium: "30-45 seconds",
  long: "45-60 seconds",
  extra_long: "60-90 seconds",
};

const frequencies: Record<string, string> = {
  three_per_week: "3x per week",
  daily: "Every day",
  twice_daily: "2x per day",
};

export default function Step8Review({ formData }: Props) {
  const sections = [
    { label: "Series Name", value: formData.seriesName || "Not set", step: 7 },
    { label: "Niche", value: niches[formData.niche] || "Not set", step: 1 },
    { label: "Language", value: formData.language.toUpperCase(), step: 2 },
    { label: "Voice", value: voices[formData.voice] || formData.voice, step: 2 },
    { label: "Music Tracks", value: `${formData.musicTracks?.length || 0} selected`, step: 3 },
    { label: "Art Style", value: artStyles[formData.artStyle] || "Not set", step: 4 },
    { label: "Caption Style", value: captionStyles[formData.captionStyle] || "Not set", step: 5 },
    { 
      label: "Platforms", 
      value: Object.entries(formData.platforms)
        .filter(([_, v]) => v)
        .map(([k]) => k.charAt(0).toUpperCase() + k.slice(1))
        .join(", ") || "None", 
      step: 6 
    },
    { label: "Video Duration", value: durations[formData.videoDuration] || "Not set", step: 7 },
    { label: "Post Frequency", value: frequencies[formData.postFrequency] || "Not set", step: 7 },
    { label: "Post Time", value: formData.postTime || "18:00", step: 7 },
  ];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Review Your Series</h2>
        <p className="text-muted-foreground">
          Make sure everything looks good before creating your series
        </p>
      </div>

      <div className="max-w-xl mx-auto">
        <div className="border rounded-xl overflow-hidden">
          {sections.map((section, index) => (
            <div
              key={section.label}
              className={`flex items-center justify-between p-4 ${
                index !== sections.length - 1 ? "border-b" : ""
              }`}
            >
              <div>
                <p className="text-sm text-muted-foreground">{section.label}</p>
                <p className="font-medium">{section.value}</p>
              </div>
              <Button variant="ghost" size="sm" className="gap-1">
                <Edit2 className="h-3 w-3" />
                Edit
              </Button>
            </div>
          ))}
        </div>

        <div className="mt-6 p-4 bg-primary/10 rounded-xl">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
              <Check className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <h3 className="font-semibold">Ready to create!</h3>
              <p className="text-sm text-muted-foreground">
                Your first video will start generating as soon as you create the series.
                You'll receive a notification when it's ready for review.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
