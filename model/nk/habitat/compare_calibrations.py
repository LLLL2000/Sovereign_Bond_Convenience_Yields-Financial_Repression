"""compare_calibrations.py — the core calibration choice, side by side.

Both columns use the headline config: Decision A (accom=0) + the data-calibrated
Vayanos–Vila term premium (θ_tp≈0.05).  The ONLY difference is how χ̄ is read:

  Cal A — "quantity reading" (Entrega III convention): χ̄=0.353 is the fresh-bond
          QUANTITY long-share.  Implies market-value wL≈0.93 (long-debt-dominated).
  Cal B — "data market-value": χ̄ set so the market-value long share = the DMO
          data (wL=0.3532 ⇒ χ̄≈0.023); habitats scaled proportionally.

Outputs a side-by-side table and an IRF overlay figure (figures/hab_compare.png).
"""

from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from params import DEFAULT
from steady_state import solve_steady_state, run_checks
from linearize import build, N_PRE, SHOCK_TO_STATE, SHOCKS, VAR
from klein import klein_solve
from calibrate import chi_for_target_wL, market_value_wL

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"; FIG.mkdir(exist_ok=True)

# --- the two calibrations -----------------------------------------------------
pA = DEFAULT                                   # χ̄=0.353 read as a quantity share
chiB = chi_for_target_wL(DEFAULT, 0.3532)      # χ̄ for data market-value wL
pB = DEFAULT.with_(chi_bar=chiB,
                   theta_A=chiB * (DEFAULT.theta_A / DEFAULT.chi_bar),
                   theta_B=chiB * (DEFAULT.theta_B / DEFAULT.chi_bar))


def solve(p):
    ss = solve_steady_state(p)
    A0, A1, ss, meta = build(ss, p)            # uses p.accom, p.theta_tp defaults
    sol = klein_solve(A0, A1, N_PRE, SHOCK_TO_STATE, len(SHOCKS))
    return ss, sol


def irf(sol, sh, h=40):
    path = np.zeros((h, len(VAR)))
    path[0] = sol["Q_impact"][:, SHOCKS.index(sh)].real
    for t in range(1, h):
        path[t] = sol["P"] @ path[t - 1]
    return {v: path[:, i] for i, v in enumerate(VAR)}


def main():
    ssA, solA = solve(pA)
    ssB, solB = solve(pB)
    chkA = all(c["ok"] for c in run_checks(ssA).values())
    chkB = all(c["ok"] for c in run_checks(ssB).values())

    iA = {sh: irf(solA, sh) for sh in ("eps_lambda", "eps_i")}
    iB = {sh: irf(solB, sh) for sh in ("eps_lambda", "eps_i")}
    # realistic shock scaling
    msA = 0.0025 / abs(iA["eps_i"]["i"][0]); msB = 0.0025 / abs(iB["eps_i"]["i"][0])
    lam = 0.01

    def row(label, a, b):
        print(f"  {label:34s} | {a:>20} | {b:>20}")

    print("=" * 84)
    print("CORE CALIBRATION CHOICE — side by side (headline config: Decision A + V-V premium)")
    print("=" * 84)
    row("", "Cal A: χ̄ = quantity", "Cal B: data wL")
    print("  " + "-" * 80)
    row("χ̄ (quantity long-share)", f"{pA.chi_bar:.4f}", f"{pB.chi_bar:.4f}")
    row("market-value wL", f"{ssA['wL']:.3f}", f"{ssB['wL']:.3f}")
    row("θ^A, θ^B (habitats)", f"{pA.theta_A:.3f}, {pA.theta_B:.3f}",
        f"{pB.theta_A:.3f}, {pB.theta_B:.3f}")
    row("φ (inverted for ω̄=0.14)", f"{ssA['phi']:.2f}", f"{ssB['phi']:.2f}")
    row("  → realism (spec outcome)", "(a) plausible", "(b) large")
    row("α^A (A long share)", f"{ssA['alpha_A']:.4f}", f"{ssB['alpha_A']:.4f}")
    row("rent X̄/v̄", f"{ssA['X_v']*100:.3f}%", f"{ssB['X_v']*100:.3f}%")
    row("all §4.4 checks pass", str(chkA), str(chkB))
    row("Blanchard–Kahn", f"{'OK' if solA['bk_satisfied'] else 'FAIL'}",
        f"{'OK' if solB['bk_satisfied'] else 'FAIL'}")
    print("  " + "-" * 80)
    print("  IMPACT, λ̂L = +1% regulatory tightening:")
    for v, lab in [("QL", "Q̂L (long price)"), ("pi", "π̂ (inflation)"),
                   ("v", "v̂ (debt value)"), ("y", "ŷ (output)"), ("X", "X̂ (rent)")]:
        row("   " + lab, f"{iA['eps_lambda'][v][0]*lam*100:+.3f}%",
            f"{iB['eps_lambda'][v][0]*lam*100:+.3f}%")
    print("  IMPACT, monetary shock scaled to 25bp equilibrium-rate move:")
    for v, lab in [("pi", "π̂ (inflation)"), ("y", "ŷ (output)")]:
        row("   " + lab, f"{iA['eps_i'][v][0]*msA*100:+.3f}%",
            f"{iB['eps_i'][v][0]*msB*100:+.3f}%")
    print("=" * 84)
    print("Cal A: plausible φ but long-debt-dominated (wL≈0.93) ⇒ severe monetary")
    print("       hyper-elasticity and the conditional signs flip.")
    print("Cal B: data-consistent maturity (wL≈0.35) tames the monetary response")
    print("       markedly, but the wedge needs an implausibly large φ.")
    print("This trade-off is THE calibration result to report (REPORT §10, §13).")

    # --- overlay figure -------------------------------------------------------
    fig, axes = plt.subplots(2, 4, figsize=(16, 6.5))
    panels = [("eps_lambda", "QL", "Q̂L | λ shock"),
              ("eps_lambda", "pi", "π̂ | λ shock"),
              ("eps_lambda", "v", "v̂ | λ shock"),
              ("eps_lambda", "X", "X̂ rent | λ shock"),
              ("eps_i", "QL", "Q̂L | money"),
              ("eps_i", "pi", "π̂ | money"),
              ("eps_i", "y", "ŷ | money"),
              ("eps_i", "i", "î | money")]
    for ax, (sh, v, title) in zip(axes.flat, panels):
        scA = lam if sh == "eps_lambda" else msA
        scB = lam if sh == "eps_lambda" else msB
        ax.plot(iA[sh][v] * scA * 100, lw=1.7, label="Cal A (χ̄ quantity)")
        ax.plot(iB[sh][v] * scB * 100, lw=1.7, ls="--", label="Cal B (data wL)")
        ax.axhline(0, color="0.6", lw=0.6); ax.set_title(title)
        ax.set_xlabel("h"); ax.set_ylabel("%"); ax.grid(alpha=0.3)
    axes.flat[0].legend(fontsize=8)
    fig.suptitle("Calibration comparison — λ at +1%, monetary at 25bp "
                 "(Decision A + V-V term premium)")
    fig.tight_layout()
    fig.savefig(FIG / "hab_compare.png", dpi=110)
    plt.close(fig)
    print(f"\n[wrote figures/hab_compare.png]")


if __name__ == "__main__":
    main()
