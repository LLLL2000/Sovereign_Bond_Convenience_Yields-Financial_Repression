"""calibrate.py — principled calibration helpers for problem #1.

PROBLEM #1 (the quantity-vs-market-value tension).
  The maturity composition χ̄ in the spec (eq 2, b̄L=χ̄(b̄S+b̄L)) is a *quantity*
  share — fresh-bond-equivalent units.  The data anchor wL=0.353 (DMO, §5.2) is a
  *market-value* share.  With a perpetuity priced at Q̄ᴸ≈22.75 these are wildly
  different objects; Entrega III's `χ̄ = wL` convention silently conflated them.

THE FIX (literature-grounded).
  In the macro-finance / FTPL literature the geometric consol's decay δ is
  calibrated to a **Macaulay-duration target** (Rudebusch–Swanson 2008; Woodford
  2001; Cochrane FTPL), and the present-value identity values debt at **market
  value**.  So the principled calibration anchors the two *observables*
  separately and lets the latent quantity share and the habitat strength float:

    δ      ← chosen so the long bond's Macaulay duration matches the data
             (geometric consol: D = 1/(1−βδ) quarters  ⇒  δ = (1 − 1/D)/β).
    wL     ← anchored to the DMO market-value long share (0.353).
    χ̄      ← the quantity share IMPLIED by (wL, δ):
                 χ̄ = wL / [ f(1−wL) + wL ],   f = 1 + δ Q̄ᴸ.
    φ      ← inverted to hit ω̄ = 0.14 (unchanged).

  This exposes (χ̄, φ) as *outcomes*, which is exactly what makes the spec's
  "outcome (a) plausible φ" vs "outcome (b) implausible φ" question answerable.
"""

from __future__ import annotations

from params import Params


def delta_from_duration(D_quarters: float, beta: float = 0.99) -> float:
    """Geometric consol decay δ for a target Macaulay duration (in quarters).
    D = 1/(1−βδ)  ⇒  δ = (1 − 1/D)/β."""
    return (1.0 - 1.0 / D_quarters) / beta


def duration_of(delta: float, beta: float = 0.99) -> float:
    """Macaulay duration (quarters) of the geometric consol with decay δ."""
    return 1.0 / (1.0 - beta * delta)


def QL_fund_of(delta: float, beta: float = 0.99) -> float:
    return (beta / 1.0) / (1.0 - beta * delta)


def chi_for_target_wL(p: Params, wL_target: float) -> float:
    """Quantity long-share χ̄ that produces market-value long share wL_target,
    given the params' (β, δ, ω̄) which fix the long price.  Inverts
       wL = f χ̄ / [ (1−χ̄) + f χ̄ ],   f = 1 + δ Q̄ᴸ_target."""
    f = 1.0 + p.delta * p.QL_target
    return wL_target / (f * (1.0 - wL_target) + wL_target)


def market_value_wL(p: Params, chi_bar: float) -> float:
    """Forward map: market-value long share implied by a quantity share χ̄."""
    f = 1.0 + p.delta * p.QL_target
    return f * chi_bar / ((1.0 - chi_bar) + f * chi_bar)


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = Params()
    print(f"baseline δ={p.delta}: duration={duration_of(p.delta):.1f}q "
          f"= {duration_of(p.delta)/4:.2f}y ; Q̄ᴸfund={QL_fund_of(p.delta):.2f}")
    print(f"  market-value wL implied by χ̄={p.chi_bar} (quantity): "
          f"{market_value_wL(p, p.chi_bar):.4f}")
    print(f"  χ̄ (quantity) needed for data wL=0.3532: "
          f"{chi_for_target_wL(p, 0.3532):.5f}")
    print()
    for Dy in (2, 5, 8, 12, 20):
        d = delta_from_duration(Dy * 4)
        print(f"  duration {Dy:2d}y -> δ={d:.4f}  Q̄ᴸfund={QL_fund_of(d):.2f}")
