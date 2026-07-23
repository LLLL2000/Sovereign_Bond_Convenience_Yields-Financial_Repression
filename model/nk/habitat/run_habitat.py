"""run_habitat.py — driver for the microfounded captive-habitat NK-FTPL model.

Build order follows the spec (Section 7):
  1. steady state + φ-inversion + Section 4.4 checks
  2. linearisation + code checks (−1 inflation coeff, relative-wealth root 1−ε)
  3. Klein/QZ solve + BK diagnostics
  4. headline λ̂L IRF + four sign predictions
  5. two regime diagnostics + φ→0 counterfactual + sensitivity bands
Outputs: figures/, irfs/*.csv, diagnostics.pkl, and a console report.
"""

from __future__ import annotations

import sys
import pickle
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from params import DEFAULT, Params
from steady_state import solve_steady_state, run_checks, print_steady_state, print_checks
from linearize import build, build_default, VAR, IDX, N_PRE, SHOCKS, SHOCK_TO_STATE
from klein import klein_solve, eigenvalue_table

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"; FIG.mkdir(exist_ok=True)
IRFD = HERE / "irfs"; IRFD.mkdir(exist_ok=True)


# ----------------------------------------------------------------------------
def solve_model(p: Params, psi=None, phi_scale=1.0):
    ss = solve_steady_state(p)
    A0, A1, ss, meta = build(ss, p, psi=psi, phi_scale=phi_scale)
    sol = klein_solve(A0, A1, N_PRE, SHOCK_TO_STATE, len(SHOCKS))
    return ss, meta, sol, (A0, A1)


def irf(sol: Dict, shock: str, horizon: int = 40) -> pd.DataFrame:
    j = SHOCKS.index(shock)
    path = np.zeros((horizon, len(VAR)))
    path[0, :] = sol["Q_impact"][:, j].real
    for h in range(1, horizon):
        path[h, :] = sol["P"] @ path[h - 1, :]
    df = pd.DataFrame(path, columns=VAR)
    df.index.name = "h"
    return df


# ----------------------------------------------------------------------------
def headline_signs(sol: Dict) -> Dict[str, tuple]:
    """Four (+ short-rate) sign predictions on impact of a unit λ̂L shock."""
    d = irf(sol, "eps_lambda", horizon=2).iloc[0]
    preds = {
        "inflation falls (π̂0<0)":          (d["pi"], d["pi"] < 0),
        "long price rises (Q̂L0>0)":        (d["QL"], d["QL"] > 0),
        "rent rises (X̂0>0)":               (d["X"],  d["X"] > 0),
        "real debt value rises (v̂0>0)":    (d["v"],  d["v"] > 0),
        "short rate falls (î0<0)":          (d["i"],  d["i"] < 0),
    }
    return preds


def plot_irf(df: pd.DataFrame, title: str, out: Path):
    target = ["pi", "QL", "X", "v", "i"]
    labels = [r"$\hat\pi$", r"$\hat Q^L$", r"$\hat X$ (rent)", r"$\hat v$", r"$\hat\imath$"]
    fig, axes = plt.subplots(1, 5, figsize=(16, 3.2))
    for ax, var, lab in zip(axes, target, labels):
        ax.plot(df.index, df[var], lw=1.7)
        ax.axhline(0, color="0.6", lw=0.6)
        ax.set_title(lab); ax.set_xlabel("h (quarters)"); ax.grid(alpha=0.3)
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)


def plot_counterfactual(sol_full, sol_cf, out: Path):
    fa = irf(sol_full, "eps_lambda"); fc = irf(sol_cf, "eps_lambda")
    target = ["pi", "QL", "X", "v"]
    labels = [r"$\hat\pi$", r"$\hat Q^L$", r"$\hat X$ (rent)", r"$\hat v$"]
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.2))
    for ax, var, lab in zip(axes, target, labels):
        ax.plot(fa.index, fa[var], lw=1.7, label=r"headline $\phi=3.0$")
        ax.plot(fc.index, fc[var], lw=1.5, ls="--", label=r"counterfactual $\phi\to0$")
        ax.axhline(0, color="0.6", lw=0.6)
        ax.set_title(lab); ax.set_xlabel("h"); ax.grid(alpha=0.3)
    axes[0].legend(fontsize=8)
    fig.suptitle(r"Habitat channel: headline vs $\phi\to0$ counterfactual ($\hat\lambda^L$ shock)")
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)


