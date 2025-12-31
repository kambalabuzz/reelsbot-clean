import { existsSync, readFileSync } from "fs";
import { join } from "path";

type LegalDoc = "privacy" | "terms";

const cache: Partial<Record<LegalDoc, string>> = {};

const resolveLegalPath = (doc: LegalDoc) => {
  const candidates = [
    join(process.cwd(), "content", `${doc}.html`),
    join(process.cwd(), "frontend", "content", `${doc}.html`),
  ];
  return candidates.find((candidate) => existsSync(candidate));
};

export function getLegalHtml(doc: LegalDoc): string {
  if (!cache[doc]) {
    const filePath = resolveLegalPath(doc);
    if (!filePath) {
      throw new Error(`Missing legal document: ${doc}`);
    }
    cache[doc] = readFileSync(filePath, "utf8");
  }
  return cache[doc] || "";
}
