import { getLegalHtml } from "@/lib/legal";

export const metadata = {
  title: "Privacy Policy - ReelsBot",
  description: "ReelsBot privacy policy.",
};

export default function PrivacyPage() {
  const html = getLegalHtml("privacy");

  return (
    <main className="legal-shell">
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </main>
  );
}