def plot_phi_pi_sensitivity(p: Params, out: Path):
    fig, ax = plt.subplots(figsize=(8, 5))
    rows = []
    for phi_pi in (0.0, 0.3, 0.5, 0.8, 0.95):
        _, _, sol, _ = solve_model(p.with_(phi_pi=phi_pi))
        if not sol["bk_satisfied"]:
            rows.append((phi_pi, None)); continue
        df = irf(sol, "eps_lambda")
        ax.plot(df.index, df["pi"], lw=1.6, label=rf"$\phi_\pi={phi_pi}$")
        rows.append((phi_pi, df["pi"].iloc[0]))
    ax.axhline(0, color="0.6", lw=0.6)
    ax.set_xlabel("h (quarters)"); ax.set_ylabel(r"$\hat\pi_t$")
    ax.set_title(r"Sensitivity of $\hat\pi$ to $\hat\lambda^L$ across $\phi_\pi$")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)
    return rows


# ----------------------------------------------------------------------------
def main() -> int:
    p = DEFAULT
    print("#" * 72)
    print("# MICROFOUNDED CAPTIVE-HABITAT NK-FTPL  —  full run")
    print("#" * 72)

    # ---- 1. steady state -----------------------------------------------------
    ss = solve_steady_state(p, verbose=True)
    print_steady_state(ss)
    checks = run_checks(ss)
    print_checks(checks)

    # ---- 2-3. linearise + solve ---------------------------------------------
    A0, A1, ss, meta = build(ss, p)
    sol = klein_solve(A0, A1, N_PRE, SHOCK_TO_STATE, len(SHOCKS))
    print("=" * 72)
    print("LINEARISATION CODE CHECKS")
    print("=" * 72)
    print(f"  row-13 inflation coefficient −(wS+wL) = {meta['inflation_coeff_R7']:+.4f}  (target −1)")
    wroot = [m for m in sol["moduli"] if 0.9 < m < 1.0]
    print(f"  relative-wealth root = {wroot} (target 1−ψ = {1-p.psi})")
    print()
    print(eigenvalue_table(sol))
    print()

    if not sol["bk_satisfied"]:
        print("BK FAILED — stopping.")
        return 1

    # ---- 4. headline IRF + four signs ---------------------------------------
    print("=" * 72)
    print("HEADLINE EXPERIMENT — unit λ̂L (regulatory tightening), four sign predictions")
    print("=" * 72)
    preds = headline_signs(sol)
    allsigns = True
    for name, (val, ok) in preds.items():
        allsigns &= ok
        print(f"  [{'OK ' if ok else 'XX '}] {name:32s} value = {val:+.5f}")
    print(f"  --> all four+ sign predictions {'CONFIRMED' if allsigns else 'NOT all confirmed (conditional, see spec §6.3)'}")
    print()
    # ---- realistic shock sizes (per-unit IRFs scale linearly) ----------------
    print("Impact responses at REALISTIC shock sizes")
    print(f"  config: Decision A (accom={p.accom}) + calibrated V-V term premium (θ_tp={p.theta_tp})")
    d1 = irf(sol, "eps_lambda", horizon=2).iloc[0]
    di = irf(sol, "eps_i", horizon=2).iloc[0]
    mon_scale = 0.0025 / abs(di["i"]) if abs(di["i"]) > 1e-9 else 0.0
    lam = 0.01   # a 1% regulatory tightening
    print(f"  λ̂L = +1% (regulatory tightening):  "
          f"Q̂L={d1['QL']*lam*100:+.3f}%  π̂={d1['pi']*lam*100:+.3f}%  "
          f"v̂={d1['v']*lam*100:+.3f}%  ŷ={d1['y']*lam*100:+.3f}%")
    print(f"  monetary, scaled to a 25bp equilibrium-rate move:  "
          f"π̂={di['pi']*mon_scale*100:+.3f}%  ŷ={di['y']*mon_scale*100:+.3f}%")
    print(f"  (ŷ stays large — the long-debt-dominated FTPL hyper-elasticity; "
          f"see REPORT §15-17)")
    print()

    # ---- 5a. regime diagnostic (i): contractionary money raises inflation ----
    di = irf(sol, "eps_i", horizon=2).iloc[0]
    print("REGIME DIAGNOSTIC (i): contractionary monetary shock (ε_i>0)")
    print(f"  π̂0 = {di['pi']:+.5f}  -> {'RISES on impact (FTPL price puzzle) OK' if di['pi']>0 else 'falls (NOT the FTPL sign)'}")
    print()

    # ---- 5b. regime diagnostic (ii): |π̂0| vs φ_π and φ_π=1 boundary ---------
    print("REGIME DIAGNOSTIC (ii): |π̂0| to λ̂L across φ_π, and the φ_π=1 boundary")
    grid = [0.0, 0.3, 0.5, 0.8, 0.95, 1.0]
    pi0 = {}
    for fp in grid:
        _, _, s2, _ = solve_model(p.with_(phi_pi=fp))
        if s2["bk_satisfied"]:
            pi0[fp] = irf(s2, "eps_lambda", horizon=2).iloc[0]["pi"]
            print(f"  φ_π={fp:4.2f}: BK OK   π̂0={pi0[fp]:+.5f}  |π̂0|={abs(pi0[fp]):.5f}")
        else:
            print(f"  φ_π={fp:4.2f}: BK FAILS (determinacy boundary)")
    print()

    # ---- 5c. φ→0 counterfactual ---------------------------------------------
    print("COUNTERFACTUAL (Section 6.5): φ→0 shuts the habitat/rent channel")
    _, _, sol_cf, _ = solve_model(p, phi_scale=0.0)
    if sol_cf["bk_satisfied"]:
        dcf = irf(sol_cf, "eps_lambda", horizon=2).iloc[0]
        dfull = irf(sol, "eps_lambda", horizon=2).iloc[0]
        for v in ["pi", "QL", "X", "v"]:
            print(f"  {v:3s}: headline {dfull[v]:+.5f}   φ→0 {dcf[v]:+.5f}   "
                  f"habitat contribution {dfull[v]-dcf[v]:+.5f}")
    print()

    # ---- 5d. ω̄ sensitivity band + ψ invariance ------------------------------
    print("SENSITIVITY: ω̄ band [0.12,0.21]  (φ inverted, π̂0 to λ̂L)")
    for om in (0.12, 0.14, 0.17, 0.21):
        ss2, _, s3, _ = solve_model(p.with_(omega_bar=om))
        d = irf(s3, "eps_lambda", horizon=2).iloc[0] if s3["bk_satisfied"] else None
        bk = s3["bk_satisfied"]
        print(f"  ω̄={om:.2f}: φ={ss2['phi']:.3f}  BK={bk}  "
              f"π̂0={d['pi']:+.5f} Q̂L0={d['QL']:+.5f} X̂0={d['X']:+.5f}" if bk else
              f"  ω̄={om:.2f}: BK fails")
    print()
    print("ψ-INVARIANCE of the headline π̂0 (closing device, spec test):")
    for psi in (1e-3, 1e-4, 1e-5):
        _, _, s4, _ = solve_model(p, psi=psi)
        d = irf(s4, "eps_lambda", horizon=2).iloc[0]
        print(f"  ψ={psi:.0e}: π̂0={d['pi']:+.6f}  Q̂L0={d['QL']:+.6f}  v̂0={d['v']:+.6f}")
    print()

    # ---- figures + csv + diagnostics ----------------------------------------
    print("Writing figures, IRF csvs, diagnostics ...")
    shock_lab = {"eps_lambda": "lambda", "eps_chi": "chi", "eps_V": "V",
                 "eps_g": "g", "eps_tau": "tau", "eps_i": "i"}
    all_irfs = {}
    for sh, lab in shock_lab.items():
        df = irf(sol, sh)
        all_irfs[sh] = df
        df.to_csv(IRFD / f"hab_irf_{lab}.csv")
    plot_irf(all_irfs["eps_lambda"], r"Headline IRF: unit $\hat\lambda^L$ (regulatory tightening)",
             FIG / "hab_irf_lambda.png")
    plot_irf(all_irfs["eps_i"], r"IRF: contractionary monetary shock $\hat u^i$",
             FIG / "hab_irf_monetary.png")
    plot_counterfactual(sol, sol_cf, FIG / "hab_counterfactual_phi.png")
    plot_phi_pi_sensitivity(p, FIG / "hab_sensitivity_phi_pi.png")

    diag = dict(VAR=VAR, SHOCKS=SHOCKS, steady_state=ss, checks=checks,
                eigenvalues=sol["eigenvalues"], bk=sol["bk_satisfied"],
                P=sol["P"], F=sol["F"], M=sol["M"], Q_impact=sol["Q_impact"],
                A0=A0, A1=A1, irfs=all_irfs, signs=preds, params=p.as_dict())
    with open(HERE / "hab_diagnostics.pkl", "wb") as f:
        pickle.dump(diag, f)
    print("  wrote figures/hab_*.png, irfs/hab_irf_*.csv, hab_diagnostics.pkl")
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
