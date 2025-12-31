"use client";

import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";
import { artStyles } from "@/data/media";

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step4ArtStyle({ formData, updateFormData }: Props) {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Art Style</h2>
        <p className="text-muted-foreground">
          Choose the visual style for your video frames
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {artStyles.map((style) => (
          <button
            key={style.id}
            onClick={() => updateFormData({ artStyle: style.id })}
            className={cn(
              "relative flex flex-col items-center p-4 rounded-xl border-2 transition-all hover:border-primary/50 group",
              formData.artStyle === style.id
                ? "border-primary bg-primary/10"
                : "border-border"
            )}
          >
            {formData.artStyle === style.id && (
              <div className="absolute top-2 right-2 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                <Check className="h-3 w-3 text-primary-foreground" />
              </div>
            )}
            
            <div className="w-full aspect-[9/16] bg-muted rounded-lg mb-3 flex items-center justify-center text-4xl overflow-hidden">
              {style.previewUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={style.previewUrl}
                  alt={style.name}
                  className="h-full w-full object-cover"
                  onError={(e) => {
                    // fallback to emoji if image missing
                    const target = e.target as HTMLImageElement;
                    target.style.display = "none";
                  }}
                />
              ) : null}
              {style.previewEmoji}
            </div>
            
            <span className="font-medium text-sm">{style.name}</span>
            <span className="text-xs text-muted-foreground text-center mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {style.description}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
