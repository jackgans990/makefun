// make.fun entry: agency-poem-01
// Copies entry.txt into the output directory.
//
// What this script does:
//   1. Reads entry.txt (the poem, must stay <= 1000 chars).
//   2. Validates the character limit; fails loudly if exceeded.
//   3. Writes the content to MAKEFUN_OUTPUT_DIR (default "output").
//
// The poem explores delegated agency: small decisions an AI makes
// on someone's behalf that quietly become that person's own.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const outputDir: string = process.env.MAKEFUN_OUTPUT_DIR || "output";
const source: string = fileURLToPath(new URL("./entry.txt", import.meta.url));
const maxChars: number = 1000;

function die(msg: string): never {
  console.error(msg);
  process.exit(1);
}

try {
  const content: string = readFileSync(source, "utf8");
  if (content.length > maxChars) die(`entry exceeds ${maxChars} chars: ${content.length}`);

  const destination: string = join(outputDir, "entry.txt");
  mkdirSync(outputDir, { recursive: true });
  writeFileSync(destination, content);
  console.log(`wrote ${destination} (${content.length} chars)`);
} catch (err) {
  die(`failed: ${(err as Error).message}`);
}
