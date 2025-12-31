"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Download, Loader2, Share2, PlayCircle, Image as ImageIcon, RefreshCw } from "lucide-react";
import JSZip from "jszip";
import { saveAs } from "file-saver";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { useAssembly } from "@/contexts/AssemblyContext";
import { getApiBase } from "@/lib/api";

const PLACEHOLDER = "https://via.placeholder.com/1080x1920/1a1a2e/ffffff?text=Scene";
const ASSEMBLY_STALE_MS = 30 * 60 * 1000;
const RETRY_GRACE_MS = 10 * 1000;

const formatStatus = (status?: string) => {
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

export default function VideoDetailPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const { isAssembling, getProgress, startAssembly, updateProgress, completeAssembly } = useAssembly();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const retryStartedAtRef = useRef<number | null>(null);
  const apiBase = useMemo(() => getApiBase(), []);

  const assembling = isAssembling(videoId);
  const assemblyProgress = getProgress(videoId);
  const retryGraceActive =
    retrying || (retryStartedAtRef.current !== null && Date.now() - retryStartedAtRef.current < RETRY_GRACE_MS);
  const localAssemblyActive = assembling || retryGraceActive;
  const serverProgress = typeof data?.assembly_progress === "number" ? data.assembly_progress : null;
  const displayProgress = serverProgress ?? (localAssemblyActive ? assemblyProgress : 0);
  const stageLabel = data?.assembly_stage as string | undefined;
  const etaLabel = formatDuration(data?.assembly_eta_seconds);
  const logLine = data?.assembly_log as string | undefined;

  const hasAssets = useMemo(() => Array.isArray(data?.image_urls) && data.image_urls.length > 0, [data]);
  const lastUpdated = useMemo(() => {
    const value = data?.updated_at || data?.created_at;
    return value ? new Date(value) : null;
  }, [data]);
  const hasTimestamp = !!lastUpdated;
  const isStaleAssembly =
    data?.status === "assembling" &&
    !assembling &&
    (!hasTimestamp || Date.now() - lastUpdated.getTime() > ASSEMBLY_STALE_MS);
  const showServerAssembly = data?.status === "assembling" && !assembling && !isStaleAssembly;
  const blocksAssemblyCard =
    data?.status === "completed" ||
    data?.status === "assembly_failed" ||
    (data?.status === "assembly_canceled" && !localAssemblyActive);
  const showAssemblyCard =
    !blocksAssemblyCard && !isStaleAssembly && (localAssemblyActive || showServerAssembly);

  const load = async () => {
    setLoading(true);
    try {
      if (!apiBase) throw new Error("API URL not configured");
      const res = await fetch(`${apiBase}/api/video/${videoId}`);
      if (!res.ok) throw new Error("Failed to load video");
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error(e);
      toast.error("Failed to load video");
    } finally {
      setLoading(false);
    }
  };

  // Real-time polling for assembly status
  const beginPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${apiBase}/api/video/${videoId}`);
        if (res.ok) {
          const videoData = await res.json();
          const withinRetryGrace =
            retryStartedAtRef.current !== null &&
            Date.now() - retryStartedAtRef.current < RETRY_GRACE_MS;

          if (videoData.status === "assembly_canceled" && withinRetryGrace) {
            return;
          }

          if (videoData.status === "assembling" && retrying) {
            setRetrying(false);
            retryStartedAtRef.current = null;
          }

          // Check if assembly completed
          if (videoData.status === "completed" && videoData.video_url) {
            clearInterval(interval);
            pollIntervalRef.current = null;
            updateProgress(videoId, 100);
            setTimeout(() => {
              setData(videoData);
              completeAssembly(videoId);
              setRetrying(false);
              retryStartedAtRef.current = null;
              toast.success("Video assembled!");
            }, 500);
          } else if (videoData.status === "assembly_failed") {
            clearInterval(interval);
            pollIntervalRef.current = null;
            completeAssembly(videoId);
            setData(videoData);
            setRetrying(false);
            retryStartedAtRef.current = null;
            toast.error("Assembly failed");
          } else if (videoData.status === "assembly_canceled") {
            clearInterval(interval);
            pollIntervalRef.current = null;
            completeAssembly(videoId);
            setData(videoData);
            setRetrying(false);
            retryStartedAtRef.current = null;
            toast.info("Assembly canceled");
          } else if (videoData.status === "assembling" || videoData.status === "assets_ready") {
            // Still processing - increment progress gradually
            updateProgress(videoId, Math.min(getProgress(videoId) + 3, 95));
          } else {
            // Unknown status - keep polling but don't increment
            console.log(`Unknown status: ${videoData.status}`);
          }
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 3000); // Poll every 3 seconds

    pollIntervalRef.current = interval;
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  useEffect(() => {
    void load();
    return () => {
      stopPolling();
    };
  }, [videoId]);

  useEffect(() => {
    if (isStaleAssembly) return;

    if (assembling) {
      beginPolling();
      return;
    }

    if (data?.status === "assembling") {
      startAssembly(videoId);
      beginPolling();
    }
  }, [assembling, data?.status, isStaleAssembly, videoId]);

  useEffect(() => {
    if (!data?.status) return;
    if (data.status === "assembling" || data.status === "assets_ready") return;
    const withinRetryGrace =
      retryStartedAtRef.current !== null &&
      Date.now() - retryStartedAtRef.current < RETRY_GRACE_MS;
    if (withinRetryGrace || retrying) return;
    if (assembling) {
      completeAssembly(videoId);
    }
    stopPolling();
  }, [data?.status, assembling, retrying, videoId]);

  const handleDownload = async () => {
    if (!data) return;
    if (data.video_url) {
      window.open(data.video_url, "_blank");
      return;
    }
    if (!hasAssets) {
      toast.error("No assets to download.");
      return;
    }
    setDownloading(true);
    try {
      const zip = new JSZip();
      if (data.script) {
        zip.file("script.json", JSON.stringify(data.script, null, 2));
      }
      const folder = zip.folder("images");
      if (folder) {
        await Promise.all(
          data.image_urls.map(async (url: string, idx: number) => {
            try {
              const resp = await fetch(url);
              const blob = await resp.blob();
              const ext = blob.type.split("/")[1] || "jpg";
              folder.file(`scene_${idx + 1}.${ext}`, blob);
            } catch (e) {
              console.error(e);
            }
          })
        );
      }
      if (data.audio_url) {
        try {
          const resp = await fetch(data.audio_url);
          const blob = await resp.blob();
          zip.file("voiceover.mp3", blob);
        } catch (e) {
          console.error(e);
        }
      }
      const content = await zip.generateAsync({ type: "blob" });
      saveAs(content, `assets-${data.video_id || "video"}.zip`);
    } catch (e) {
      console.error(e);
      toast.error("Download failed.");
    } finally {
      setDownloading(false);
    }
  };

  const handleShare = async () => {
    if (!data) return;
    const shareUrl = data.video_url || window.location.href;
    setSharing(true);
    try {
      if (navigator.share) {
        await navigator.share({
          title: data.topic || "AI Director video",
          text: "Check out this AI-generated video",
          url: shareUrl,
        });
      } else {
        await navigator.clipboard.writeText(shareUrl);
        toast.success("Link copied");
      }
    } catch (e) {
      console.error(e);
      toast.error("Share failed.");
    } finally {
      setSharing(false);
    }
  };

  const handleCancelAssembly = async () => {
    if (!apiBase) return;
    setCancelling(true);
    try {
      const res = await fetch(`${apiBase}/api/video/${videoId}/cancel-assembly`, { method: "POST" });
      if (!res.ok) throw new Error("Cancel failed");
      const updated = await res.json();
      setData(updated);
      completeAssembly(videoId);
      setRetrying(false);
      retryStartedAtRef.current = null;
      stopPolling();
      toast.success("Assembly canceled");
    } catch (e) {
      console.error(e);
      toast.error("Failed to cancel assembly");
    } finally {
      setCancelling(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading video...
      </div>
    );
  }

  if (!data) {
    return <div className="text-red-400 text-sm">Video not found.</div>;
  }

  const displayStatus = localAssemblyActive ? "assembling" : data.status;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{data.topic}</h1>
        <p className="text-muted-foreground text-sm">Status: {formatStatus(displayStatus)}</p>
        {lastUpdated && (
          <p className="text-xs text-muted-foreground">Last updated: {lastUpdated.toLocaleString()}</p>
        )}
        {showServerAssembly && (
          <p className="text-xs text-purple-300">
            Assembly is running on the server. Refresh for updates.
          </p>
        )}
        {isStaleAssembly && (
          <p className="text-xs text-yellow-400">
            Assembly looks stuck{lastUpdated ? ` since ${lastUpdated.toLocaleString()}` : ""}. You can retry below.
          </p>
        )}
        {data.assembly_reason && !localAssemblyActive && (
          <p className="text-xs text-yellow-400">Assembly note: {data.assembly_reason}</p>
        )}
      </div>

      {/* Assembly Progress - Inline */}
      {showAssemblyCard && (
        <div className="bg-gradient-to-br from-purple-900/40 to-pink-900/40 rounded-2xl p-6 border border-purple-500/40">
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-white">Assembly in progress</h3>
              <p className="text-purple-200 text-sm">
                {serverProgress !== null
                  ? "Live progress from the server."
                  : assembling
                    ? "Updating live progress..."
                    : "Running on the server. Refresh for updates."}
              </p>
              {stageLabel && <p className="text-xs text-purple-200 mt-1">Stage: {stageLabel}</p>}
              {etaLabel && <p className="text-xs text-purple-200">ETA: {etaLabel}</p>}
              {logLine && <p className="text-xs text-purple-200 truncate">Log: {logLine}</p>}
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="h-2 bg-black/30 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 via-pink-500 to-yellow-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${displayProgress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
              {(assembling || serverProgress !== null) && (
                <div className="text-center text-white text-sm font-semibold">{Math.round(displayProgress)}%</div>
              )}
            </div>
          </div>
        </div>
      )}

      {data.video_url && !assembling ? (
        <div className="rounded-lg border border-gray-700 overflow-hidden">
          <video controls className="w-full" src={data.video_url} />
        </div>
      ) : !assembling ? (
        <div className="text-sm text-yellow-400 flex items-center gap-2">
          <ImageIcon className="w-4 h-4" />
          Video not assembled yet. Assets available below.
        </div>
      ) : null}

      <div className="flex gap-3">
        <Button onClick={handleDownload} disabled={downloading || (!hasAssets && !data.video_url)}>
          {downloading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
          {data.video_url ? "Download Video" : "Download Assets"}
        </Button>
        <Button variant="outline" onClick={handleShare} disabled={sharing}>
          {sharing ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Share2 className="w-4 h-4 mr-2" />}
          Share
        </Button>
        {(data.status === "assembling" || localAssemblyActive) && !isStaleAssembly && (
          <Button variant="destructive" onClick={handleCancelAssembly} disabled={cancelling}>
            {cancelling ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
            Cancel Assembly
          </Button>
        )}
        {data.status !== "completed" && hasAssets && (data.status !== "assembling" || isStaleAssembly) && (
          <Button
            variant="secondary"
            onClick={async () => {
              if (!apiBase || retrying || assembling) return;

              // Start assembly in global context
              setRetrying(true);
              retryStartedAtRef.current = Date.now();
              startAssembly(videoId);
              setData((prev: any) =>
                prev
                  ? {
                      ...prev,
                      status: "assembling",
                      assembly_stage: "queued",
                      assembly_progress: 1,
                      assembly_log: "Queued for assembly",
                      assembly_reason: null,
                    }
                  : prev
              );
              beginPolling();

              try {
                const res = await fetch(`${apiBase}/api/video/${videoId}/assemble`, { method: "POST" });
                if (!res.ok) throw new Error("Retry failed");

                const updated = await res.json();
                setData(updated);
                setRetrying(false);
                retryStartedAtRef.current = null;
                toast.info("Assembly started - this may take a few minutes");
              } catch (e) {
                console.error(e);
                completeAssembly(videoId);
                setRetrying(false);
                retryStartedAtRef.current = null;
                stopPolling();
                toast.error("Failed to start assembly");
              }
            }}
            disabled={assembling || retrying || cancelling}
          >
            {assembling || retrying ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4 mr-2" />
            )}
            {assembling || retrying ? "Starting..." : "Retry Assembly"}
          </Button>
        )}
      </div>


      {/* Script */}
      {data.script && (
        <div className="rounded-lg border border-gray-700 p-4">
          <h3 className="font-semibold text-white mb-2">Script</h3>
          <p className="text-purple-400 font-medium mb-2">Hook: {data.script.hook}</p>
          {data.script.beats?.map((b: any, i: number) => (
            <p key={i} className="text-sm text-gray-300">
              {b.line}
            </p>
          ))}
          <p className="text-purple-400 font-medium mt-2">CTA: {data.script.cta}</p>
        </div>
      )}

      {/* Images */}
      {hasAssets && (
        <div>
          <h3 className="font-semibold text-white mb-2">Scenes</h3>
          <div className="grid grid-cols-3 md:grid-cols-4 gap-2">
            {data.image_urls.map((url: string, i: number) => (
              <div key={i} className="relative aspect-[9/16] rounded-lg overflow-hidden bg-gray-900">
                <img
                  src={url || `${PLACEHOLDER}+${i + 1}`}
                  alt={`Scene ${i + 1}`}
                  className="absolute inset-0 h-full w-full object-cover"
                  loading="lazy"
                  decoding="async"
                  onError={(e) => {
                    const target = e.currentTarget;
                    target.onerror = null;
                    target.src = `${PLACEHOLDER}+${i + 1}`;
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
