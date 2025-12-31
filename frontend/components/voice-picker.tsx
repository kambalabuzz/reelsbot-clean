/* Reusable voice picker + previewer for ElevenLabs */
"use client";

import { useEffect, useState } from "react";
import { listVoices, previewVoice } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2, Volume2 } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

type Voice = {
  voice_id: string;
  name: string;
  description?: string;
};

let cachedVoices: Voice[] | null = null;

type Props = {
  defaultText?: string;
  onSelect?: (voiceId: string) => void;
};

export function VoicePicker({ defaultText = "This is your AI voice preview.", onSelect }: Props) {
  const { toast } = useToast();
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loadingVoices, setLoadingVoices] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<string>("");
  const [previewText, setPreviewText] = useState(defaultText);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [voicesError, setVoicesError] = useState<string | null>(null);

  useEffect(() => {
    const loadVoices = async () => {
      setLoadingVoices(true);
      setVoicesError(null);
      try {
        if (cachedVoices) {
          setVoices(cachedVoices);
          if (cachedVoices.length > 0 && !selectedVoice) {
            setSelectedVoice(cachedVoices[0].voice_id);
            onSelect?.(cachedVoices[0].voice_id);
          }
          return;
        }
        const res = await listVoices();
        const list = res?.voices || [];
        setVoices(list);
        cachedVoices = list;
        if (list.length > 0) {
          setSelectedVoice(list[0].voice_id);
          onSelect?.(list[0].voice_id);
        }
      } catch (err) {
        setVoicesError("Unable to load voices. Check API key/quota.");
        toast({ title: "Unable to load voices", variant: "destructive" });
      } finally {
        setLoadingVoices(false);
      }
    };
    loadVoices();
  }, [onSelect, toast]);

  const handlePreview = async () => {
    if (!previewText.trim()) {
      toast({ title: "Enter text to preview" });
      return;
    }
    setPreviewLoading(true);
    try {
      const res = await previewVoice({ text: previewText, voice_id: selectedVoice || undefined });
      const audioBase64 = res?.audio_base64;
      if (audioBase64) {
        const url = `data:audio/mpeg;base64,${audioBase64}`;
        setAudioUrl(url);
      }
    } catch (err) {
      toast({ title: "Preview failed", variant: "destructive" });
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Voices</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1">
          <p className="text-sm font-medium">Select voice</p>
          {loadingVoices ? (
            <div className="text-sm text-muted-foreground flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading voices…
            </div>
          ) : voicesError ? (
            <div className="flex items-center justify-between">
              <p className="text-sm text-destructive">{voicesError}</p>
              <Button variant="outline" size="sm" onClick={() => { cachedVoices = null; setVoicesError(null); setLoadingVoices(true); listVoices().then((res) => {
                const list = res?.voices || [];
                cachedVoices = list;
                setVoices(list);
                if (list.length > 0) {
                  setSelectedVoice(list[0].voice_id);
                  onSelect?.(list[0].voice_id);
                }
              }).catch(() => setVoicesError("Unable to load voices.")).finally(() => setLoadingVoices(false)); }}>
                Retry
              </Button>
            </div>
          ) : (
            <Select value={selectedVoice} onValueChange={(val) => { setSelectedVoice(val); onSelect?.(val); }}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a voice" />
              </SelectTrigger>
              <SelectContent>
                {voices.map((v) => (
                  <SelectItem key={v.voice_id} value={v.voice_id}>
                    {v.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        <div className="space-y-1">
          <p className="text-sm font-medium">Preview text</p>
          <Textarea value={previewText} onChange={(e) => setPreviewText(e.target.value)} rows={3} />
        </div>

        <Button className="gap-2" onClick={handlePreview} disabled={previewLoading}>
          {previewLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Volume2 className="h-4 w-4" />}
          {previewLoading ? "Generating..." : "Preview voice"}
        </Button>

        {audioUrl && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Preview</p>
            <audio controls src={audioUrl} className="w-full" />
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          Previews are limited to 320 characters to control costs.
        </p>
      </CardContent>
    </Card>
  );
}
