# news-image-01

make.fun entry: a single 1024x1024 PNG summarizing the world's news on
**Friday, 13 November 2026** — six headlines, one image, under 1 MiB.

## Headlines

1. **Iran** — Iran claims radar strike in Bahrain; US intercepts 2 drones (Guardian/CENTCOM)
2. **USA** — FAA nationwide ground stop lifted after comms outage; SpaceX debris halted west coast flights (Guardian)
3. **TECH** — Nvidia CEO Jensen Huang resigns (AP/NPR)
4. **UKRAINE** — Russia-Ukraine peace talks in Abu Dhabi end without breakthrough — first talks in 9 months (AP/NPR)
5. **TECH** — Microsoft 365 global outage hit email and the workday (The Hindu/AP)
6. **INDIA** — Delhi world's most polluted city, AQI 334 (IQAir via The Hindu)

## Build

Regenerate the image (Python 3 + Pillow, DejaVu fonts):

```sh
python3 tools/generate_news.py   # writes entry.png
```

Copy to the make.fun output dir (Node 22, stdlib only):

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
# -> out/entry.png (1024x1024, 94071 bytes)
```

## Files

- `entry.png` — the entry image
- `main.ts` — copies `entry.png` into `$MAKEFUN_OUTPUT_DIR` (default `out`)
- `tools/generate_news.py` — PIL script that draws the infographic
- `LICENSE` — MIT
- `.makefun/owner.json` — entry owner wallet
