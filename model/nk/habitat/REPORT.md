# Microfounded Captive-Habitat NK-FTPL — implementation report (v1)

**Folder:** `nk/habitat/`  ·  **Date:** 2026-06-01  ·  **Author of code:** Claude (for L. Leturia)

This implements the *microfounded* spec `habitat_nk_spec.pdf` ("A Captive-Habitat
FTPL Model Embedded in New Keynesian Structure") — the two-agent preferred-habitat
model that replaces the Entrega III reduced-form mandate. It is built alongside,
not on top of, the existing reduced-form solver `../nk_ftpl_solve.py`; the
Klein/QZ machinery is reused (spec §6.1: "drop-in reuse … only the matrices
change").

**You gave me freedom to make judgment calls — every one is logged in §3 below.**
Read §3 (judgment calls) and §6 (the one genuine open issue) first; those are
where your eyes are most needed.

---

## 1. What runs, and how

```
python steady_state.py     # Section 4: SS solve, φ-inversion, the six 4.4 checks
python run_habitat.py       # full pipeline: SS → linearise → Klein → IRFs → report
```

Files:
| file | role |
|---|---|
| `params.py` | calibration dataclass; conventional params + the structural judgment calls |
| `steady_state.py` | numerical binding-mandate steady state (§4.2), φ-inversion (§4.3), six §4.4 checks |
| `linearize.py` | log-linearised system (§5), compact form, all coefficients from the SS |
| `klein.py` | Klein (1999) generalized-Schur solver (reused from Entrega III) |
| `run_habitat.py` | driver: BK diagnostics, headline IRF + four signs, two regime diagnostics, φ→0 counterfactual, ω̄ & ψ sensitivity, figures/CSVs/pickle |

Outputs land in `figures/hab_*.png`, `irfs/hab_irf_*.csv`, `hab_diagnostics.pkl`.

---

## 2. Headline results (all reproducible from `run_habitat.py`)

### 2.1 Steady state — the load-bearing computation (§4). **All six §4.4 checks PASS.**

| object | value | note |
|---|---:|---|
| **φ (inverted for ω̄=0.14)** | **3.02** | moderate, plausible ⇒ spec "outcome (a)": the microfoundation rationalises the wedge |
| Q̄ˢ, Q̄ᴸ, Q̄ᴸᶠᵘⁿᵈ | 0.960, 22.75, 19.96 | Q̄ᴸ = (1+ω̄)Q̄ᴸᶠᵘⁿᵈ by construction |
| αᴬ, αᴮ | 0.180, 0.526 | both **below** habitat (θᴬ=0.25, θᴮ=0.55) — distortion active |
| X̄ (rent, eq 13) | +0.0134 | **positive** (Prop. 1 neighbourhood) |
| determinant bᴸᴬbˢᴮ−bˢᴬbᴸᴮ | −0.073 | **negative** near the symmetric reference, as §4.4-6 predicts |
| Ψ̄ (revaluation, eq 14) | 0.453 | tracked separately from X̄ (the spec's distinct objects) |
| v̄, s̄, τ̄ | 3.998, +0.0266, 0.227 | v̄/ȳ ≈ 4 (≈100% of annual GDP) |
| wˢ, wᴸ | **0.074, 0.926** | structural — **see §6, this is the key finding/issue** |

Two strong internal-consistency signals (not imposed, they fall out):
- the **short-Euler tie** ξ̄ˢᴬ = ξ̄ˢᴮ holds to 6e-17 (the cross-agent restriction of §4.2);
- the **PV identity** v̄(1−β) = s̄ + X̄ holds to 2e-17 — i.e. the rent X̄ computed
  from eq (13) independently equals what the augmented FTPL identity requires.
  This cross-validates the rent formula against the budget+Euler block.

φ stays in **[2.6, 4.5]** across the whole ω̄∈[0.12, 0.21] sensitivity band — plausible throughout.

### 2.2 Linearisation & determinacy — **all three spec code-checks PASS**

| spec check | result |
|---|---|
| row-13 inflation coefficient −(wˢ+wᴸ) = −1 (exact) | **−1.0000** ✓ |
| relative-wealth root at 1−ε (LANDMINE 1) | **0.999 = 1−ψ** ✓ |
| Blanchard–Kahn count #unstable = #jumps | **9 stable / 11 unstable** ✓ |
| determinacy fails at φπ=1 (Leeper boundary) | **BK fails at φπ=1, holds on [0,0.95]** ✓ |
| IRFs invariant as ψ→0 (closing device) | π̂₀ moves <1% over ψ∈{1e-3,1e-4,1e-5} ✓ |

### 2.3 Headline λ̂ᴸ shock, four sign predictions (§6.3) — **conditional, as the spec warns**

| prediction | impact value | matches spec? |
|---|---:|---|
| inflation falls (π̂₀<0) | −1.30 | ✓ |
| rent rises (X̂₀>0) | +3.38 | ✓ |
| real debt value rises (v̂₀>0) | +1.02 | ✓ |
| short rate falls (î₀<0) | −0.65 | ✓ |
| long price rises (Q̂ᴸ₀>0) | **−0.31** | **✗ — falls** |

Four of five match. The long-price sign **flips**, and the monetary "price-puzzle"
regime diagnostic also flips (contractionary money is *disinflationary* here,
π̂₀=−2.5, vs the +0.16 of Entrega III). **These are not bugs** — see §6. The spec
(LANDMINE 3, §6.3) explicitly says the four signs "are not automatic in the
microfounded model … verify numerically … every outcome is reportable."

### 2.4 φ→0 counterfactual (§6.5) and sensitivity
The habitat channel's contribution (headline minus φ→0) is real and sizeable on the
rent (+1.44) and the long price (−0.32). Full numbers in the console output and
`figures/hab_counterfactual_phi.png`.

---

## 3. Judgment calls (you have freedom — here is exactly what I chose)

The spec leaves three explicit DECISIONs plus several structural parameters open.

**DECISION 1 (closing device).** Spec recommends a utility cost. I used the
mathematically equivalent **own-wealth-elastic AR(1)** for the relative-wealth
state WtA (variant ii), which *guarantees* the root is exactly 1−ψ. WtA is driven
by the long-bond **revaluation** channel (a mandate tightening raises Q̄ᴸ, revaluing
the long-habitat agent B up relative to A) and is a **benign, non-feeding-back**
state in v1 (it satisfies the spec's "sole role is to move the root to 1−ε" and the
ψ→0 invariance test). *Why benign:* under DECISION 2 option 1 the A–B distribution
is a sideshow; the consumption-differential driver I first tried couples WtA to a
near-unit forward mode and breaks the BK count, so I drive it from exogenous states
instead. **Full two-way relative-wealth dynamics (WtA from A's exact budget,
feeding back) is a flagged v2 item.**

**DECISION 2 (which Euler is the IS curve).** I used **option 1, the recommended
baseline**: agent A's short Euler is the IS curve; B's consumption is residual via
the resource constraint; B's flow budget is dropped (redundant by Walras's law).
This is what makes the system square (it resolved an initial 21-equations-for-20-
variables over-determination). A's SDF prices the government debt, exactly as the
spec wants.

**DECISION 3 (what to substitute out).** I built the **compact form**: aggregate
current bond stocks follow the captive-demand issuance rule b̂ᴸ = λ̂ᴸ+V̂ˡⁱᵃᵇ−Q̂ᴸ
(the Entrega III closure, reinterpreted: the government sizes long issuance to
captive demand), so the augmented FTPL identity stays the independent price-level
equation and the structural rent X̂ enters price determination. The agent-level
portfolio objects (α̂ᴬ, the rent determinant) are reconstructed analytically from
the retained variables. *The redundant full form (a correctness cross-check the
spec suggests) is not yet built — v2 item.*

**Structural parameters not pinned by the spec** (set here, all defensible):
- μᴬ=μᴮ=0.5 (equal populations);
- θᴬ=0.25, θᴮ=0.55 (short/long habitats; θ̄=0.40 > χ̄=0.353 so both agents are
  pushed below habitat and the wedge is positive — the §4.1 distorted point);
- D̄=0.459 (aggregate real debt), chosen so v̄/ȳ≈4; pure level normalisation;
- ḡ/ȳ=0.20; income symmetric yᴬ=yᴮ=ȳ;
- **closure of the wealth-level indeterminacy:** W̄ᴬ=W̄ᴮ=D̄ (equal per-capita
  wealth), which is automatically consistent with market clearing.

**Two derivations where I departed from the spec's schematic, deliberately:**
1. **Row-12 rent, ĉᴬ coefficient.** The §5 table writes `−σĉᴬ`; the explicit eq
   (13) has X ∝ (cᴬ)^{+σ}, i.e. **+σĉᴬ**. I followed eq (13) (the `(cᴬ)^{−σ}` is
   in the *denominator*). I read the table's `−σ` as a sign typo. **Please confirm.**
2. **Wedge-law determinacy (the §6.2 subtlety).** Agent A's long *share* responds
   to the contemporaneous long *price* (Q̂ᴸ↑ → α̂ᴬ↓ → wedge widens). Inside the
   *forward* wedge law this self-reference pulls the wedge's root from 1/(βδ)≈1.05
   below 1 and creates indeterminacy. In the **wedge law only** I drive the wedge by
   the mandate/wealth reallocation and drop the own-price feedback (kept everywhere
   else — rent, clearing, shares). This is exactly the determinacy issue §6.2
   flags; the full self-referential treatment is a v2 item.

---

## 4. Mapping to the spec's Section-5 table (what's implemented)

20 variables: 9 predetermined (bˢ_lag, bᴸ_lag, WtA, six AR(1)), 11 jumps
(ĉᴬ, ĉᴮ, ŷ, π̂, î, Q̂ᴸ, Q̂ᴸᶠᵘⁿᵈ, ω̂, X̂, v̂, ŝ). Rows R0–R19 in `linearize.py`
correspond to the §5 table:

- R0 IS (A short Euler) · R1 NKPC · R2 Taylor · R3 fundamental price · R4 wedge
  identity · **R5 wedge law (ω̂ now endogenous & forward, driven by A's long
  habitat wedge — replaces the reduced-form rent identity)** · **R6 structural
  rent X̂ (eq 13, front factor αᴬ/(αᴬ−θᴬ), determinant elasticities)** · R7 real
  debt value · R8 augmented FTPL identity (with X̄/v̄) · R9 surplus · R10 resource/
  aggregation · R11–R12 bond-lag laws · **R13 relative-wealth law (closing device)**
  · R14–R19 six AR(1) laws.

The genuinely *new microfounded content* vs the reduced form is in R5, R6, R13 and
the agent reconstruction feeding them.

---

## 5. Determinacy & sign mechanics (why the signs are what they are)

Determinacy is clean: the FTPL root 1/β≈1.01, the two asset-pricing roots ≈1.04 and
≈1.07 (complex pair), plus six AR(1) roots at 0.7 and the relative-wealth root at
0.999. The §6.2 "small core" analytic programme is **not** attempted; only QZ
eigenvalues are reported (a v2 aspiration).

The flipped signs (long price falls; contractionary money is disinflationary) trace
to **one structural fact: wᴸ=0.926** (§6). With 92.6% of debt market value in a
~25-quarter-duration perpetuity, a monetary contraction crashes the long-bond price
(Q̂ᴸᶠᵘⁿᵈ₀=−2.8), and that **long-debt revaluation channel dominates the classic
FTPL discounting channel**, so the price level must *fall* to restore real debt
value. This is the known "FTPL with long-term debt" result (Cochrane): long maturity
can flip the impact sign of inflation. It is economically coherent, and the spec
anticipates exactly this kind of conditional outcome.

---

## 6. The one genuine open issue — quantity vs market-value long share (please read)

**The maturity composition χ̄ is a *quantity* share** (eq 2: b̄ᴸ=χ̄(b̄ˢ+b̄ᴸ), fresh-
bond-equivalent units). **The data anchor wᴸ=0.353 (DMO, your §5.2 memo) is a
*market-value* share.** With a perpetuity priced at Q̄ᴸ=22.75, these are wildly
different objects:

- Headline run, **χ̄=0.353 read as a quantity share** (inheriting Entrega III's
  `χ̄ = wᴸ` convention, which conflated the two): structural **wᴸ=0.926**, **φ=3.0
  (plausible)**, but long-debt-dominated ⇒ the sign flips above.
- To match the **data market-value wᴸ=0.353** you need a tiny quantity share
  **χ̄≈0.0233**. Re-solving there gives **φ≈115** (and the SS barely converges) —
  which is precisely the spec's **"outcome (b): a 14% wedge is hard to generate from
  optimising habitat demand."**

So **both** outcomes the spec anticipated (§4.3) actually occur, and *which* you
report is a genuine modelling/calibration choice you need to make:
1. keep χ̄=0.353 as a quantity share (plausible φ, but long-debt-dominated dynamics
   with flipped signs), **or**
2. recalibrate χ̄≈0.023 to the data market value (data-consistent dynamics, but
   φ≈115 — the "reduced form was baking in more distortion than micro-behaviour
   supports" finding), **or**
3. shorten δ so the perpetuity's duration/price is smaller and the quantity and
   value shares are closer (changes a parameter the spec lists as fixed).

My recommendation: **report this as a result, not a nuisance.** It sharpens the
dissertation — the microfoundation *exposes* a tension the reduced form hid. The
headline numbers above use option 1.

Secondary consequence: magnitudes are large (ŷ₀≈−11 for a *unit*, i.e. 100%, λ̂ᴸ
innovation), amplified by wᴸ=0.926 and the long duration. IRFs scale linearly, so a
1-s.d. (≈1%) shock gives 1% of these. Still, the linear approximation is stretched;
a smaller, more realistic shock size for the figures is worth setting.

---

## 7. Confidence levels (be appropriately skeptical)

| component | confidence | basis |
|---|---|---|
| Steady state + φ-inversion + §4.4 checks | **high** | 6/6 checks pass; tie & PV identity hold to 1e-16; φ-band sane |
| Klein/QZ solve, BK count, −1 coeff, 1−ε root | **high** | exact code-checks pass; reproduces φπ=1 boundary |
| Wedge law R5, rent R6 structural coefficients | **medium-high** | derived from eq (9),(13); one documented determinacy choice + the +σ vs −σ reading |
| Aggregate-issuance closure (E3-inherited) | **medium** | leading-order; loses the flow-budget micro-detail (kept FTPL so X enters price) |
| Relative-wealth dynamics R13 | **medium-low (v1 benign)** | satisfies the root/invariance requirements but does not yet feed back (DECISION-2-opt-1 makes this OK; full version = v2) |
| Sign/magnitude *economics* | **the signs are real, the calibration needs your call** | see §6 |

---

## 8. Scoped v2 work (in priority order)

1. **Resolve the χ̄ quantity-vs-value tension (§6).** This is the single most
   important decision; it changes the headline dynamics.
2. Two-way relative-wealth dynamics: derive WtA from agent A's exact flow budget and
   let it feed back (drop the v1 benign-appendage simplification).
3. The §6.2 analytic determinacy programme (reduce to the {π̂, v̂, ω̂} core), instead
   of only QZ eigenvalues.
4. The redundant full (agent-level) form as a correctness cross-check vs the compact
   form (DECISION 3).
5. Re-examine the wedge-law own-price feedback (the §6.2 simplification in §3) with a
   proper (lagged-share or simultaneous) treatment.
6. Confirm the row-12 `+σĉᴬ` vs `−σĉᴬ` reading against the [Hab] source.
```

---

# ADDENDUM (session 2) — calibration fix for problem #1, Decision A, and sweeps

New code: `calibrate.py` (duration→δ and χ̄↔wL helpers), `sweeps.py`
(`sweeps_output.md`). `linearize.py` now has an `agg_closure='partial'` mode with
an `accom` (accommodation) parameter; **the default is now `accom=0.0` = Decision A.**

## 9. Problem #1 — the principled fix (literature-grounded)

**The tension.** χ̄ (spec eq 2) is a *quantity* long-share; the data anchor
wL=0.353 (DMO) is a *market-value* share. With Q̄ᴸ≈22.75 they differ enormously —
reading χ̄=0.353 as quantity gives wL=0.926. Entrega III's `χ̄=wL` convention
silently conflated them.

**What the literature does.** In macro-finance / FTPL the geometric consol's decay
δ is calibrated to a **Macaulay-duration target** (geometric consol: duration
= 1/(1−βδ) quarters), and the present-value identity values debt at **market
value**. So the observables are (i) the long-bond duration and (ii) the
market-value maturity share. References:
- Rudebusch & Swanson (2008/2012), *"The bond premium in a DSGE model…"* — the
  geometric-consol device; δ picked to hit a target Macaulay duration.
- Cochrane (2021), *"A fiscal theory of monetary policy with partially-repaid
  long-term debt"* (NBER w26745) and **Corhay, Kung & Morales (2023), "Discount
  Rates, Debt Maturity, and the Fiscal Theory," *Journal of Finance*** — long
  maturity makes debt-revaluation dominate; **a rate hike can be disinflationary
  on impact** (see §11).

**The fix (implemented in `calibrate.py`):** anchor the two *observables* and let
χ̄ and φ float:
- δ ← duration target: `δ = (1 − 1/D)/β` (D in quarters);
- wL ← DMO market-value share (0.353);
- χ̄ ← implied quantity share `χ̄ = wL/[f(1−wL)+wL]`, `f = 1+δQ̄ᴸ`;
- φ ← inverted to hit ω̄=0.14 (unchanged).

## 10. The sweeps (`sweeps_output.md`) — what they show

**Sweep 3 (the core calibration choice).** Anchoring to the data wL forces a large φ:

| target wL | χ̄ (quantity) | φ | reading |
|---:|---:|---:|---|
| 0.93 (χ̄ read as quantity) | 0.368 | **2.9** | spec "outcome (a)": plausible |
| 0.70 | 0.093 | 9.9 | |
| 0.50 | 0.042 | 21.3 | |
| **0.353 (DMO data)** | **0.023** | **37.9** | spec "outcome (b)": a 14% wedge is hard to micro-found |

This is a clean, reportable dichotomy and **the single calibration decision you
must make.** (The exact φ at wL=0.353 depends on how habitats are scaled — 38 here
with proportional scaling, ~115 with fixed habitats — but the message is robust:
data-consistent wL ⇒ large φ.)

**Sweep 2 (duration).** Matching a *realistic* UK long-gilt duration (8–12y+) pushes
δ→1, Q̄ᴸ and wL up, and **deepens** the long-debt-dominated regime — it does not
rescue the signs. Short bonds (1–2y) give milder magnitudes but an even larger
λ-output response. There is no duration that tames everything.

## 11. Decision A — implemented, and what it does

`agg_closure='partial'`, `b̂L = accom·(λ̂L+V̂liab) − Q̂L`. **accom=1** is the Entrega
III rule (aggregate long supply expands with the mandate; agent A is never squeezed
→ weak wedge → long price falls). **accom=0** (the new default) is Decision A: the
government does **not** accommodate the mandate with new issuance, so the mandate
purely **redistributes** the aggregate long stock from A to B, squeezing A off
habitat and widening the wedge. Determinacy holds for all accom (the −Q̂L term
carries the asset-price root).

**Sweep 1 — accom from 1→0 (baseline calibration), λ̂L shock:**

| accom | Q̂ᴸ₀ | π̂₀ | v̂₀ | λ-output ŷ₀ |
|---:|---:|---:|---:|---:|
| 1.00 (E3) | −0.31 ↓ | −1.30 | +1.02 | −10.9 |
| 0.50 | −0.12 ↓ | −0.48 | +0.37 | −3.5 |
| **0.00 (Decision A)** | **+0.07 ↑** | +0.34 | −0.28 | **+4.0** |

**Decision A fixes the two things you flagged:** the long price now **rises** on a
tightening, and the insane λ-output collapse shrinks by ~3×.

**But it exposes a real result, not a tuning failure:** at accom=0 the *inflation*
and *debt-value* signs flip. The reason is mechanical. On impact the debt-revaluation
identity is `v̂₀ = −π̂₀ + wᴸη·Q̂ᴸ₀ + (small rent)`, and the FTPL fixes v̂₀ ≈ const
because **the rent is tiny relative to debt: X̄/v̄ ≈ 0.34%.** So `Q̂ᴸ₀↑ ⟹ π̂₀↑`.
**You cannot get "long price rises" *and* "inflation falls" simultaneously unless the
rent is a materially larger share of debt backing.** With UK debt ≈ 400% of
quarterly GDP and a 14% wedge, it isn't. *This is arguably the sharpest finding of
the microfoundation:* the captive rent is a real but **second-order** fiscal-backing
margin; the price level is governed by long-debt revaluation.

## 12. The monetary → inflation sign: keep it, and cite

The contractionary-money-is-disinflationary result is **the documented FTPL-with-
long-term-debt mechanism** (Cochrane 2021; Corhay–Kung–Morales 2023). The
bond-revaluation channel dominates the discounting channel, so a rate hike crashes
the long-bond price, real debt value falls, and the price level falls to restore it.
**Recommendation: keep it and cite the long-debt FTPL literature** — it distinguishes
your model from the short-debt benchmark and is internally consistent.

## 13. STILL OPEN / flagged (needs your call or a v2)

1. **The core calibration choice (Sweep 3):** report χ̄ as a quantity share (φ≈3,
   "outcome a", long-debt-dominated dynamics) or anchor to the data wL (φ≈38–115,
   "outcome b"). My recommendation: **report the dichotomy itself** — it is a result.
2. **The monetary output response is implausibly large** (ŷ₀≈−27 for a unit, i.e.
   ~−27% for a 1% shock) and is **not** fixed by Decision A or duration. Root cause:
   pure active-fiscal/passive-money + long-dominated debt + a *small* rent gives an
   essentially unanchored, hyper-elastic price level. **Likely v2 fix:** allow a
   modest surplus-feedback to debt (partial-Ricardian damping), or revisit how
   strongly money is passive. This is the most important remaining modelling issue
   after the calibration choice.
3. The "rent is small" finding (§11) suggests revisiting the captive-sector size μᴮ
   and whether the rent X̄/v̄ can be made first-order without abandoning ω̄=0.14.

---

# ADDENDUM (session 3) — taming the hyper-elastic price level

New `linearize.build` knobs (all default 0, baseline unchanged): `gamma_v` (Bohn
contemporaneous debt feedback), `gamma_rep` (Cochrane s-shaped / partial-repayment
on lagged debt), `theta_tp` (Vayanos–Vila term premium).

## 14. Leeper (1991) active/passive — what is and isn't binary

The *regime* is either/or (exactly one active + one passive authority for a unique
equilibrium). But **"passive fiscal" is a threshold, not a point**: a surplus rule
`s=γ·b+…` is active iff γ < (1−β)/β. So a *nonzero* γ below that threshold is still
active fiscal (still FTPL, still determinate under passive money) — it only changes
the magnitude/persistence. "Partial Ricardian" here means exactly that, not a blend
of regimes. And **Cochrane's s-shaped surplus is orthogonal to the γ classification**
— it shapes the *time-series of surplus innovations* (deficit-then-repayment), not
the contemporaneous feedback, so it sidesteps the Leeper threshold entirely.

## 15. What tames the hyper-elasticity — tested

**The problem is genuine, not a shock-scaling artifact.** At a shock that moves the
equilibrium short rate just **25bp**, output still falls **≈27%** (multiplier ~100×).
Mechanically `ŷ ≈ π̂/κ`: FTPL pins a large π̂ (from the long-bond price crash) and the
flat Phillips curve turns it into enormous output.

| lever | impact on hyper-elasticity | verdict |
|---|---|---|
| **stickier prices** (θC↑, κ↓) | π̂ **unchanged**; output **explodes** (ŷ≈π̂/κ) | **wrong lever** — π̂ is fiscally pinned, not PC-pinned |
| **Bohn feedback** `gamma_v` (on current v̂) | negligible on impact | weak; impact is asset-price-driven |
| **s-shaped surplus** `gamma_rep` (on lagged debt) | negligible on impact; reshapes the *path* | Cochrane smoothing of the path/puzzles, not the jump |
| **V-V term premium** `theta_tp` | monetary output −27%→−21.5% (θ=0.5), →−9.6% (θ=1); strengthens Q̂ᴸ↑ | **most useful single lever** |
| **lower long-debt dominance** (problem #1, data-consistent χ̄) | reduces π̂ at the source, but φ→large | the fundamental fix; trades off vs φ plausibility |

**Bottom line:** the hyper-elasticity is the long-debt-dominated FTPL regime. The
term premium helps and is on-theme; the deepest fix is reducing long-debt dominance.

## 16. The correct Vayanos–Vila specification (proposal)

**Structure (V-V 2021; Greenwood–Vayanos 2014).** Two investor types: *arbitrageurs*
(trade across maturities, risk-averse, finite risk-bearing capacity) and
*preferred-habitat* investors (maturity-specific demand). Map to this model:
**agent A = arbitrageur; agent B + the mandate = habitat demand.**

**Arbitrageur problem (mean-variance over wealth):** A maximises
`E_t[W^A_{t+1}] − (a/2)Var_t[W^A_{t+1}]`. The FOC prices the long bond with a
duration-risk premium:

> **Q^L_t = E_t[M^A_{t+1}(1+δQ^L_{t+1})/π_{t+1}] + ξ^{L,A}_t − τp_t ,**
> **τp_t = a · Var_t(R^L_{t+1}) · z^A_t ≈ a·D²·σ_r² · (μ_A b^{L,A}_t)**

where z^A_t is A's long-duration exposure, a its risk aversion, D the bond's
duration, σ_r² the short-rate variance. **Linearised:** `τ̂p_t = θ_tp · b̂^{L,A}_t`,
with **θ_tp = a·D²·σ_r²** — exactly the reduced form prototyped here.

**The two V-V results this delivers:**
1. *Demand compresses the premium (financial repression):* a mandate tightening
   forces B's long holding up; market clearing makes A hold less (b̂^{L,A}↓); the
   premium A requires falls; the long price rises / long rate falls. This is the
   dissertation's own mechanism, now with a risk-based price.
2. *The long rate underreacts to the short rate:* with finite risk-bearing (a>0)
   and price-elastic habitat demand (the ξ^L penalty), arbitrageurs don't fully
   arbitrage short-rate moves into the long rate — stabilising Q^L and damping the
   monetary hyper-elasticity (confirmed: θ_tp↑ shrinks the monetary output response).

**Caveat — to first order a term premium is certainty-equivalent (zero).** A genuinely
*risk-based, time-varying* premium needs either (a) the reduced-form `θ_tp` used here
(tractable, recommended for v1), or (b) a higher-order / Epstein–Zin + stochastic-
volatility solution (Rudebusch–Swanson 2012) that endogenises σ_r² and a — a larger
v2. Recommended: calibrate θ_tp to a target steady-state term premium (e.g. the
average 10y-3m gilt term premium) and report sensitivity.

## 17. Recommended configuration going forward

For the dissertation's headline runs: **Decision A** (accom=0) **+ a calibrated
Vayanos–Vila term premium** (θ_tp to a data term premium) **+ a modest s-shaped
surplus** (γ_rep small, for path-smoothing and puzzle-avoidance) **+ realistic shock
sizes** (report responses per 1% regulatory / 25bp monetary, not per unit). The
residual hyper-elasticity is the long-debt FTPL regime itself — disclose it and lean
on the V-V channel + the long-debt-FTPL literature (Cochrane; Corhay–Kung–Morales).

---

# ADDENDUM (session 4) — term-premium calibration from Bloomberg gilt data

Data source: `calibration/Bloomberg_Data_Pull (1).xlsx`, sheet `A_B_E` (gilt
zero-coupon yields GUKG1–GUKG30, bank rate UKBRBASE, daily 2004-12 → 2025).

**Empirical term-premium proxies (average long-minus-short spread):**

| sample | 5y−bank | 10y−1y | 10y−bank | 20y−bank |
|---|---:|---:|---:|---:|
| full 2004–2025 | 0.36% | 0.90% | 0.83% | 1.27% |
| clean 2021–2024 | −0.18% | −0.06% | −0.03% | 0.36% |

(The clean window is curve-inverted, so the **full-sample** average is the right
term-premium anchor.) Short-rate quarterly-change volatility σ_r ≈ 0.45pp (a
cross-check for the structural a·D²·σ_r² form; not needed for the reduced form).

**Mapping to θ_tp.** A return premium maps to the log price through duration
(`dlnQ ≈ −D·τp`), and the V-V premium is `τp = a·D²·σ_r²·z`, so the linearised
price-sensitivity is **θ_tp = D · τ̄p** (duration × steady-state per-period term
premium). With D ≈ 20.2q (model δ=0.96 ⇒ 5.0y duration) and τ̄p ≈ 1.0%/yr:

> **θ_tp = 20.2 × (0.010/4) ≈ 0.05**  (sensitivity band **[0.025, 0.064]** for
> τ̄p ∈ [0.5%, 1.27%]/yr).

This is now the **headline default** (`Params.theta_tp = 0.0505`), with Decision A.

**What the calibrated premium does (impact, realistic shock sizes):**
- λ̂L = +1% tightening: Q̂L **+0.15%** (vs +0.07% without the premium — it more
  than doubles the long-price-rises / financial-repression effect), π̂ +0.47%,
  v̂ −0.34%, ŷ +4.95%.
- monetary, 25bp equilibrium-rate move: π̂ −2.38%, ŷ **−25.2%** (≈ unchanged from
  −27%).

**Verdict.** The empirically-sized term premium **reinforces the headline
repression channel** (long price rises more on a tightening — good for the thesis)
but is **far too small to cure the monetary hyper-elasticity**. Caveat noted in §16:
a genuinely risk-based, time-varying premium needs a higher-order/Epstein–Zin
solution; the reduced-form θ_tp here is the v1 stand-in (per your instruction not to
build the higher-order version yet). The hyper-elasticity remains a long-debt-FTPL
property to be addressed via the problem-#1 calibration choice, not the premium.

**Duration caveat (ties back to problem #1).** The model's δ=0.96 implies a **5y**
duration, but the captive/LDI demand is for **15–30y** gilts. Matching the long-end
duration would raise D (→ larger θ_tp, ~0.2) but also deepen the long-debt dominance
and the hyper-elasticity. This is the same quantity/maturity tension as problem #1.

---

# ADDENDUM (session 5) — the two calibrations, side by side

`compare_calibrations.py` (→ `figures/hab_compare.png`). Both columns use the
**headline config** (Decision A, accom=0, + the calibrated V-V term premium
θ_tp≈0.05); the ONLY difference is how χ̄ is read.

| | **Cal A: χ̄ = quantity** | **Cal B: data market-value** |
|---|---:|---:|
| χ̄ (quantity long-share) | 0.353 | 0.023 |
| market-value wL | 0.926 | 0.353 |
| θ^A, θ^B (habitats) | 0.25, 0.55 | 0.017, 0.036 |
| **φ (inverted for ω̄=0.14)** | **3.0 — plausible (outcome a)** | **37.9 — large (outcome b)** |
| α^A | 0.180 | 0.012 |
| rent X̄/v̄ | 0.34% | 0.11% |
| §4.4 checks / BK | pass / OK | pass / OK |
| **λ̂L +1%:** Q̂L | +0.15% | +0.72% |
| &nbsp;&nbsp;&nbsp;&nbsp; π̂ | +0.47% | +1.20% |
| &nbsp;&nbsp;&nbsp;&nbsp; v̂ | −0.34% | −0.96% |
| &nbsp;&nbsp;&nbsp;&nbsp; ŷ | +4.95% | +8.26% |
| **monetary 25bp:** π̂ | −2.38% | −1.03% |
| &nbsp;&nbsp;&nbsp;&nbsp; ŷ | **−25.2%** | **−8.7%** |

**The result to report.** The data-consistent maturity (Cal B) **cuts the monetary
hyper-elasticity ≈3×** (−25%→−8.7%) because debt is no longer long-dominated, **but
the wedge then needs an implausible φ≈38**. Cal A keeps a believable φ≈3 but pays
with severe hyper-elasticity. Both stay determinate and pass all §4.4 checks. The
inflation-rises-on-a-tightening sign persists in both (the small-rent property,
§11). Even Cal B's −8.7% output for a 25bp shock is ~10× empirical — the
hyper-elasticity is reduced, not removed.

**Interpretation for the dissertation:** the microfoundation forces a genuine
trade-off — you cannot simultaneously have (i) a *plausible* habitat penalty, (ii)
*data-consistent* debt maturity, and (iii) the 14% *market-value* wedge. Generating
a 14% market-value wedge from a *realistic (small) long-quantity* captive position
requires a strong penalty. This is the sharp, honest contribution of moving from the
reduced form to the microfoundation.

