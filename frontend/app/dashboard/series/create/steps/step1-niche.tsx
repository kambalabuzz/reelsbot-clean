"use client";

import { useState } from "react";
import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { 
  Skull, Ghost, History, Search, Brain, Rocket, 
  TrendingUp as TrendingUpIcon, DollarSign, Cpu, Sparkles
} from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ViralScore } from "@/components/viral-score";
import { analyzeViralScore } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

const niches = [
  { id: "true_crime", name: "True Crime", icon: Skull, description: "Unsolved cases and mysteries" },
  { id: "horror", name: "Horror", icon: Ghost, description: "Creepy and scary stories" },
  { id: "history", name: "History", icon: History, description: "Fascinating historical events" },
  { id: "mystery", name: "Mystery", icon: Search, description: "Puzzles and strange occurrences" },
  { id: "conspiracy", name: "Conspiracy", icon: Brain, description: "Alternative theories" },
  { id: "paranormal", name: "Paranormal", icon: Sparkles, description: "Ghosts, UFOs, supernatural" },
  { id: "sci_fi", name: "Sci-Fi", icon: Rocket, description: "Future and space stories" },
  { id: "motivation", name: "Motivation", icon: TrendingUpIcon, description: "Success and inspiration" },
  { id: "finance", name: "Finance", icon: DollarSign, description: "Money and investing tips" },
  { id: "tech", name: "Tech", icon: Cpu, description: "Technology and AI" },
];

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step1Niche({ formData, updateFormData }: Props) {
  const { toast } = useToast();
  const [script, setScript] = useState("");
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!script.trim()) {
      toast({ title: "Add a script or topic", description: "Paste a rough script to predict virality." });
      return;
    }
    setLoading(true);
    try {
      const result = await analyzeViralScore(script, formData.niche);
      setAnalysis(result);
      toast({ title: "Viral score ready", description: "Use the insights to tweak your script." });
    } catch (err) {
      toast({ title: "Analysis failed", description: "Try again in a moment.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = (optimized: string) => {
    setScript(optimized);
    toast({ title: "Optimized script applied" });
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Choose Your Niche</h2>
        <p className="text-muted-foreground">
          Select the content category for your video series
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {niches.map((niche) => (
          <button
            key={niche.id}
            onClick={() => updateFormData({ niche: niche.id })}
            className={cn(
              "flex flex-col items-center p-4 rounded-xl border-2 transition-all hover:border-primary/50",
              formData.niche === niche.id
                ? "border-primary bg-primary/10"
                : "border-border hover:bg-muted/50"
            )}
          >
            <div
              className={cn(
                "w-12 h-12 rounded-full flex items-center justify-center mb-3",
                formData.niche === niche.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              )}
            >
              <niche.icon className="h-6 w-6" />
            </div>
            <span className="font-medium text-sm">{niche.name}</span>
            <span className="text-xs text-muted-foreground text-center mt-1">
              {niche.description}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-8 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Test your script</h3>
          <Button size="sm" variant="outline" onClick={handleAnalyze} disabled={loading}>
            {loading ? "Analyzing..." : "Predict viral score"}
          </Button>
        </div>
        <Textarea
          placeholder="Paste a hook or short script to see its viral potential"
          value={script}
          onChange={(e) => setScript(e.target.value)}
          rows={4}
        />
        <ViralScore
          score={analysis?.score}
          breakdown={analysis?.breakdown}
          strengths={analysis?.strengths}
          improvements={analysis?.improvements}
          optimizedScript={analysis?.optimized_script}
          loading={loading}
          onOptimize={handleOptimize}
        />
      </div>
    </div>
  );
}
