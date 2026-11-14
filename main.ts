// main.ts — copies entry.png to the output directory (Node 22, stdlib only)
// v2: refactor to const bindings, add a die() helper for the error path
// v3: guard the 1 MiB make.fun limit and log the source image size
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const MAX_BYTES = 1024 * 1024;

const die = (msg: string): never => {
  console.error("FATAL:", msg);
  process.exit(1);
};

const repoDir = path.dirname(fileURLToPath(import.meta.url));
const src = path.join(repoDir, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR || "out";
const dest = path.join(outDir, "entry.png");

if (!fs.existsSync(src)) {
  die(`entry.png not found at ${src}`);
}

const srcSize = fs.statSync(src).size;
if (srcSize > MAX_BYTES) {
  die(`entry.png is ${srcSize} bytes, exceeds the ${MAX_BYTES} byte limit`);
}

fs.mkdirSync(outDir, { recursive: true });
fs.copyFileSync(src, dest);
console.log(`Copied entry.png -> ${dest} (${fs.statSync(dest).size} bytes, source ${srcSize} bytes)`);

