# §5.5 IRF run v2 — recalibrated to §5.2 headline ω̄ = 0.14

Re-run of `nk_ftpl_solve.py` at the new clean-window calibration. All other model features unchanged. Determinacy verified, all six structural-shock IRFs and the φ_π sensitivity figure regenerated.

---

## a. Calibration used

### Updated from the §5.2 clean-window run (`calibration/outputs_clean.xlsx`)

| Parameter | Old (ω̄ = 0.121) | New (ω̄ = 0.14) | Source |
|---|---:|---:|---|
| `omega_bar` | 0.121 | **0.14** | §5.2 headline, 4-year average ω̄ on 2021–2024 clean window |
| `wL` (long-bond share of debt MV) | 0.37 | **0.3532** | DMO QR Apr-Jun 2025 gilts-in-issue, nominal-weighted long share |
| `wS` (= 1 − wL) | 0.63 | **0.6468** | derived |
| `s_v` (s̄/v) | −0.03 | **−0.0334** | §5.2 4-yr avg primary balance / 4-yr avg v |
| `R_v` (R̄/v) | 0.04 | **0.0434** | derived: (1−β) − s̄/v at β = 0.99 |
| `chi_bar` (χ̄) | 0.37 | **0.3532** | inherited convention χ̄ = wL ("long-bond share of issuance", section5.md L88) |
| `eta` (η = δQ̄^L/(1+δQ̄^L)) | 0.954 | **0.956** | recomputed: Q̄^L_fund = β/(1−βδ) = 19.96; Q̄^L = (1+ω̄)·Q̄^L_fund = 22.75; η = δQ̄^L/(1+δQ̄^L) |

### Unchanged (per user spec)

| Parameter | Value | Note |
|---|---:|---|
| β | 0.99 | literature standard, inherited §3.4 |
| σ (IES inverse) | 1.0 | log utility |
| δ | 0.96 | inherited |
| θ (Calvo) | 0.75 | inherited |
| φ_π (Taylor) | 0.5 | baseline; sweep over {0, 0.3, 0.5, 0.8, 0.95} for sensitivity |
| ρ for all six AR(1) | 0.7 | uniform |
| κ (Phillips slope) | (1−θ)(1−βθ)σ/θ ≈ 0.0858 | derived |

### Inherited from prior run; NOT in §5.2 (flagged)

These NK consumption / fiscal share parameters do not appear in `outputs_clean.xlsx` and were not part of the §5.2 calibration. Kept at the prior-run values; should be re-examined if and when the §5.2 calibration is extended to cover them.

| Parameter | Value | Note |
|---|---:|---|
| `c_y` (c̄/ȳ) | 0.60 | inherited |
| `g_y` (ḡ/ȳ) | 0.40 | inherited |
| `tau_y` (τ̄/ȳ) | 0.37 | inherited |

---

## b. Blanchard–Kahn diagnostics

System: 18 variables, 8 predetermined (two bond-stock lags + six AR(1) states), 10 forward jumps.

| | Required | Found |
|---|---:|---:|
| Stable eigenvalues (|·| < 1) | 8 | **8** ✓ |
| Unstable eigenvalues (|·| > 1) | 10 | **10** ✓ |
| Unit-circle eigenvalues | 0 | 0 |

**BK satisfied.** The recalibrated system remains determinate. Eigenvalue moduli (ascending): 0.000, 0.700 (×6, AR(1) block), 0.867 (slowest stable mode), 1.022, 1.195, 25.81, plus seven unbounded — typical for the partially static rows.

The Klein–ordqz decomposition (`scipy.linalg.ordqz` on (A1, A0), sort='iuc') yields well-conditioned Z₁₁ and B̄_ss, so the policy function F (10×8) and state law M (8×8) are recovered cleanly.

---

## c. Impact-response table, h = 0

All 12 named endogenous variables × all 6 structural shocks. Each column is a unit innovation in the corresponding AR(1) state; each row is the contemporaneous (h = 0) percent-deviation response. Identical structure to the prior report's Appendix A.1.

