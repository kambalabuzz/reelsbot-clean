"use client";

import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { TrendCard } from "@/components/trend-card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { fetchTrends } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import Link from "next/link";

const niches = ["horror", "finance", "tech", "fitness", "history", "motivation"];

export default function TrendsPage() {
  const [niche, setNiche] = useState("horror");
  const [loading, setLoading] = useState(false);
  const [trends, setTrends] = useState<any>(null);
  const { toast } = useToast();

  const load = async (selected: string) => {
    setLoading(true);
    try {
      const data = await fetchTrends(selected);
      setTrends(data);
      if (data?.source) {
        toast({ title: `Trends loaded from ${data.source.replace(/_/g, " ")}` });
      }
    } catch (err) {
      toast({ title: "Unable to load trends", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(niche);
  }, [niche]);

  const handleUseTopic = (topic: string) => {
    toast({ title: "Topic applied", description: "Redirecting to series planner." });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">Trend Radar</h1>
          <p className="text-muted-foreground">Discover rising topics before they peak.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={niche} onValueChange={setNiche}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select niche" />
            </SelectTrigger>
            <SelectContent>
              {niches.map((n) => (
                <SelectItem key={n} value={n}>{n}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={() => load(niche)} disabled={loading} className="gap-2">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {loading &&
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-40 rounded-lg border animate-pulse bg-muted/50" />
          ))}
        {!loading && trends?.trending_topics?.map((topic: any) => (
          <TrendCard
            key={topic.topic}
            topic={topic.topic}
            growth={topic.growth}
            searchVolume={topic.search_volume}
            history={topic.history}
            onUse={handleUseTopic}
          />
        ))}
      </div>

      {trends?.suggested_titles && (
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Suggested titles</h2>
              <p className="text-sm text-muted-foreground">Crafted from current signals.</p>
            </div>
            <Link href="/dashboard/series/plan">
              <Button variant="outline">Open series planner</Button>
            </Link>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {trends.suggested_titles.map((title: string) => (
              <div key={title} className="rounded-md border px-3 py-2 text-sm">{title}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
