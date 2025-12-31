"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Plus, Video, Eye, Clock, Play, MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getEpisodes, getSeries, fetchAnalytics, updateEpisodeStats } from "@/lib/api";
import { LineStatChart, BarStatChart, PieStatChart } from "@/components/analytics-chart";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";

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
  topic?: string;
  status?: string;
  views?: number;
  likes?: number;
  shares?: number;
  niche?: string;
  created_at?: string;
};

const statusColors: Record<string, string> = {
  completed: "bg-green-500/20 text-green-500",
  queued: "bg-blue-500/20 text-blue-500",
  generating: "bg-yellow-500/20 text-yellow-500",
  failed: "bg-red-500/20 text-red-500",
  scheduled: "bg-blue-500/20 text-blue-500",
  published: "bg-green-500/20 text-green-500",
};

const formatNumber = (value: number | string) => {
  if (typeof value === "number") return value.toLocaleString();
  return value || "—";
};

const formatDate = (value?: string) => {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, { month: "short", day: "numeric" });
};

export default function DashboardPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showStatsForm, setShowStatsForm] = useState(false);
  const [statsPayload, setStatsPayload] = useState({ episodeId: "", views: "", likes: "", shares: "" });
  const { toast } = useToast();

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [seriesData, episodeData, analyticsData] = await Promise.all([
          getSeries(),
          getEpisodes(),
          fetchAnalytics("demo_user"),
        ]);
        setSeries(Array.isArray(seriesData) ? seriesData : []);
        setEpisodes(Array.isArray(episodeData) ? episodeData : []);
        setAnalytics(analyticsData);
      } catch (err) {
        console.error(err);
        setError("Unable to load live data from Supabase.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const stats = useMemo(() => {
    return [
      {
        label: "Total Views",
        value: formatNumber(analytics?.total_views || 0),
        icon: Eye,
        change: "Across all videos",
      },
      {
        label: "Total Videos",
        value: formatNumber(analytics?.total_videos || episodes.length),
        icon: Video,
        change: `${episodes.filter((e) => e.status === "completed").length} completed`,
      },
      {
        label: "Avg Views",
        value: formatNumber(analytics?.avg_views_per_video || 0),
        icon: Clock,
        change: "Per published video",
      },
      {
        label: "Engagement",
        value: analytics?.engagement_rate || "—",
        icon: Play,
        change: "Views vs likes",
      },
    ];
  }, [episodes, analytics]);

  const recentVideos = useMemo(() => {
    const sorted = [...episodes].sort((a, b) => {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bDate - aDate;
    });
    return sorted.slice(0, 3);
  }, [episodes]);

  const bestVideos = useMemo(() => {
    return [...episodes]
      .filter((e) => typeof e.views === "number")
      .sort((a, b) => (b.views || 0) - (a.views || 0))
      .slice(0, 3);
  }, [episodes]);

  const handleUpdateStats = async () => {
    if (!statsPayload.episodeId) {
      toast({ title: "Episode ID required", variant: "destructive" });
      return;
    }
    try {
      await updateEpisodeStats(statsPayload.episodeId, {
        views: Number(statsPayload.views) || 0,
        likes: Number(statsPayload.likes) || 0,
        shares: Number(statsPayload.shares) || 0,
      });
      toast({ title: "Stats updated" });
      setShowStatsForm(false);
    } catch (err) {
      toast({ title: "Failed to update", variant: "destructive" });
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Welcome back! 👋</h1>
          <p className="text-muted-foreground">
            Live metrics pulled from your Supabase data
          </p>
        </div>
        <Link href="/dashboard/series/create">
          <Button className="gap-2">
            <Plus className="h-5 w-5" />
            New Series
          </Button>
        </Link>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {loading ? "…" : stat.value}
              </div>
              <p className="text-xs text-muted-foreground">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <LineStatChart
          title="Views over time"
          data={(analytics?.performance_by_day || []).map((item: any) => ({ name: item.day, value: item.avg_views }))}
        />
        <BarStatChart
          title="Performance by niche"
          data={(analytics?.performance_by_niche || []).map((item: any) => ({ name: item.niche, value: item.avg_views }))}
        />
        <PieStatChart
          title="Content distribution"
          data={Object.entries(
            episodes.reduce<Record<string, number>>((acc, ep) => {
              const niche = ep.niche || "general";
              acc[niche] = (acc[niche] || 0) + 1;
              return acc;
            }, {})
          ).map(([name, value]) => ({ name, value }))}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Videos</CardTitle>
          </CardHeader>
          <CardContent>
            {loading && (
              <p className="text-sm text-muted-foreground">Loading videos…</p>
            )}
            {!loading && recentVideos.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No episodes yet. Create a series to get started.
              </p>
            )}
            <div className="space-y-4">
              {recentVideos.map((video) => {
                const seriesName =
                  series.find((s) => s.id === video.series_id)?.name || "Series";
                const badgeColor =
                  statusColors[video.status || ""] ||
                  "bg-muted text-muted-foreground";
                const viewsText =
                  typeof video.views === "number" && video.views > 0
                    ? `${video.views.toLocaleString()} views`
                    : formatDate(video.created_at);

                return (
                  <div
                    key={video.id}
                    className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted transition-colors"
                  >
                    <div className="w-20 h-12 bg-muted rounded-md flex items-center justify-center flex-shrink-0">
                      <Play className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">
                        {video.topic || "Untitled episode"}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {seriesName}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badgeColor}`}
                      >
                        {video.status || "unknown"}
                      </span>
                      <p className="text-xs text-muted-foreground mt-1">
                        {viewsText}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Best performing</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => setShowStatsForm(true)}>
              Update stats
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {bestVideos.length === 0 && (
                <p className="text-sm text-muted-foreground">No videos yet. Generate a series to start tracking.</p>
              )}
              {bestVideos.map((video) => (
                <div key={video.id} className="rounded-md border p-3 flex items-center justify-between">
                  <div>
                    <p className="font-medium">{video.topic || "Untitled episode"}</p>
                    <p className="text-xs text-muted-foreground">Views: {formatNumber(video.views || 0)}</p>
                  </div>
                  <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                </div>
              ))}
            </div>

            {showStatsForm && (
              <div className="mt-4 space-y-2 rounded-md border p-3">
                <Input placeholder="Episode ID" value={statsPayload.episodeId} onChange={(e) => setStatsPayload({ ...statsPayload, episodeId: e.target.value })} />
                <div className="grid gap-2 grid-cols-3">
                  <Input placeholder="Views" value={statsPayload.views} onChange={(e) => setStatsPayload({ ...statsPayload, views: e.target.value })} />
                  <Input placeholder="Likes" value={statsPayload.likes} onChange={(e) => setStatsPayload({ ...statsPayload, likes: e.target.value })} />
                  <Input placeholder="Shares" value={statsPayload.shares} onChange={(e) => setStatsPayload({ ...statsPayload, shares: e.target.value })} />
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleUpdateStats}>Save</Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowStatsForm(false)}>Cancel</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="rounded-lg border p-4">
        <h3 className="text-lg font-semibold mb-2">AI recommendations</h3>
        <ul className="space-y-2 text-sm text-muted-foreground">
          {(analytics?.recommendations || []).map((rec: string) => (
            <li key={rec}>• {rec}</li>
          ))}
          {(!analytics?.recommendations || analytics.recommendations.length === 0) && (
            <li>Waiting for data to generate recommendations.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