| variable | ε_λ | ε_χ | ε_V | ε_g | ε_τ | ε_i |
|---|---:|---:|---:|---:|---:|---:|
| π̂ | −0.0306 | −0.0023 | −0.0306 | +0.0561 | +0.0089 | +0.1638 |
| î | −0.0153 | −0.0011 | −0.0153 | +0.0280 | +0.0045 | +1.0819 |
| ĉ | −0.0843 | −0.0063 | −0.0843 | −0.1085 | +0.0247 | −1.5678 |
| ŷ | −0.0506 | −0.0038 | −0.0506 | +0.3349 | +0.0148 | −0.9407 |
| Q̂^L | +1.0230 | −2.8295 | +1.0230 | +0.0526 | −0.0067 | −0.5968 |
| Q̂^L,fund | +0.7190 | −1.8910 | +0.7190 | +0.0507 | −0.0146 | −1.9759 |
| b̂^S | −0.0230 | −1.5478 | −0.0230 | −0.0526 | +0.0067 | +0.5968 |
| b̂^L | −0.0230 | +2.8295 | −0.0230 | −0.0526 | +0.0067 | +0.5968 |
| ω̂ | +0.3040 | −0.9386 | +0.3040 | +0.0019 | +0.0078 | +1.3790 |
| R̂ | +3.1716 | −6.7041 | +3.1716 | +0.0133 | +0.0559 | +9.8503 |
| v̂ | +0.3761 | −0.9531 | +0.3761 | −0.0383 | −0.0112 | −0.3653 |
| ŝ | 0.0000 | 0.0000 | 0.0000 | −0.4000 | +0.3700 | 0.0000 |

**Observational equivalence of ε_λ and ε_V.** λ̂^L and V̂_liab enter the model only through the sum (λ̂^L + V̂_liab) in row 5 (rent), row 10 (b^S dynamic), and row 11 (b^L dynamic), and have identical AR(1) persistence (ρ = 0.7). At unit innovation they produce identical IRFs — a model property, not a bug. Empirically distinguishing regulatory tightening (ε_λ) from balance-sheet growth (ε_V) requires separate priors on the two innovation variances.

---

## d. Headline ε_λ shock — featured dissertation values

The five variables featured in the §5.5 IRF figure, h = 0:

| Variable | Impact response |
|---|---:|
| π̂_0 | **−0.0306** |
| Q̂^L_0 | **+1.0230** |
| R̂_0 | **+3.1716** |
| v̂_0 | **+0.3761** |
| î_0 | **−0.0153** |

A unit positive regulatory-tightening shock (more captive long-bond demand) raises Q̄^L by ~1.0 pp, raises the captive rent R by ~3.2 pp, raises real-debt market value by 0.4 pp, and **lowers** inflation by 3 bp and the policy rate by 1.5 bp. The disinflationary impact-response is the signature §5 narrative: regulatory tightening expands fiscal space at the long end, the FTPL identity satisfies itself in part through downward inflation pressure, and the Taylor rule passes through to a lower nominal rate.

---

## e. Two non-obvious predictions

### (i) π̂_0 under the monetary shock

A positive interest-rate shock (ε_i, contractionary) produces **π̂_0 = +0.1638** — i.e. inflation rises on impact. This is the FTPL counterpart to the "price puzzle" but with a clean mechanism: the contractionary î shock raises the discounted fiscal financing burden in the FTPL identity, which has to be absorbed by an upward jump in the price level. The standard NK price-puzzle (which is an empirical artifact) is replaced here by a structural FTPL prediction. The sign survives the recalibration to ω̄ = 0.14 and is materially the same magnitude as under the prior calibration.

### (ii) |π̂_0| across the φ_π sweep, ε_λ shock

