const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function createSeries(data: any) {
  const res = await fetch(`${API_URL}/api/series`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create series");
  return res.json();
}

export async function getSeries() {
  const res = await fetch(`${API_URL}/api/series`);
  if (!res.ok) throw new Error("Failed to fetch series");
  return res.json();
}

export async function deleteSeries(id: string) {
  const res = await fetch(`${API_URL}/api/series/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete series");
  return res.json();
}

export async function createEpisode(seriesId: string, topic: string) {
  const res = await fetch(`${API_URL}/api/episodes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ series_id: seriesId, topic }),
  });
  if (!res.ok) throw new Error("Failed to create episode");
  return res.json();
}

export async function getEpisodes(seriesId?: string) {
  const url = seriesId
    ? `${API_URL}/api/episodes?series_id=${seriesId}`
    : `${API_URL}/api/episodes`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch episodes");
  return res.json();
}

export async function deleteEpisode(id: string) {
  const res = await fetch(`${API_URL}/api/episodes/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete episode");
  return res.json();
}

export async function generateVideo(data: any) {
  const res = await fetch(`${API_URL}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to start generation");
  return res.json();
}

export async function getJobStatus(jobId: string) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`);
  if (!res.ok) throw new Error("Job not found");
  return res.json();
}

export async function getSocialAccounts() {
  const res = await fetch(`${API_URL}/api/social-accounts`);
  if (!res.ok) throw new Error("Failed to fetch social accounts");
  return res.json();
}

export async function connectSocialAccount(provider: string, redirectUrl?: string) {
  if (provider === "youtube") {
    const url = new URL(`${API_URL}/api/auth/${provider}/start`);
    if (redirectUrl) url.searchParams.set("redirect_url", redirectUrl);
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error("Failed to start OAuth");
    return res.json();
  }
  const res = await fetch(`${API_URL}/api/social-accounts/connect?provider=${provider}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to connect account");
  return res.json();
}

export async function analyzeViralScore(script: string, topic?: string) {
  const res = await fetch(`${API_URL}/api/analyze-viral-score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script, topic }),
  });
  if (!res.ok) throw new Error("Failed to analyze script");
  return res.json();
}

export async function fetchTrends(niche: string) {
  const res = await fetch(`${API_URL}/api/trends/${encodeURIComponent(niche)}`);
  if (!res.ok) throw new Error("Failed to load trends");
  return res.json();
}

export async function generateSeriesPlan(payload: { topic: string; num_episodes: number; niche?: string }) {
  const res = await fetch(`${API_URL}/api/generate-series-plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to generate plan");
  return res.json();
}

export async function updateEpisodeStats(episodeId: string, stats: Record<string, any>) {
  const res = await fetch(`${API_URL}/api/episodes/${episodeId}/stats`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(stats),
  });
  if (!res.ok) throw new Error("Failed to update stats");
  return res.json();
}

export async function fetchAnalytics(userId: string) {
  const res = await fetch(`${API_URL}/api/analytics/${userId}`);
  if (!res.ok) throw new Error("Failed to load analytics");
  return res.json();
}

export async function cloneVideo(payload: { video_url?: string; transcript?: string }) {
  const res = await fetch(`${API_URL}/api/clone-video`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to analyze video");
  return res.json();
}

export async function applyTemplate(payload: { analysis: any; topic: string }) {
  const res = await fetch(`${API_URL}/api/apply-template`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to apply template");
  return res.json();
}

export async function listVoices() {
  const res = await fetch(`${API_URL}/api/voices`);
  if (!res.ok) throw new Error("Failed to load voices");
  return res.json();
}

export async function previewVoice(payload: { text: string; voice_id?: string }) {
  const res = await fetch(`${API_URL}/api/voices/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to generate preview");
  return res.json();
}
