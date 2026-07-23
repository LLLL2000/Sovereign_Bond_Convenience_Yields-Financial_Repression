# Parameter sweeps — habitat NK-FTPL calibration fix & Decision A

## Sweep 1 — ACCOMMODATION (Decision A lever), baseline calibration

`b̂L = accom·(λ̂L+V̂liab) − Q̂L`. accom=1 is the Entrega III rule (long
supply expands with the mandate, A not squeezed); accom=0 is Decision A
(no accommodation, mandate redistributes, A squeezed off habitat).

| accom | BK | λ: π̂₀ | λ: Q̂ᴸ₀ | λ: X̂₀ | λ: v̂₀ | λ: ŷ₀ | money: π̂₀ | money: ŷ₀ |
|---:|:--:|---:|---:|---:|---:|---:|---:|---:|
| 1.00 | ✓ | -1.300 | **-0.312**↓ | +3.38 | +1.023 | -10.93 | -2.500 | -27.07 |
| 0.75 | ✓ | -0.890 | **-0.217**↓ | +6.36 | +0.697 | -7.19 | -2.500 | -27.07 |
| 0.50 | ✓ | -0.480 | **-0.122**↓ | +9.34 | +0.372 | -3.46 | -2.500 | -27.07 |
| 0.25 | ✓ | -0.071 | **-0.028**↓ | +12.33 | +0.046 | +0.28 | -2.500 | -27.07 |
| 0.00 | ✓ | +0.339 | **+0.067**↑ | +15.31 | -0.279 | +4.02 | -2.500 | -27.07 |

Reading: accom→0 flips the **long price to RISE** (Decision A works) and
shrinks the λ-output collapse. But π̂₀ and v̂₀ flip sign — the rent is too
small (X̄/v̄≈0.34%) to drive the 'rent→backing→deflation' story; long-bond
revaluation dominates. The monetary column is unaffected (no mandate).

## Sweep 2 — DURATION / δ (drives long-debt dominance), accom=0

χ̄=0.353 held as a quantity share; δ set from the duration target.

| duration | δ | Q̄ᴸ | wL (mkt-val) | φ | checks | λ: Q̂ᴸ₀ | λ: π̂₀ | λ: ŷ₀ | money: ŷ₀ |
|---:|---:|---:|---:|---:|:--:|---:|---:|---:|---:|
| 1y | 0.7576 | 4.51 | 0.707 | 3.00 | ✓ | +2.149↑ | +3.362 | +30.74 | -19.60 |
| 2y | 0.8838 | 9.03 | 0.830 | 3.01 | ✓ | +1.294↑ | +2.087 | +18.42 | -24.10 |
| 5y | 0.9596 | 22.57 | 0.925 | 3.02 | ✓ | +0.076↑ | +0.351 | +4.11 | -27.05 |
| 8y | 0.9785 | 36.12 | 0.952 | 3.04 | ✓ | -0.351↓ | -0.254 | -0.60 | -27.70 |
| 12y | 0.9891 | 54.17 | 0.968 | 3.06 | ✓ | -0.604↓ | -0.612 | -3.35 | -28.05 |

Reading: shorter bonds (low δ) → wL closer to the quantity share, smaller
φ, and **far milder magnitudes** (the monetary ŷ₀ collapses in size). A
realistic UK long-gilt duration (8–12y+) pushes δ→1, Q̄ᴸ and wL up, and the
amplification up — the long-debt-dominated FTPL regime (Cochrane).

## Sweep 3 — DATA-CONSISTENT market-value share wL (recalibrate χ̄, habitats)

χ̄ (quantity) set to hit each market-value wL; habitats scaled to keep the
same θ/χ̄ ratios as baseline. φ is inverted to hit ω̄=0.14.

| target wL | χ̄ (quantity) | θᴬ | θᴮ | φ | αᴬ | solve | checks |
|---:|---:|---:|---:|---:|---:|:--:|:--:|
| 0.930 | 0.3677 | 0.2604 | 0.5729 | **2.9** | 0.1873 | ✓ | ✓ |
| 0.700 | 0.0927 | 0.0656 | 0.1444 | **9.9** | 0.0472 | ✓ | ✓ |
| 0.500 | 0.0419 | 0.0297 | 0.0653 | **21.3** | 0.0214 | ✓ | ✓ |
| 0.353 | 0.0233 | 0.0165 | 0.0364 | **37.9** | 0.0119 | ✓ | ✓ |

Reading: anchoring to the **data** market-value share (wL=0.353 ⇒ χ̄≈0.023)
forces a huge φ — the spec's 'outcome (b)': a 14% wedge is hard to generate
from optimising habitat demand at a realistic (small-quantity) long position.
Keeping χ̄=0.353 as a quantity share (wL=0.93) gives the plausible φ≈3 of
'outcome (a)'. **This is the core calibration choice for the dissertation.**
