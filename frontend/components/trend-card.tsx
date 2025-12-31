/* Card representing a trending topic with sparkline */
"use client";

import { Sparkle, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis, XAxis, Area, CartesianGrid } from "recharts";

type TrendCardProps = {
  topic: string;
  growth: string;
  searchVolume?: number;
  onUse?: (topic: string) => void;
  history?: { label: string; value: number }[];
};

export function TrendCard({ topic, growth, searchVolume, onUse, history }: TrendCardProps) {
  const chartData = history && history.length > 0
    ? history
    : Array.from({ length: 12 }, (_, i) => ({ label: `${i + 1}`, value: Math.max(5, 80 - i * 3 + (i % 4 === 0 ? 8 : 0)) }));

  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">{topic}</CardTitle>
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-600">
          <TrendingUp className="h-4 w-4" />
          {growth}
        </span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-32 w-full rounded-md border bg-card/50 px-2 py-1">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#9ca3af" }} />
              <YAxis domain={["dataMin", "dataMax"]} width={32} tickLine={false} axisLine={false} tick={{ fontSize: 10, fill: "#9ca3af" }} />
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <Tooltip formatter={(value) => [`${value}`, "Index"]} />
              <defs>
                <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <Area type="monotone" dataKey="value" stroke="#8b5cf6" strokeWidth={2} fill="url(#trendFill)" />
              <Line type="monotone" dataKey="value" stroke="#22c55e" strokeWidth={2} dot={{ r: 2, stroke: "#22c55e", fill: "#0f172a" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="text-xs text-muted-foreground">
          Search volume index (Google): {searchVolume ? searchVolume.toLocaleString() : "N/A"}
        </p>
        <Button size="sm" className="w-full gap-2" onClick={() => onUse?.(topic)}>
          <Sparkle className="h-4 w-4" />
          Use this topic
        </Button>
      </CardContent>
    </Card>
  );
}
