import { readFileSync } from "fs";
import { join } from "path";

type LegalDoc = "privacy" | "terms";

const cache: Partial<Record<LegalDoc, string>> = {};

export function getLegalHtml(doc: LegalDoc): string {
  if (!cache[doc]) {
    const filePath = join(process.cwd(), "content", `${doc}.html`);
    cache[doc] = readFileSync(filePath, "utf8");
  }
  return cache[doc] || "";
}
