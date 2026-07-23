"""sweeps.py — parameter sweeps for the calibration fix + Decision A.

Three sweeps, each printed as a clean table and saved to sweeps_output.md:
  1. ACCOMMODATION (Decision A lever): how the long-issuance accommodation of the
     mandate governs the long-price sign and the λ-shock output response.
  2. DURATION / δ: how long-bond duration drives market-value dominance (wL), the
     inverted φ, and the monetary-shock amplification.
  3. DATA-CONSISTENT wL: recalibrate χ̄ (and habitats) to hit market-value long
     shares; report the φ that the wedge target then requires (outcome a vs b).
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from params import Params, DEFAULT
from steady_state import solve_steady_state, run_checks
from linearize import build, N_PRE, SHOCK_TO_STATE, SHOCKS, VAR
from klein import klein_solve
from calibrate import delta_from_duration, duration_of, chi_for_target_wL, market_value_wL

HERE = Path(__file__).resolve().parent
OUT = []


def emit(line=""):
    print(line)
    OUT.append(line)


def impact(p: Params, accom=0.0, agg_closure="partial"):
    """Solve and return impact (h=0) responses + BK flag + SS objects."""
    ss = solve_steady_state(p)
    A0, A1, ss, meta = build(ss, p, agg_closure=agg_closure, accom=accom)
    sol = klein_solve(A0, A1, N_PRE, SHOCK_TO_STATE, len(SHOCKS))
    out = dict(ss=ss, bk=sol["bk_satisfied"])
    if sol["bk_satisfied"]:
        for sh in ("eps_lambda", "eps_i"):
            d = dict(zip(VAR, sol["Q_impact"][:, SHOCKS.index(sh)].real))
            out[sh] = d
    return out


def sign(x):
    return "↑" if x > 1e-4 else ("↓" if x < -1e-4 else "·")


# ---------------------------------------------------------------------------
def sweep_accommodation():
    emit("## Sweep 1 — ACCOMMODATION (Decision A lever), baseline calibration")
    emit()
    emit("`b̂L = accom·(λ̂L+V̂liab) − Q̂L`. accom=1 is the Entrega III rule (long")
    emit("supply expands with the mandate, A not squeezed); accom=0 is Decision A")
    emit("(no accommodation, mandate redistributes, A squeezed off habitat).")
    emit()
    emit("| accom | BK | λ: π̂₀ | λ: Q̂ᴸ₀ | λ: X̂₀ | λ: v̂₀ | λ: ŷ₀ | money: π̂₀ | money: ŷ₀ |")
    emit("|---:|:--:|---:|---:|---:|---:|---:|---:|---:|")
    for a in (1.0, 0.75, 0.5, 0.25, 0.0):
        r = impact(DEFAULT, accom=a)
        if not r["bk"]:
            emit(f"| {a:.2f} | ✗ | — | — | — | — | — | — | — |"); continue
        dl, di = r["eps_lambda"], r["eps_i"]
        emit(f"| {a:.2f} | ✓ | {dl['pi']:+.3f} | **{dl['QL']:+.3f}**{sign(dl['QL'])} | "
             f"{dl['X']:+.2f} | {dl['v']:+.3f} | {dl['y']:+.2f} | "
             f"{di['pi']:+.3f} | {di['y']:+.2f} |")
    emit()
    emit("Reading: accom→0 flips the **long price to RISE** (Decision A works) and")
    emit("shrinks the λ-output collapse. But π̂₀ and v̂₀ flip sign — the rent is too")
    emit("small (X̄/v̄≈0.34%) to drive the 'rent→backing→deflation' story; long-bond")
    emit("revaluation dominates. The monetary column is unaffected (no mandate).")
    emit()


# ---------------------------------------------------------------------------
def sweep_duration():
    emit("## Sweep 2 — DURATION / δ (drives long-debt dominance), accom=0")
    emit()
    emit("χ̄=0.353 held as a quantity share; δ set from the duration target.")
    emit()
    emit("| duration | δ | Q̄ᴸ | wL (mkt-val) | φ | checks | λ: Q̂ᴸ₀ | λ: π̂₀ | λ: ŷ₀ | money: ŷ₀ |")
    emit("|---:|---:|---:|---:|---:|:--:|---:|---:|---:|---:|")
    for Dy in (1, 2, 5, 8, 12):
        d = delta_from_duration(Dy * 4)
        p = DEFAULT.with_(delta=d)
        ss = solve_steady_state(p)
        ch = run_checks(ss); ok = all(c["ok"] for c in ch.values())
        r = impact(p, accom=0.0)
        if not r["bk"]:
            emit(f"| {Dy}y | {d:.4f} | {ss['QL']:.2f} | {ss['wL']:.3f} | {ss['phi']:.2f} | "
                 f"{'✓' if ok else '✗'} | BK✗ | — | — | — |"); continue
        dl, di = r["eps_lambda"], r["eps_i"]
        emit(f"| {Dy}y | {d:.4f} | {ss['QL']:.2f} | {ss['wL']:.3f} | {ss['phi']:.2f} | "
             f"{'✓' if ok else '✗'} | {dl['QL']:+.3f}{sign(dl['QL'])} | {dl['pi']:+.3f} | "
             f"{dl['y']:+.2f} | {di['y']:+.2f} |")
    emit()
    emit("Reading: shorter bonds (low δ) → wL closer to the quantity share, smaller")
    emit("φ, and **far milder magnitudes** (the monetary ŷ₀ collapses in size). A")
    emit("realistic UK long-gilt duration (8–12y+) pushes δ→1, Q̄ᴸ and wL up, and the")
    emit("amplification up — the long-debt-dominated FTPL regime (Cochrane).")
    emit()


# ---------------------------------------------------------------------------
def sweep_wL_target():
    emit("## Sweep 3 — DATA-CONSISTENT market-value share wL (recalibrate χ̄, habitats)")
    emit()
    emit("χ̄ (quantity) set to hit each market-value wL; habitats scaled to keep the")
    emit("same θ/χ̄ ratios as baseline. φ is inverted to hit ω̄=0.14.")
    emit()
    emit("| target wL | χ̄ (quantity) | θᴬ | θᴮ | φ | αᴬ | solve | checks |")
    emit("|---:|---:|---:|---:|---:|---:|:--:|:--:|")
    for wL in (0.93, 0.70, 0.50, 0.3532):
        chi = chi_for_target_wL(DEFAULT, wL)
        # keep θ/χ̄ ratios as in baseline (θA/χ̄0 = 0.25/0.353, θB/χ̄0 = 0.55/0.353)
        tA = chi * (DEFAULT.theta_A / DEFAULT.chi_bar)
        tB = chi * (DEFAULT.theta_B / DEFAULT.chi_bar)
        p = DEFAULT.with_(chi_bar=chi, theta_A=tA, theta_B=tB)
        try:
            ss = solve_steady_state(p)
            ch = run_checks(ss); ok = all(c["ok"] for c in ch.values())
            emit(f"| {wL:.3f} | {chi:.4f} | {tA:.4f} | {tB:.4f} | **{ss['phi']:.1f}** | "
                 f"{ss['alpha_A']:.4f} | {'✓' if ss['success'] else '✗'} | {'✓' if ok else '✗'} |")
        except Exception as e:
            emit(f"| {wL:.3f} | {chi:.4f} | {tA:.4f} | {tB:.4f} | err | — | ✗ | ✗ |")
    emit()
    emit("Reading: anchoring to the **data** market-value share (wL=0.353 ⇒ χ̄≈0.023)")
    emit("forces a huge φ — the spec's 'outcome (b)': a 14% wedge is hard to generate")
    emit("from optimising habitat demand at a realistic (small-quantity) long position.")
    emit("Keeping χ̄=0.353 as a quantity share (wL=0.93) gives the plausible φ≈3 of")
    emit("'outcome (a)'. **This is the core calibration choice for the dissertation.**")
    emit()


if __name__ == "__main__":
    emit("# Parameter sweeps — habitat NK-FTPL calibration fix & Decision A")
    emit()
    sweep_accommodation()
    sweep_duration()
    sweep_wL_target()
    (HERE / "sweeps_output.md").write_text("\n".join(OUT), encoding="utf-8")
    print("\n[written sweeps_output.md]")
