# Sovereign Bond Convenience Yields as Financial Repression
### Price and Real Effects

![Python](https://img.shields.io/badge/Python-numpy%20%2F%20scipy-3776AB?logo=python&logoColor=white)
![Solution](https://img.shields.io/badge/Solution-QZ%20%2F%20gensys-8A2BE2)
![Field](https://img.shields.io/badge/Field-Macro%20%26%20Finance-2E7D32)

Governments can manufacture demand for their own debt through financial regulation — for instance, prudential rules that force pension funds and insurers to hold long-dated government bonds. That captive demand bids bond prices up and quietly relaxes the government's budget constraint. This dissertation asks:

> **Can financial regulatory policy move inflation and real activity — not through interest rates, but through the government's budget constraint?**

The central observation ties two separate literatures together: the *convenience yield* that macro-finance measures on safe sovereign debt and the *repression rent* a government extracts through regulation are the **same price wedge read through two lenses** — one an exogenous demand for safety, the other the endogenous outcome of policy.

---

## Approach

**A micro-founded model** built from three ingredients:
- **Intermediary Asset Pricing** — the price wedge on long bonds is the shadow value of a binding duration-matching mandate.
- **Fiscal Theory of the Price Level** — the rent enters the government's valuation identity as genuine fiscal backing alongside the primary surplus (an "augmented FTPL identity").
- **New Keynesian rigidities** — sticky prices let movements in the price level carry real effects.

**Three results** fall out:
- *Proposition 1* — regulation relaxes the budget constraint (a pure accounting property; no rigidity or particular regime required).
- *Proposition 2* — holding inflation fixed, the rent substitutes one-for-one for the primary surplus.
- *Proposition 3* — under fiscal dominance, a tighter mandate lowers the price level, with output bearing the adjustment through sticky prices.

**Calibrated to UK gilt data** and solved by a generalized-Schur (QZ) decomposition in the Sims (2002) form. The results trace impulse responses to a regulatory shock, the repression-vs-surplus frontier, and a fiscal- vs monetary-dominance comparison.

---

## Key findings

- **Regulation relaxes the budget constraint — that part is just accounting.** Whether the extra backing reaches the price level is a separate question, settled by equilibrium selection.
- **Same rent, opposite outcome, depending on the regime.** Under fiscal dominance (passive money) a tighter mandate lowers the price level and drags output down; under monetary dominance the primary surplus absorbs the rent and prices are unmoved. The price effect is a property of the monetary–fiscal regime, not of repression as such.
- **Deliberately small, by construction.** The model prices a single instrument (duration-matching mandates) on a single tranche (~a third of the stock) at a conservative 23 bp wedge floor — so the ~0.6% long-run price-level move and ~0.19%-of-debt fiscal space from a 10% tightening are a *lower bound* on the fiscal pull of repression. The contribution is the channel's coherence and regime-dependence, not its magnitude.

---

## Repository structure

```
├── model/       # gensys-style solver, calibration, steady state
├── figures/     # IRFs, fiscal-space frontier, regime contrast, wedge charts
├── data/         # UK gilt yields, spreads, sector holdings
└── paper/       # full dissertation (PDF)
```
*(adjust to match the scripts as you add them)*

---

## Data

UK Debt Management Office (gilt maturity structure) · ONS & OBR (public finances) · Bank of England (gilt yields, sector holdings, the September 2022 LDI episode) · Bloomberg / Vanguard (15+ year gilt duration).

---

## Tech stack

- **Python** — model construction, steady state, generalized-Schur (QZ) solution, and impulse responses (`numpy`, `scipy`).

---

## Author

**Lucas Leturia** — full dissertation in [`paper/`](paper/).
