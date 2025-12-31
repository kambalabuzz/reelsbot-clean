"use client";

import { useState } from "react";
import { useToast } from "@/components/ui/use-toast";
import { cloneVideo, applyTemplate } from "@/lib/api";
import { CloneAnalyzer } from "@/components/clone-analyzer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";

export default function ClonePage() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [template, setTemplate] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [customTopic, setCustomTopic] = useState("");
  const [generatedScript, setGeneratedScript] = useState<any>(null);
  const { toast } = useToast();

  const handleAnalyze = async (payload: { video_url?: string; transcript?: string }) => {
    setLoading(true);
    try {
      const data = await cloneVideo(payload);
      setAnalysis(data.analysis);
      setTemplate(data.extracted_template);
      setSuggestions(data.suggested_topics || []);
      toast({ title: "Analysis complete", description: "Template extracted." });
    } catch (err) {
      toast({ title: "Analysis failed", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (topic: string) => {
    if (!analysis) {
      toast({ title: "Analyze first", description: "Run an analysis to capture the template." });
      return;
    }
    setLoading(true);
    try {
      const data = await applyTemplate({ analysis, topic });
      setGeneratedScript(data);
      toast({ title: "Script generated" });
    } catch (err) {
      toast({ title: "Unable to apply template", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Clone a video</h1>
        <p className="text-muted-foreground">Reverse engineer hooks, pacing, and structure. Reuse the style instantly.</p>
      </div>

      <CloneAnalyzer
        loading={loading}
        onAnalyze={handleAnalyze}
        analysis={analysis}
        template={template || undefined}
        suggestions={suggestions}
        onApply={handleApply}
      />

      <Card>
        <CardHeader>
          <CardTitle>Apply to a custom topic</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-col gap-2 md:flex-row">
            <Input placeholder="Apply this style to..." value={customTopic} onChange={(e) => setCustomTopic(e.target.value)} />
            <Button onClick={() => handleApply(customTopic)} disabled={loading} className="gap-2">
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Apply template
            </Button>
          </div>
          {generatedScript && (
            <div className="rounded-md border p-3">
              <p className="text-sm whitespace-pre-wrap">{generatedScript.script || generatedScript}</p>
              {generatedScript.cta && <p className="mt-2 text-xs text-muted-foreground">CTA: {generatedScript.cta}</p>}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
