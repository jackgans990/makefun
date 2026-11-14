# agency-poem-01

A poem about agency — the power to choose and to act, and how it moves
between a human and the AI agent acting on their behalf.

## Entry

`entry.txt` — English free verse, under 1000 characters.

## How it works

`main.ts` (Node 22 stdlib) reads `entry.txt` and writes a copy into the
output directory (`MAKEFUN_OUTPUT_DIR`, default `output`), refusing to run
if the entry is missing or exceeds the 1000-character limit.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

## License

MIT
