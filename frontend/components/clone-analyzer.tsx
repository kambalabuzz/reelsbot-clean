/* Handles clone workflow UI */
"use client";

import { useState } from "react";
import { Copy, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";

type Analysis = {
  hook_type?: string;
  pacing?: string;
  structure?: string[];
  tone?: string;
  music_mood?: string;
  avg_scene_duration?: number;
};

type Props = {
  loading?: boolean;
  onAnalyze: (payload: { video_url?: string; transcript?: string }) => Promise<void>;
  analysis?: Analysis;
  template?: string;
  suggestions?: string[];
  onApply?: (topic: string) => void;
};

export function CloneAnalyzer({ loading, onAnalyze, analysis, template, suggestions = [], onApply }: Props) {
  const [url, setUrl] = useState("");
  const [transcript, setTranscript] = useState("");

  const handleAnalyze = async () => {
    await onAnalyze({ video_url: url || undefined, transcript: transcript || undefined });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Analyze a video</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <label className="text-sm font-medium">Video URL</label>
            <div className="flex gap-2">
              <Input placeholder="Paste TikTok/YouTube/Instagram URL" value={url} onChange={(e) => setUrl(e.target.value)} />
              <Button type="button" variant="outline" onClick={() => navigator.clipboard.readText().then(setUrl)} className="gap-2">
                <Copy className="h-4 w-4" />
                Paste
              </Button>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">Or transcript</label>
            <Textarea placeholder="Paste transcript" value={transcript} onChange={(e) => setTranscript(e.target.value)} rows={4} />
          </div>
          <Button onClick={handleAnalyze} disabled={loading} className="gap-2">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Analyzing..." : "Analyze"}
          </Button>
        </CardContent>
      </Card>

      {analysis && (
        <Card>
          <CardHeader>
            <CardTitle>Template breakdown</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            <InfoCard label="Hook type" value={analysis.hook_type} />
            <InfoCard label="Pacing" value={analysis.pacing} />
            <InfoCard label="Tone" value={analysis.tone} />
            <InfoCard label="Music mood" value={analysis.music_mood} />
            <InfoCard label="Avg scene" value={analysis.avg_scene_duration ? `${analysis.avg_scene_duration}s` : undefined} />
            <InfoCard label="Structure" value={analysis.structure?.join(" → ")} />
          </CardContent>
        </Card>
      )}

      {template && (
        <Card>
          <CardHeader>
            <CardTitle>Reusable template</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{template}</p>
          </CardContent>
        </Card>
      )}

      {suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Suggested topics</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 md:grid-cols-2">
            {suggestions.map((s) => (
              <Button key={s} variant="outline" className="justify-between" onClick={() => onApply?.(s)}>
                {s}
                <Sparkles className="h-4 w-4" />
              </Button>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function InfoCard({ label, value }: { label: string; value?: string }) {
  return (
    <div className="rounded-lg border p-3">
      <p className="text-xs text-muted-foreground uppercase">{label}</p>
      <p className="text-sm font-medium">{value || "—"}</p>
    </div>
  );
}
