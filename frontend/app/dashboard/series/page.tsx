"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Plus, RefreshCw, Clock, Video, Play, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getEpisodes, getSeries, deleteSeries } from "@/lib/api";

type Series = {
  id: string;
  name?: string;
  niche?: string;
  post_time?: string;
  post_frequency?: string;
  created_at?: string;
};

type Episode = {
  id: string;
  series_id?: string;
  status?: string;
  created_at?: string;
};

const formatDate = (value?: string) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
};

export default function SeriesPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const loadSeries = async () => {
    setLoading(true);
    setError(null);
    try {
      const [seriesData, episodeData] = await Promise.all([
        getSeries(),
        getEpisodes(),
      ]);
      setSeries(Array.isArray(seriesData) ? seriesData : []);
      setEpisodes(Array.isArray(episodeData) ? episodeData : []);
    } catch (err) {
      console.error(err);
      setError("Unable to load series from Supabase.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSeries = async (seriesId: string, seriesName: string) => {
    const episodeCount = seriesEpisodeCounts[seriesId] || 0;
    const confirmMessage = episodeCount > 0
      ? `Delete "${seriesName}"?\n\nThis will permanently delete the series and all ${episodeCount} episode(s). This action cannot be undone.`
      : `Delete "${seriesName}"?\n\nThis action cannot be undone.`;

    if (!confirm(confirmMessage)) {
      return;
    }

    setDeleting(seriesId);
    setError(null);

    try {
      await deleteSeries(seriesId);
      // Remove from local state immediately
      setSeries(series.filter(s => s.id !== seriesId));
      setEpisodes(episodes.filter(ep => ep.series_id !== seriesId));
    } catch (err) {
      console.error("Delete failed:", err);
      setError(`Failed to delete series: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => {
    loadSeries();
  }, []);

  const seriesEpisodeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    episodes.forEach((ep) => {
      if (!ep.series_id) return;
      counts[ep.series_id] = (counts[ep.series_id] || 0) + 1;
    });
    return counts;
  }, [episodes]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Series</h1>
          <p className="text-muted-foreground">
            Live list pulled directly from Supabase
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadSeries} disabled={loading}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Link href="/dashboard/series/create">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              New Series
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading && (
        <p className="text-sm text-muted-foreground">Loading series…</p>
      )}

      {!loading && series.length === 0 && (
        <Card className="p-6 text-center">
          <h2 className="text-xl font-semibold mb-2">No series yet</h2>
          <p className="text-muted-foreground mb-4">
            Create your first series to start generating episodes.
          </p>
          <Link href="/dashboard/series/create">
            <Button className="gap-2">
              <Plus className="h-4 w-4" />
              Create Series
            </Button>
          </Link>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {series.map((s) => {
          const episodeCount = seriesEpisodeCounts[s.id] || 0;
          const schedule = s.post_time
            ? `${s.post_frequency || "daily"} at ${s.post_time}`
            : "No schedule set";

          const isDeleting = deleting === s.id;

          return (
            <Card key={s.id} className="border">
              <CardHeader className="flex flex-row items-start justify-between gap-2">
                <div>
                  <CardTitle>{s.name || "Untitled series"}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {s.niche || "No niche provided"}
                  </p>
                </div>
                <div className="text-right text-xs text-muted-foreground">
                  Created {formatDate(s.created_at)}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3 text-sm">
                  <div className="inline-flex items-center gap-2 rounded-md bg-muted px-3 py-2">
                    <Video className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{episodeCount}</span>
                    <span className="text-muted-foreground">episodes</span>
                  </div>
                  <div className="inline-flex items-center gap-2 rounded-md bg-muted px-3 py-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span>{schedule}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Play className="h-4 w-4" />
                    {episodeCount > 0
                      ? "Episodes generated from this series"
                      : "No episodes yet"}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteSeries(s.id, s.name || "Untitled series")}
                    disabled={isDeleting}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="h-4 w-4" />
                    {isDeleting ? "Deleting..." : "Delete"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
