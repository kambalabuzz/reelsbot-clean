"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Play, Search, Loader2, AlertCircle, Trash2, Film } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useAssembly } from "@/contexts/AssemblyContext";
import { VideoGridSkeleton } from "@/components/VideoCardSkeleton";

type VideoItem = {
  id?: string;
  video_id: string;
  topic: string;
  status: string;
  video_url?: string | null;
  image_urls?: string[];
  created_at?: string;
  updated_at?: string;
  assembly_reason?: string | null;
  assembly_progress?: number | null;
  assembly_stage?: string | null;
  assembly_eta_seconds?: number | null;
  assembly_log?: string | null;
};

const statusColors: Record<string, string> = {
  completed: "bg-green-500/20 text-green-400",
  assets_ready: "bg-yellow-500/20 text-yellow-400",
  assembly_failed: "bg-red-500/20 text-red-400",
  assembly_canceled: "bg-gray-500/20 text-gray-200",
};

const PLACEHOLDER = "https://via.placeholder.com/1080x1920/1a1a2e/ffffff?text=Scene";
const ASSEMBLY_STALE_MS = 30 * 60 * 1000;
const LOCAL_GRACE_MS = 2 * 60 * 1000;

const formatStatus = (status: string) => {
  if (!status) return "Unknown";
  return status.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
};

const formatDuration = (totalSeconds?: number | null) => {
  if (!totalSeconds || totalSeconds <= 0) return null;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  if (minutes <= 0) return `${seconds}s`;
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
};

const getLastUpdated = (video: VideoItem) => {
  const value = video.updated_at || video.created_at;
  return value ? new Date(value) : null;
};

