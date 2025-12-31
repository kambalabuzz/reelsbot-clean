import Link from "next/link";
import { Mail, LifeBuoy, MessageSquare, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const faqs = [
  {
    question: "Why isn't my video generating?",
    answer: "Most issues are missing API keys or an expired social token. Reconnect the account and retry the episode.",
  },
  {
    question: "Can I reschedule a series?",
    answer: "Yes. Edit the series schedule and the next runs will use the updated cadence.",
  },
  {
    question: "Where are my uploads stored?",
    answer: "Assets are stored in your Supabase storage bucket and linked to the series episode record.",
  },
  {
    question: "How do I connect YouTube?",
    answer: "Complete OAuth on the Series step, then pick YouTube as a destination before scheduling.",
  },
];

export const metadata = {
  title: "Support - ReelsBot",
  description: "Get help with ReelsBot.",
};

export default function SupportPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto w-full max-w-5xl px-6 py-16">
        <div className="rounded-3xl border bg-card p-10 shadow-lg">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm text-primary">
                <LifeBuoy className="h-4 w-4" />
                Support
              </div>
              <h1 className="mt-4 text-3xl font-semibold md:text-4xl">
                We are here to help you ship faster.
              </h1>
              <p className="mt-3 text-muted-foreground">
                Tell us what you are building and we will unblock you quickly.
              </p>
            </div>
            <div className="flex flex-col gap-3">
              <Button asChild className="gap-2">
                <a href="mailto:support@reelsbot.ai">
                  <Mail className="h-4 w-4" />
                  Email Support
                </a>
              </Button>
              <Button asChild variant="outline" className="gap-2">
                <Link href="/dashboard">
                  Open Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <div className="rounded-2xl border bg-background/60 p-6">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h2 className="mt-3 text-lg font-semibold">Response time</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                We respond within 24 hours on weekdays.
              </p>
            </div>
            <div className="rounded-2xl border bg-background/60 p-6">
              <LifeBuoy className="h-5 w-5 text-primary" />
              <h2 className="mt-3 text-lg font-semibold">Need urgent help?</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Include your series ID and recent logs so we can help faster.
              </p>
            </div>
            <div className="rounded-2xl border bg-background/60 p-6">
              <Mail className="h-5 w-5 text-primary" />
              <h2 className="mt-3 text-lg font-semibold">Account updates</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Billing or account changes are handled via email for security.
              </p>
            </div>
          </div>

          <div className="mt-12">
            <h2 className="text-2xl font-semibold">Frequently asked</h2>
            <div className="mt-6 grid gap-4">
              {faqs.map((faq) => (
                <div key={faq.question} className="rounded-2xl border bg-background/40 p-5">
                  <h3 className="text-base font-semibold">{faq.question}</h3>
                  <p className="mt-2 text-sm text-muted-foreground">{faq.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
