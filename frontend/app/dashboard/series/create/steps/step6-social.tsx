"use client";

import { SeriesFormData } from "../page";
import { cn } from "@/lib/utils";
import { Plus, Check, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useEffect, useState } from "react";
import { connectSocialAccount, getSocialAccounts } from "@/lib/api";

const platforms = [
  { 
    id: "tiktok", 
    name: "TikTok", 
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z'/%3E%3C/svg%3E",
    color: "bg-black"
  },
  { 
    id: "instagram", 
    name: "Instagram", 
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z'/%3E%3C/svg%3E",
    color: "bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400"
  },
  { 
    id: "youtube", 
    name: "YouTube", 
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='white' d='M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z'/%3E%3C/svg%3E",
    color: "bg-red-600"
  },
];

type Props = {
  formData: SeriesFormData;
  updateFormData: (data: Partial<SeriesFormData>) => void;
};

export default function Step6Social({ formData, updateFormData }: Props) {
  const [connected, setConnected] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const accounts = await getSocialAccounts();
        const map: Record<string, boolean> = {};
        accounts.forEach((a: any) => { map[a.provider] = true; });
        setConnected(map);
        updateFormData({
          platforms: {
            ...formData.platforms,
            ...map,
          },
        });
      } catch (err) {
        console.error(err);
        setError("Unable to load connected accounts.");
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const togglePlatform = (platformId: string) => {
    updateFormData({
      platforms: {
        ...formData.platforms,
        [platformId]: !formData.platforms[platformId as keyof typeof formData.platforms],
      },
    });
  };

  const handleConnect = async (provider: string) => {
    setLoading(true);
    setError(null);
    try {
      const redirectUrl =
        typeof window !== "undefined"
          ? `${window.location.origin}/dashboard/series/create`
          : undefined;
      const response = await connectSocialAccount(provider, redirectUrl);
      if (response?.auth_url) {
        window.location.href = response.auth_url;
        return;
      }
      setConnected((prev) => ({ ...prev, [provider]: true }));
      updateFormData({
        platforms: {
          ...formData.platforms,
          [provider]: true,
        },
      });
    } catch (err) {
      console.error(err);
      setError(`Failed to connect ${provider}.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Connect Social Accounts</h2>
        <p className="text-muted-foreground">
          Connect and select the social media accounts where you want to publish your content
        </p>
      </div>

      <div className="max-w-xl mx-auto">
        <div className="border rounded-xl p-8 text-center mb-6">
          <p className="text-muted-foreground mb-6">
            {Object.keys(connected).length === 0
              ? "You haven't connected any social media accounts yet."
              : "Connected accounts will be used for auto-posting."}
          </p>
          
          <div className="flex flex-col gap-4">
            {platforms.map((platform) => (
              <Button
                key={platform.id}
                variant="outline"
                className="w-full h-14 justify-start gap-4"
                disabled={loading}
                onClick={() => handleConnect(platform.id)}
              >
                <div className={cn("w-10 h-10 rounded-lg flex items-center justify-center", platform.color)}>
                  <img src={platform.icon} alt={platform.name} className="w-5 h-5" />
                </div>
                <span className="flex-1 text-left font-medium">
                  Connect {platform.name}
                </span>
                {formData.platforms[platform.id as keyof typeof formData.platforms] || connected[platform.id] ? (
                  <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <Check className="h-4 w-4 text-white" />
                  </div>
                ) : (
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            ))}
          </div>
        </div>

        {error && (
          <p className="text-sm text-destructive text-center mb-4">{error}</p>
        )}

        <p className="text-sm text-muted-foreground text-center">
          You can connect your social media accounts later.
        </p>
      </div>
    </div>
  );
}
