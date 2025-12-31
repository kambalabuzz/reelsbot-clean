"use client";

import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

const captionStyles = [
  { 
    id: "red_highlight", 
    name: "Red Highlight",
    preview: { word1: "NOTEBOOK", word2: "HIDDEN", highlight: "red" }
  },
  { 
    id: "karaoke", 
    name: "Karaoke",
    preview: { word1: "NOTEBOOK", word2: "HIDDEN", highlight: "purple-box" }
  },
  { 
    id: "beast", 
    name: "Beast",
    preview: { word1: "NOTEBOOK", word2: "", highlight: "yellow-italic" }
  },
  { 
    id: "bold_stroke", 
    name: "Bold Stroke",
    preview: { word1: "NOTEBOOK", word2: "", highlight: "white-stroke" }
  },
  { 
    id: "sleek", 
    name: "Sleek",
    preview: { word1: "A", word2: "DUSTY", highlight: "gray-pop" }
  },
  { 
    id: "majestic", 
    name: "Majestic",
    preview: { word1: "NOTEBOOK", word2: "HIDDEN", highlight: "gold" }
  },
  { 
    id: "elegant", 
    name: "Elegant",
    preview: { word1: "NOTEBOOK", word2: "", highlight: "serif" }
  },
  { 
    id: "neon", 
    name: "Neon",
    preview: { word1: "NOTEBOOK", word2: "", highlight: "neon" }
  },
  { 
    id: "fire", 
    name: "Fire",
    preview: { word1: "NOTEBOOK", word2: "", highlight: "orange" }
  },
  { 
    id: "hormozi", 
    name: "Hormozi",
    preview: { word1: "BIG", word2: "TEXT", highlight: "yellow-big" }
  },
];

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step5Captions({ formData, updateFormData }: Props) {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Caption Style</h2>
        <p className="text-muted-foreground">
          Choose how captions will appear in your videos
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {captionStyles.map((style) => (
          <button
            key={style.id}
            onClick={() => updateFormData({ captionStyle: style.id })}
            className={cn(
              "relative flex flex-col items-center rounded-xl border-2 transition-all hover:border-primary/50 overflow-hidden",
              formData.captionStyle === style.id
                ? "border-primary"
                : "border-border"
            )}
          >
            {formData.captionStyle === style.id && (
              <div className="absolute top-2 right-2 z-10 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
                <Check className="h-3 w-3 text-primary-foreground" />
              </div>
            )}
            
            {/* Preview */}
            <div className="w-full aspect-video bg-zinc-800 flex flex-col items-center justify-center p-4">
              <CaptionPreview style={style.id} />
            </div>
            
            <div className="p-3 w-full bg-card">
              <span className="font-medium text-sm">{style.name}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

function CaptionPreview({ style }: { style: string }) {
  const styles: Record<string, React.ReactNode> = {
    red_highlight: (
      <div className="text-center">
        <span className="text-red-500 font-black text-lg drop-shadow-[0_0_10px_rgba(255,0,0,0.5)]">NOTEBOOK</span>
        <br />
        <span className="text-white font-black text-lg">HIDDEN</span>
      </div>
    ),
    karaoke: (
      <div className="text-center">
        <span className="bg-purple-600 text-white font-black text-lg px-2">NOTEBOOK</span>
        <br />
        <span className="text-white font-black text-lg">HIDDEN</span>
      </div>
    ),
    beast: (
      <span className="text-yellow-400 font-black text-xl italic drop-shadow-[2px_2px_0_#000]">NOTEBOOK</span>
    ),
    bold_stroke: (
      <span className="text-white font-black text-xl" style={{ WebkitTextStroke: "2px black" }}>NOTEBOOK</span>
    ),
    sleek: (
      <div className="text-center">
        <span className="text-gray-400 font-bold text-sm">A</span>
        <br />
        <span className="text-white font-bold text-lg">DUSTY</span>
      </div>
    ),
    majestic: (
      <div className="text-center">
        <span className="text-amber-300 font-semibold text-lg">NOTEBOOK</span>
        <br />
        <span className="text-white font-semibold text-lg">HIDDEN</span>
      </div>
    ),
    elegant: (
      <span className="text-white font-serif text-lg italic">NOTEBOOK</span>
    ),
    neon: (
      <span className="text-cyan-400 font-black text-lg drop-shadow-[0_0_15px_rgba(0,255,255,0.8)]">NOTEBOOK</span>
    ),
    fire: (
      <span className="text-orange-500 font-black text-lg drop-shadow-[0_0_10px_rgba(255,100,0,0.5)]">NOTEBOOK</span>
    ),
    hormozi: (
      <div className="text-center">
        <span className="text-yellow-400 font-black text-2xl">BIG</span>
        <br />
        <span className="text-white font-black text-2xl">TEXT</span>
      </div>
    ),
  };

  return styles[style] || <span className="text-white font-bold">PREVIEW</span>;
}
