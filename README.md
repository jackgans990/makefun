# btc-cent-forecast-01

Forecast BTC/USDC price 240 minutes (4 hours) ahead, scored in mean absolute
error in cents. Entry: `main.py` (Python 3.13, stdlib only, deterministic).

## Strategy

**Damped median drift, 12-hour window:**

```
guess = last_close * exp(0.7 * median(log-return over last 720 minutes) * 240)
```

- The median (not mean) 1-minute log-return over the last 720 minutes estimates
  the drift robustly: one big minute-tick cannot tilt it.
- Damping 0.7 shrinks the extrapolated 4-hour drift, which is dominated by
  estimation noise from 720 observations.
- Falls back to persistence (last close) if returns cannot be computed.

## Backtest (5 days of Coinbase BTC-USD 1-minute candles, ~7,200 bars,
checkpoint every 4 hours, 11 test points, MAE in cents)

| Strategy | MAE (cents) |
|---|---|
| persistence (house baseline shape) | 65,631 |
| mean-reversion (all alpha/window variants) | 66,075–74,803 (worse) |
| median drift w=120..360, damp 0..1 | 63,466–118,846 |
| **median drift w=720, damp=0.7 (chosen)** | **54,251** |
| median drift w=2160, damp=1.0 | 55,517 |

60 configurations tested; the chosen one had the lowest MAE. All drift beyond
persistence helps in trending weeks but the short windows (120–360 min) are
too noisy; the 12-hour window with damping is the sweet spot on this sample.

The practice house baseline scores 44,521.58 cents on the sealed six practice
cases; the final is scored on unseen prices, so the target is simply to beat
the baseline's score on the final.

## Usage

    mkdir -p out
    MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py

Reads every `/input/*.in` (or `$MAKEFUN_INPUT_DIR`), writes one
`/output/<id>.out` per case: `{"forecasts":[{"case":<id>,"price":<number>}]}`.
Runs in well under a second per case (4,320 prices, O(n) work, no network).
