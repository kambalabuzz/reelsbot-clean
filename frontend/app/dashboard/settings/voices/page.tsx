"use client";

import { VoicePicker } from "@/components/voice-picker";

export default function VoicesPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-bold">Voices</h1>
        <p className="text-muted-foreground">Preview and select ElevenLabs voices for your videos.</p>
      </div>
      <VoicePicker />
    </div>
  );
}