| φ_π | π̂_0 | \|π̂_0\| |
|---:|---:|---:|
| 0.00 | −0.02890 | 0.02890 |
| 0.30 | −0.03020 | 0.03020 |
| 0.50 | −0.03062 | 0.03062 |
| 0.80 | −0.02775 | 0.02775 |
| 0.95 | −0.01844 | 0.01844 |

**Non-monotone.** \|π̂_0\| rises from φ_π = 0 to a peak near φ_π ≈ 0.5, then falls as φ_π → 1. Every φ_π in the sweep satisfies BK (no determinacy frontier crossed in this range). The dissertation point — that the inflation impact of regulatory tightening is bounded and modest across a wide φ_π band, including the (still passive) value φ_π = 0.95 — holds at the new calibration.

---

## f. Diff summary vs. ω̄ = 0.121 run

The rent elasticity 1/ω̄ moves from **≈ 8.26 → ≈ 7.14** (a 13.6% decline). This coefficient sits in row 5 of the system (the rent equation R̂ = ω̂/ω̄ + λ̂^L + V̂_liab), so any shock that drives ω̂ flows through to R̂ at a smaller magnitude under the new calibration. **Direction of expected change** under recalibration:

- **R̂ impact response shrinks** for every shock that activates ω̂ (ε_λ, ε_V, ε_χ, ε_i). For ε_λ, R̂_0 = +3.17 is the post-recalibration value; with the same policy-function structure but the old 1/ω̄ ≈ 8.26, the analogous figure would have been larger.
- **ω̂ impact response itself is slightly larger.** The new ω̄ = 0.14 means a unit positive rent-share movement maps to a larger ω̂. For ε_λ, ω̂_0 = +0.30.
- **π̂, Q̂^L, v̂ impact responses are second-order changed.** These are buffered by the policy function across all 10 forward jumps; the recalibration tweaks the FTPL identity's coefficients on s̄/v and R̄/v but doesn't change the qualitative IRF pattern.
- **Sign pattern is preserved on every shock** — both the disinflationary ε_λ response and the FTPL-style ε_i price-puzzle survive. BK count (8/10) is unchanged.

Materially unchanged: shock-to-output, shock-to-consumption, and shock-to-policy-rate impact patterns; the ε_τ pure-Ricardian-equivalence near-irrelevance pattern (Δŝ = +0.37, almost no effect on real allocations); ε_χ portfolio-rebalancing pattern (large opposite-sign moves in b̂^L vs b̂^S).

Materially changed: R̂ magnitudes scale down by roughly the rent-elasticity ratio 7.14/8.26 ≈ 0.86 across the four "fiscal-stress" shocks.

---

## Artifacts

- `irfs/irf_lambda.pdf`, `irf_chi.pdf`, `irf_V.pdf`, `irf_g.pdf`, `irf_tau.pdf`, `irf_i.pdf` — six-shock IRF five-panel plots (π̂, Q̂^L, R̂, v̂, î over 40 quarters), drop-in identical format to the prior run.
- `irfs/sensitivity_phi_pi.pdf` — π̂(ε_λ) overlay for φ_π ∈ {0, 0.3, 0.5, 0.8, 0.95}.
- `irfs/irf_*.csv` — full 40-quarter IRF series for every shock (18 variables + b̂^S, b̂^L derived).
- `diagnostics.pkl` — A0, A1, B, F, M, P, Q_impact, eigenvalues, calibration dict, all IRF DataFrames.

### Minimal solver edits

1. Updated CAL dict (lines 84–107) — calibration constants only.
2. Extended `shock_to_label` to cover all six shocks (was three).
3. Added 0.95 to the φ_π sweep grid.

No changes to the solver logic, system builder, Klein decomposition, or IRF iteration.

### Non-stationarity notes

At h = 39, four state variables remain above the 0.01 tolerance under the ε_i shock (b̂^S_lag, b̂^L_lag, Q̂^L, Q̂^L_fund — all around 0.011–0.014). This is the slowest stable mode at modulus 0.867 not fully decayed over 40 quarters under the monetary shock, identical in pattern to the prior run. Not a determinacy issue.
