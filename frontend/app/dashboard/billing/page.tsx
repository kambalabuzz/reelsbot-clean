"use client";

import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const plans = [
  {
    id: "hobby",
    name: "Hobby",
    price: 19,
    description: "Best for creators starting out",
    features: [
      "3 posts per week",
      "1 Series",
      "Automated posting",
      "Background music",
      "6+ art styles",
      "AI voiceover",
      "No watermark",
    ],
  },
  {
    id: "daily",
    name: "Daily",
    price: 39,
    description: "Best for growing creators",
    features: [
      "Posts every day",
      "3 Series",
      "Everything in Hobby",
      "Priority rendering",
      "25+ art styles",
      "Custom music",
      "Analytics",
    ],
    popular: true,
  },
  {
    id: "pro",
    name: "Pro",
    price: 69,
    description: "Best for serious creators",
    features: [
      "2 posts per day",
      "10 Series",
      "Everything in Daily",
      "API access",
      "White-label",
      "Team members",
      "Priority support",
    ],
  },
];

export default function BillingPage() {
  const [loading, setLoading] = useState<string | null>(null);

  const handleCheckout = async (planId: string) => {
    setLoading(planId);
    try {
      const res = await fetch(`${API_URL}/api/checkout?plan=${planId}`, {
        method: "POST",
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      }
    } catch (err) {
      console.error(err);
    }
    setLoading(null);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Billing</h1>
        <p className="text-muted-foreground">Choose your plan</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <Card
            key={plan.id}
            className={cn("relative", plan.popular && "border-primary shadow-lg")}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs font-medium px-3 py-1 rounded-full">
                MOST POPULAR
              </div>
            )}
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <div className="mt-2">
                <span className="text-4xl font-bold">${plan.price}</span>
                <span className="text-muted-foreground">/mo</span>
              </div>
              <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 mb-6">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-primary" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                className="w-full"
                variant={plan.popular ? "default" : "outline"}
                onClick={() => handleCheckout(plan.id)}
                disabled={loading === plan.id}
              >
                {loading === plan.id ? "Loading..." : `Choose ${plan.name}`}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}