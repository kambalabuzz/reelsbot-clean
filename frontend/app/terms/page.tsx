import { getLegalHtml } from "@/lib/legal";

export const metadata = {
  title: "Terms of Service - ReelsBot",
  description: "ReelsBot terms of service.",
};

export default function TermsPage() {
  const html = getLegalHtml("terms");

  return (
    <main className="legal-shell">
      <div dangerouslySetInnerHTML={{ __html: html }} />
    </main>
  );
}
