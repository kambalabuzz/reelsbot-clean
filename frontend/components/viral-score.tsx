/* Displays viral score with breakdown and optimization CTA */
"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronDown, Loader2, Wand2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

type Breakdown = {
  hook: number;
  emotion: number;
  curiosity: number;
  trending: number;
};

type Props = {
  score?: number;
  breakdown?: Breakdown;
  strengths?: string[];
  improvements?: string[];
  optimizedScript?: string;
  loading?: boolean;
  onOptimize?: (script: string) => void;
};

export function ViralScore(props: Props) {
  const { breakdown, strengths = [], improvements = [], optimizedScript, onOptimize } = props;
  const [expanded, setExpanded] = useState(false);
  const [displayScore, setDisplayScore] = useState(0);

  const palette = useMemo(() => {
    const score = props.score || 0;
    if (score < 50) return { text: "text-red-500", stroke: "stroke-red-500" };
    if (score < 76) return { text: "text-yellow-500", stroke: "stroke-yellow-500" };
    return { text: "text-green-500", stroke: "stroke-green-500" };
  }, [props.score]);

  useEffect(() => {
    if (!props.score || props.loading) return;
    const target = props.score;
    let current = 0;
    const step = Math.max(1, Math.round(target / 30));
    const id = setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        clearInterval(id);
      }
      setDisplayScore(current);
    }, 16);
    return () => clearInterval(id);
  }, [props.score, props.loading]);

  const chartStroke = useMemo(() => {
    const value = Math.min(props.score || 0, 100);
    const circumference = 2 * Math.PI * 45;
    return {
      dashArray: `${(value / 100) * circumference} ${circumference}`,
      offset: circumference / 4,
    };
  }, [props.score]);

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle>Viral Score</CardTitle>
        {onOptimize && optimizedScript && (
          <Button size="sm" variant="outline" className="gap-2" onClick={() => onOptimize(optimizedScript)}>
            <Wand2 className="h-4 w-4" />
            Use optimized script
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center gap-6">
          <div className="flex items-center gap-4">
            <div className="relative h-24 w-24">
              <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" className="stroke-muted text-muted fill-none" strokeWidth="10" />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  className={`transition-all duration-500 ease-out fill-none stroke-current ${palette.stroke}`}
                  strokeWidth="10"
                  strokeDasharray={chartStroke.dashArray}
                  strokeDashoffset={chartStroke.offset}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                {props.loading ? <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /> : (
                  <div className={`text-2xl font-bold ${palette.text}`}>{displayScore}</div>
                )}
              </div>
            </div>
            <div>
              <p className="text-muted-foreground text-sm">Predicted virality</p>
              <p className={`text-2xl font-semibold ${palette.text}`}>{props.loading ? "…" : `${props.score || 0}/100`}</p>
              <p className="text-xs text-muted-foreground">Higher is better</p>
            </div>
          </div>
          <div className="flex-1 grid grid-cols-2 gap-3">
            {breakdown ? Object.entries(breakdown).map(([key, value]) => (
              <div key={key} className="rounded-lg border p-3">
                <p className="text-xs uppercase text-muted-foreground tracking-wide">{key}</p>
                <p className="text-lg font-semibold">{props.loading ? "…" : value}</p>
              </div>
            )) : (
              <div className="text-sm text-muted-foreground">No breakdown yet.</div>
            )}
          </div>
        </div>

        <button
          type="button"
          className="flex w-full items-center justify-between rounded-md border bg-muted/30 px-3 py-2 text-sm"
          onClick={() => setExpanded(!expanded)}
        >
          <span>View insights</span>
          <ChevronDown className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`} />
        </button>

        {expanded && (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <p className="text-sm font-medium">Strengths</p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {strengths?.length ? strengths.map((item) => <li key={item}>• {item}</li>) : <li>Pending analysis</li>}
              </ul>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">Improvements</p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {improvements?.length ? improvements.map((item) => <li key={item}>• {item}</li>) : <li>Pending analysis</li>}
              </ul>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
