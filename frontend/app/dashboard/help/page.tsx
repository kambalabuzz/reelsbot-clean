import Link from "next/link";
import { Mail, BookOpen, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const quickLinks = [
  {
    title: "Series setup",
    description: "Create a series, pick your style, and set a schedule.",
    href: "/dashboard/series/create",
  },
  {
    title: "Connect accounts",
    description: "Link YouTube, TikTok, and Instagram in the Social step.",
    href: "/dashboard/series/create",
  },
  {
    title: "Billing",
    description: "Manage your plan and upgrade when you are ready.",
    href: "/dashboard/billing",
  },
];

export default function HelpPage() {
  return (
    <div className="space-y-8">
      <div className="rounded-2xl border bg-card p-8">
        <h1 className="text-2xl font-semibold">Help & Support</h1>
        <p className="mt-2 text-muted-foreground">
          Use these shortcuts to get back to creating. If you are stuck, reach out and we will help.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button asChild className="gap-2">
            <a href="mailto:support@reelsbot.ai">
              <Mail className="h-4 w-4" />
              Contact support
            </a>
          </Button>
          <Button asChild variant="outline" className="gap-2">
            <Link href="/support">
              Support hub
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {quickLinks.map((link) => (
          <Link
            key={link.title}
            href={link.href}
            className="rounded-2xl border bg-card p-6 transition hover:border-primary/50"
          >
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{link.title}</h2>
              <BookOpen className="h-4 w-4 text-primary" />
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{link.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
