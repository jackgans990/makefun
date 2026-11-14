// ai-happy-01 entry: copies entry.png to the output dir (Node 22 stdlib only).
import { copyFileSync, statSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const src = fileURLToPath(new URL('./entry.png', import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

function die(msg: string): never {
  console.error(`error: ${msg}`);
  process.exit(1);
}

try {
  statSync(src);
} catch {
  die(`source file not found: ${src}`);
}

try {
  mkdirSync(outDir, { recursive: true });
  copyFileSync(src, join(outDir, 'entry.png'));
} catch (err) {
  die(`failed to copy to ${outDir}: ${err instanceof Error ? err.message : String(err)}`);
}
