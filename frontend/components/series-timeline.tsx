/* Visual timeline for generated series with simple reordering controls */
"use client";

import { GripVertical, Pencil, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Episode = {
  episode_number: number;
  title: string;
  hook?: string;
  description?: string;
  cliffhanger?: string;
};

type Props = {
  episodes: Episode[];
  onReorder?: (episodes: Episode[]) => void;
  onEdit?: (episode: Episode) => void;
  onGenerateAll?: () => void;
};

export function SeriesTimeline({ episodes, onReorder, onEdit, onGenerateAll }: Props) {
  const moveEpisode = (index: number, direction: -1 | 1) => {
    if (!onReorder) return;
    const next = [...episodes];
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= episodes.length) return;
    const temp = next[index];
    next[index] = next[newIndex];
    next[newIndex] = temp;
    onReorder(next.map((ep, idx) => ({ ...ep, episode_number: idx + 1 })));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Series roadmap</h3>
          <p className="text-sm text-muted-foreground">Reorder episodes or refine before generating.</p>
        </div>
        {onGenerateAll && (
          <Button onClick={onGenerateAll} className="gap-2">
            <Play className="h-4 w-4" />
            Create all episodes
          </Button>
        )}
      </div>
      <div className="space-y-3">
        {episodes.map((episode, index) => (
          <Card key={episode.title + index}>
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <GripVertical className="h-5 w-5 text-muted-foreground" />
                <div>
                  <CardTitle className="text-base">
                    {episode.episode_number}. {episode.title}
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">{episode.hook}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => moveEpisode(index, -1)}>Up</Button>
                <Button variant="outline" size="sm" onClick={() => moveEpisode(index, 1)}>Down</Button>
                {onEdit && (
                  <Button variant="ghost" size="icon" onClick={() => onEdit(episode)}>
                    <Pencil className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm">{episode.description}</p>
              <p className="text-xs text-muted-foreground">Cliffhanger: {episode.cliffhanger}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
