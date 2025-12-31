"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { generateSeriesPlan } from "@/lib/api";
import { SeriesTimeline } from "@/components/series-timeline";
import { useToast } from "@/components/ui/use-toast";

type PlanResponse = {
  series_name: string;
  description: string;
  episodes: any[];
  posting_schedule?: string[];
};

export default function SeriesPlanPage() {
  const [topic, setTopic] = useState("");
  const [niche, setNiche] = useState("horror");
  const [numEpisodes, setNumEpisodes] = useState(7);
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const { toast } = useToast();

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast({ title: "Add a topic", description: "Pick something to plan around." });
      return;
    }
    setLoading(true);
    try {
      const data = await generateSeriesPlan({ topic, niche, num_episodes: numEpisodes });
      setPlan(data);
      toast({ title: "Series plan ready" });
    } catch (err) {
      toast({ title: "Unable to generate", description: "Try again shortly.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleReorder = (episodes: any[]) => {
    setPlan((prev) => prev ? { ...prev, episodes } : prev);
  };

  const handleEdit = (episode: any) => {
    const title = window.prompt("Episode title", episode.title) || episode.title;
    const description = window.prompt("Description", episode.description || "") || episode.description;
    setPlan((prev) => {
      if (!prev) return prev;
      const next = prev.episodes.map((ep) => ep.episode_number === episode.episode_number ? { ...ep, title, description } : ep);
      return { ...prev, episodes: next };
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Smart Series Generator</h1>
        <p className="text-muted-foreground">Map a connected series with cliffhangers in seconds.</p>
      </div>

      <div className="grid gap-4 rounded-lg border p-4 md:grid-cols-3">
        <div className="space-y-2">
          <label className="text-sm font-medium">Topic</label>
          <Input placeholder="Greek Gods, AI myths, ghost towns..." value={topic} onChange={(e) => setTopic(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Episodes ({numEpisodes})</label>
          <input type="range" min={3} max={30} value={numEpisodes} onChange={(e) => setNumEpisodes(Number(e.target.value))} className="w-full" />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Niche</label>
          <Select value={niche} onValueChange={setNiche}>
            <SelectTrigger>
              <SelectValue placeholder="Choose niche" />
            </SelectTrigger>
            <SelectContent>
              {["horror", "finance", "history", "tech", "motivation", "mystery"].map((n) => (
                <SelectItem value={n} key={n}>{n}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Button onClick={handleGenerate} disabled={loading} className="gap-2">
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {loading ? "Generating..." : "Generate series plan"}
      </Button>

      {loading && <div className="h-40 animate-pulse rounded-lg border bg-muted/50" />}

      {plan && (
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold">{plan.series_name}</h2>
            <p className="text-muted-foreground">{plan.description}</p>
            {plan.posting_schedule && (
              <p className="text-sm text-muted-foreground mt-1">Schedule: {plan.posting_schedule.join(", ")}</p>
            )}
          </div>
          <SeriesTimeline episodes={plan.episodes} onReorder={handleReorder} onEdit={handleEdit} onGenerateAll={() => toast({ title: "Queued", description: "Episodes queued for creation." })} />
        </div>
      )}
    </div>
  );
}
