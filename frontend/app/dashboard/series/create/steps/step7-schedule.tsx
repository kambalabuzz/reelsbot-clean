"use client";

import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { Info } from "lucide-react";

const durations = [
  { id: "short", name: "15-30 seconds", description: "Quick, punchy content" },
  { id: "medium", name: "30-45 seconds", description: "Standard TikTok length" },
  { id: "long", name: "45-60 seconds", description: "More detailed stories" },
  { id: "extra_long", name: "60-90 seconds", description: "In-depth content" },
];

const frequencies = [
  { id: "three_per_week", name: "3x per week", description: "Mon, Wed, Fri" },
  { id: "daily", name: "Every day", description: "Consistent daily posts" },
  { id: "twice_daily", name: "2x per day", description: "Maximum growth" },
];

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step7Schedule({ formData, updateFormData }: Props) {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Series Details</h2>
        <p className="text-muted-foreground">
          Finalize your series details and posting schedule
        </p>
      </div>

      <div className="max-w-xl mx-auto space-y-8">
        {/* Series Name */}
        <div>
          <label className="block text-sm font-medium mb-2">Series Name</label>
          <input
            type="text"
            value={formData.seriesName}
            onChange={(e) => updateFormData({ seriesName: e.target.value })}
            placeholder="e.g., True Crime Stories"
            className="w-full h-12 px-4 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        {/* Video Duration */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <label className="text-sm font-medium">Video Duration</label>
            <Info className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            {durations.map((duration) => (
              <button
                key={duration.id}
                onClick={() => updateFormData({ videoDuration: duration.id })}
                className={cn(
                  "p-4 rounded-lg border-2 text-left transition-all",
                  formData.videoDuration === duration.id
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                )}
              >
                <span className="font-medium">{duration.name}</span>
                <p className="text-sm text-muted-foreground">{duration.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Schedule */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Schedule</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Set when you want your videos to be published.
          </p>

          {/* Frequency */}
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">Post Frequency</label>
            <div className="grid grid-cols-3 gap-3">
              {frequencies.map((freq) => (
                <button
                  key={freq.id}
                  onClick={() => updateFormData({ postFrequency: freq.id })}
                  className={cn(
                    "p-4 rounded-lg border-2 text-center transition-all",
                    formData.postFrequency === freq.id
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  <span className="font-medium text-sm">{freq.name}</span>
                  <p className="text-xs text-muted-foreground mt-1">{freq.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Time */}
          <div>
            <label className="block text-sm font-medium mb-2">Publish time:</label>
            <div className="flex items-center gap-4">
              <input
                type="time"
                value={formData.postTime}
                onChange={(e) => updateFormData({ postTime: e.target.value })}
                className="h-12 px-4 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <span className="text-sm text-muted-foreground">(Your local time)</span>
            </div>
          </div>
        </div>

        {/* Note */}
        <div className="bg-muted/50 rounded-lg p-4 flex gap-3">
          <Info className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
          <p className="text-sm text-muted-foreground">
            <strong>Note:</strong> Videos will be generated 6 hours before the scheduled 
            publish time so you have time to review them.
          </p>
        </div>
      </div>
    </div>
  );
}