export default function VideosPage() {
  const { getProgress, activeAssemblies, completeAssembly } = useAssembly();
  const [items, setItems] = useState<VideoItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const apiBase = useMemo(
    () => process.env.NEXT_PUBLIC_API_URL || (typeof window !== "undefined" ? window.location.origin : ""),
    []
  );

  const filtered = useMemo(() => {
    return items.filter((v) => v.topic.toLowerCase().includes(search.toLowerCase()));
  }, [items, search]);

  const loadVideos = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      if (!apiBase) throw new Error("API URL not configured");
      const res = await fetch(`${apiBase}/api/videos`);
      if (!res.ok) throw new Error("Failed to load videos");
      const data = await res.json();
      setItems(data || []);

      const statusById = new Map(
        (data || []).map((video: VideoItem) => [video.video_id, video.status])
      );

      activeAssemblies.forEach((assembly, videoId) => {
        const status = statusById.get(videoId);
        if (status === "assembling") return;
        if (status === "assembly_failed" || status === "assembly_canceled" || status === "completed") {
          completeAssembly(videoId);
          return;
        }

        const withinGrace = Date.now() - assembly.startedAt <= LOCAL_GRACE_MS;
        if (!withinGrace) {
          completeAssembly(videoId);
        }
      });
    } catch (e: any) {
      setError(e.message || "Failed to load videos");
    } finally {
      setLoading(false);
    }
  }, [apiBase, activeAssemblies, completeAssembly]);

  const deleteVideo = async (videoId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this video?")) return;

    setDeleting(videoId);
    try {
      if (!apiBase) throw new Error("API URL not configured");
      const res = await fetch(`${apiBase}/api/video/${videoId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete video");
      toast.success("Video deleted");
      await loadVideos();
    } catch (e: any) {
      toast.error(e.message || "Failed to delete video");
    } finally {
      setDeleting(null);
    }
  };

  useEffect(() => {
    void loadVideos();
  }, [loadVideos]);

  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null;

    const startPolling = () => {
      if (intervalId) return;
      intervalId = setInterval(() => {
        void loadVideos();
      }, 10000);
    };

    const stopPolling = () => {
      if (!intervalId) return;
      clearInterval(intervalId);
      intervalId = null;
    };

    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        void loadVideos();
        startPolling();
      } else {
        stopPolling();
      }
    };

    startPolling();
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  }, [loadVideos]);

  const activeAssemblyCount = useMemo(() => {
    return items.filter((video) => {
      if (video.status !== "assembling") return false;
      const lastUpdated = getLastUpdated(video);
      return !!lastUpdated && Date.now() - lastUpdated.getTime() <= ASSEMBLY_STALE_MS;
    }).length;
  }, [items]);

  return (
    <div className="space-y-6">
      {/* Active Assemblies Banner */}
      {activeAssemblyCount > 0 && (
        <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 border border-purple-500/50 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Film className="w-5 h-5 text-purple-400 animate-pulse" />
            <div className="flex-1">
              <h3 className="font-semibold text-white">Videos Being Assembled</h3>
              <p className="text-sm text-purple-200">
                {activeAssemblyCount} video{activeAssemblyCount > 1 ? "s" : ""} currently cooking...
              </p>
            </div>
            <div className="text-xs text-purple-300">Click on a video to view progress</div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Videos</h1>
          <p className="text-muted-foreground">View and download your generated videos</p>
        </div>
      </div>

      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search videos..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full h-10 pl-10 pr-4 rounded-lg border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" /> {error}
        </div>
      )}

      {loading ? (
        <VideoGridSkeleton count={6} />
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((video) => {
          const localAssembly = activeAssemblies.get(video.video_id);
          const isLocalActive = !!localAssembly && Date.now() - localAssembly.startedAt <= ASSEMBLY_STALE_MS;
          const withinGrace = !!localAssembly && Date.now() - localAssembly.startedAt <= LOCAL_GRACE_MS;
          const lastUpdated = getLastUpdated(video);
          const hasTimestamp = !!lastUpdated;
          const isStaleAssembly =
            video.status === "assembling" &&
            !withinGrace &&
            (!hasTimestamp || Date.now() - lastUpdated.getTime() > ASSEMBLY_STALE_MS);
          const blocksLocalAssembly =
            video.status === "completed" ||
            video.status === "assembly_failed" ||
            video.status === "assembly_canceled";
          const isActiveAssembly =
            !isStaleAssembly && (video.status === "assembling" || (isLocalActive && !blocksLocalAssembly));
          const localProgress = isLocalActive ? getProgress(video.video_id) : 0;
          const serverProgress = typeof video.assembly_progress === "number" ? video.assembly_progress : null;
          const displayProgress = serverProgress ?? localProgress;
          const etaLabel = formatDuration(video.assembly_eta_seconds);
          const statusLabel = isStaleAssembly ? "Stalled" : isActiveAssembly ? "Assembling" : formatStatus(video.status);
          const statusClass = isStaleAssembly
            ? "bg-orange-500/20 text-orange-300"
            : video.status === "assembly_canceled"
              ? "bg-gray-600/30 text-gray-200"
              : isActiveAssembly
                ? "bg-purple-500/80 text-white animate-pulse"
                : statusColors[video.status] || "bg-gray-700 text-gray-200";
          const statusDetail = isStaleAssembly
            ? `Assembly stalled${lastUpdated ? ` since ${lastUpdated.toLocaleString()}` : ""}`
            : video.status === "assembly_failed"
              ? video.assembly_reason
                ? `Assembly failed: ${video.assembly_reason}`
                : "Assembly failed. Open to retry."
              : video.status === "assembly_canceled"
                ? "Assembly canceled."
                : video.status === "assembling"
                  ? serverProgress !== null
                    ? `Assembly ${Math.round(serverProgress)}%${etaLabel ? ` • ETA ${etaLabel}` : ""}`
                    : "Assembly in progress..."
                  : video.video_url
                    ? "Video ready"
                    : "Assets ready";

          return (
            <div key={video.video_id} className="relative group">
              <Link
                href={`/dashboard/videos/${video.video_id}`}
                className={cn(
                  "block rounded-lg border border-border bg-card hover:border-primary transition-colors overflow-hidden",
                  isActiveAssembly && "ring-2 ring-purple-500/50 border-purple-500"
                )}
              >
                <div className="relative aspect-[9/16] bg-muted">
                  {video.image_urls?.[0] ? (
                    <img
                      src={video.image_urls[0]}
                      alt={video.topic}
                      className="absolute inset-0 h-full w-full object-cover"
                      loading="lazy"
                      decoding="async"
                      onError={(e) => {
                        const target = e.currentTarget;
                        target.onerror = null;
                        target.src = PLACEHOLDER;
                      }}
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <Play className="h-10 w-10 text-muted-foreground" />
                    </div>
                  )}

                  {/* Assembly Overlay */}
                  {isActiveAssembly && !isStaleAssembly && (
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center gap-3">
                      <div className="text-white text-sm font-semibold">Assembling...</div>
                      {video.assembly_stage && (
                        <div className="text-xs text-white/80">{video.assembly_stage}</div>
                      )}
                      <div className="w-3/4 h-2 bg-black/50 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-yellow-500 transition-all duration-500"
                          style={{ width: `${displayProgress}%` }}
                        />
                      </div>
                      <div className="text-purple-200 text-xs">{Math.round(displayProgress)}%</div>
                    </div>
                  )}

                  <div className="absolute top-2 left-2">
                    <span
                      className={cn(
                        "px-2 py-1 rounded-full text-xs font-medium",
                        statusClass
                      )}
                    >
                      {statusLabel}
                    </span>
                  </div>
                </div>
              <div className="p-4">
                <div className="font-semibold truncate">{video.topic}</div>
                <div className="text-xs text-muted-foreground">
                  {statusDetail}
                </div>
                <div className="text-xs text-muted-foreground">
                  {lastUpdated ? `Updated ${lastUpdated.toLocaleString()}` : ""}
                </div>
              </div>
              </Link>
              <Button
                variant="destructive"
                size="icon"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => deleteVideo(video.video_id, e)}
                disabled={deleting === video.video_id || isActiveAssembly}
              >
                {deleting === video.video_id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          );
        })}
        </div>
      )}

      {filtered.length === 0 && !loading && (
        <div className="text-center py-12 text-muted-foreground">No videos found</div>
      )}
    </div>
  );
}
