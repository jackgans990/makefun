// ai-joke-03 entry: copies the joke to the output dir.
import { copyFileSync } from 'node:fs';
import { join } from 'node:path';

copyFileSync(new URL('./entry.txt', import.meta.url), join(process.env.MAKEFUN_OUTPUT_DIR ?? '/output', 'entry.txt'));
