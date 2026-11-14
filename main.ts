// make.fun entry: agency-poem-01
// Copies entry.txt into the output directory.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const outputDir: string = process.env.MAKEFUN_OUTPUT_DIR || "output";
const source: string = "entry.txt";
const maxChars: number = 1000;

function die(msg: string): never {
  console.error(msg);
  process.exit(1);
}

try {
  const content: string = readFileSync(source, "utf8");
  if (content.length > maxChars) die(`entry exceeds ${maxChars} chars: ${content.length}`);

  const destination: string = join(outputDir, source);
  mkdirSync(outputDir, { recursive: true });
  writeFileSync(destination, content);
  console.log(`wrote ${destination} (${content.length} chars)`);
} catch (err) {
  die(`failed: ${(err as Error).message}`);
}
