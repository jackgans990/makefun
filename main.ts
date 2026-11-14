// ai-happy-01 entry: copies entry.png to the output dir (Node 22 stdlib only).
// VERSION 2: minor refactor — named constants SRC and OUT declared up top,
// existence check + die() helper kept from VERSION 1.
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const SRC = fileURLToPath(new URL('./entry.png', import.meta.url));
const OUT = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

function die(msg: string): never {
  console.error(`error: ${msg}`);
  process.exit(1);
}

if (!existsSync(SRC)) {
  die(`entry.png not found next to main.ts (looked at: ${SRC}). ` +
      `Make sure entry.png is committed in the repo root before running.`);
}

try {
  mkdirSync(OUT, { recursive: true });
  copyFileSync(SRC, join(OUT, 'entry.png'));
  console.log(`copied ${SRC} -> ${join(OUT, 'entry.png')}`);
} catch (err) {
  die(`failed to copy to ${OUT}: ${err instanceof Error ? err.message : String(err)}`);
}
