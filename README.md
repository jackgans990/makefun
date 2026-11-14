# food-picture-01

make.fun entry: a single 1024x1024 PNG of the most appetizing food picture —
a **top-down ramen bowl** drawn entirely with PIL: glossy amber broth, wavy
yellow noodles, two jammy egg halves, nori sheets, a chashu slice, scallion
rings, chili oil droplets, steam wisps and chopsticks on a dark wooden table.

## Build

Regenerate the image (Python 3 + Pillow):

```sh
python3 tools/generate_food.py   # writes entry.png
```

Copy to the make.fun output dir (Node 22, stdlib only):

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
# -> out/entry.png (1024x1024, 421641 bytes)
```

## Files

- `entry.png` — the entry image (1024x1024, under 1 MiB)
- `main.ts` — copies `entry.png` into `$MAKEFUN_OUTPUT_DIR` (default `out`), with a 1 MiB guard
- `tools/generate_food.py` — PIL script that draws the ramen bowl
- `LICENSE` — MIT
- `.makefun/owner.json` — entry owner wallet
