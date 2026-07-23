"""nk_ftpl_solve.py

Solver and impulse-responses for the NK-FTPL with long-end captive demand.

Implements the log-linearized system from `nk_ftpl_embedding.pdf` (§4)
and the calibration / outputs requested in the RA brief.

Approach:
  - 18 state-vector components: 8 predetermined (b̂S_{t-1}, b̂L_{t-1}, plus
    six AR(1) states λ̂L, χ̂, V̂liab, ĝ, τ̂, ûi) followed by 10 forward jumps
    (ĉ, ŷ, π̂, î, Q̂L, Q̂L,fund, ω̂, R̂, v̂, ŝ).
  - The current-period stocks b̂L_t, b̂S_t are substituted out using
    eqs (5) and (10), reducing the 12 endogenous to 10 jumps; their
    lagged values are carried as predetermined state with explicit
    dynamic equations.
  - System stacked as  A0 E_t x_{t+1} = A1 x_t + B ε_t.  B = 0 since
    AR(1) innovations enter at t+1; shock impacts at t = 0 are
    constructed manually as the initial-state matrix Q_impact.
  - Klein (1999) generalized Schur via scipy.linalg.ordqz on (A1, A0),
    sorting eigenvalues 'iuc' (stable inside the unit circle first).
"""

from __future__ import annotations

import pickle
import sys
import traceback
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import scipy.linalg
import matplotlib.pyplot as plt

# Windows consoles default to cp1252 — force UTF-8 so we can print
# Greek letters and math symbols in diagnostics.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
IRFS_DIR = HERE / "irfs"
IRFS_DIR.mkdir(exist_ok=True)
DIAG_PATH = HERE / "diagnostics.pkl"


# ------------------------------------------------------------------
# Variable / shock ordering
# ------------------------------------------------------------------

VAR_NAMES = [
    # Predetermined (8): two bond-stock lags + six AR(1) states
    "bS_lag", "bL_lag",
    "lambda_L", "chi", "V_liab", "g", "tau", "u_i",
    # Forward-looking (10)
    "c", "y", "pi", "i", "QL", "QL_fund", "omega", "R", "v", "s",
]
N = len(VAR_NAMES)         # 18
N_PRE = 8
N_FWD = N - N_PRE          # 10
IDX = {n: i for i, n in enumerate(VAR_NAMES)}

SHOCK_NAMES = ["eps_lambda", "eps_chi", "eps_V", "eps_g", "eps_tau", "eps_i"]
N_SHOCKS = len(SHOCK_NAMES)

# Map shock j -> predetermined-row hit by that shock at t = 0
SHOCK_TO_AR1_ROW = {
    "eps_lambda": IDX["lambda_L"],
    "eps_chi":    IDX["chi"],
    "eps_V":      IDX["V_liab"],
    "eps_g":      IDX["g"],
    "eps_tau":    IDX["tau"],
    "eps_i":      IDX["u_i"],
}


# ------------------------------------------------------------------
# Calibration (matches Table in §3 of the brief / §7 of the PDF)
# ------------------------------------------------------------------

CAL = {
    "beta":         0.99,
    "sigma":        1.0,
    "delta":        0.96,
    "omega_bar":    0.14,    # §5.2 clean-window headline (4-yr avg 2021-2024)
    "eta":          0.956,   # δQ^L/(1+δQ^L) at new ω̄; Q^L=1.14·Q^L_fund=22.75
    "wS":           0.6468,  # 1 - long_share (QR Jun-2025 nominal-weighted)
    "wL":           0.3532,  # DMO QR Jun-2025 nominal-weighted long share
    "s_v":         -0.0334,  # s̄/v consistent with ω̄=0.14, wL=0.3532
    "R_v":          0.0434,  # R̄/v = (1-β) - s̄/v at β=0.99
    "c_y":          0.60,    # NK calibration; not in §5.2 outputs (inherited)
    "g_y":          0.40,    # NK calibration; not in §5.2 outputs (inherited)
    "tau_y":        0.37,    # NK calibration; not in §5.2 outputs (inherited)
    "chi_bar":      0.3532,  # χ̄ = wL convention per section5.md L88
    "theta":        0.75,
    "phi_pi":       0.5,
    "rho_lambda":   0.7,
    "rho_chi":      0.7,
    "rho_V":        0.7,
    "rho_g":        0.7,
    "rho_tau":      0.7,
    "rho_i":        0.7,
    "sigma_lambda": 0.01,
}
CAL["kappa"] = (1 - CAL["theta"]) * (1 - CAL["beta"] * CAL["theta"]) * CAL["sigma"] / CAL["theta"]


# ------------------------------------------------------------------
# System builder
# ------------------------------------------------------------------

def build_system(cal: Dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the 18×18 matrices A0, A1 and the 18×6 shock matrix B.

    Rows 0–9   = jump equations (1, 2, 3, 4, 6, 7, 8, 9, 11, 12 of §5).
    Rows 10–11 = bond-lag dynamics (eq 5 and eq 10 substituted).
    Rows 12–17 = AR(1) laws for the six exogenous states.

    B is identically zero: AR(1) innovations enter at t+1, not t.
    Shock impacts at t=0 are constructed manually in klein_solve.
    """
    A0 = np.zeros((N, N))
    A1 = np.zeros((N, N))
    B  = np.zeros((N, N_SHOCKS))

    beta_      = cal["beta"]
    sigma      = cal["sigma"]
    kappa      = cal["kappa"]
    phi_pi     = cal["phi_pi"]
    eta        = cal["eta"]
    wS, wL     = cal["wS"], cal["wL"]
    s_v, R_v   = cal["s_v"], cal["R_v"]
    c_y, g_y   = cal["c_y"], cal["g_y"]
    tau_y      = cal["tau_y"]
    chi_bar    = cal["chi_bar"]
    omega_bar  = cal["omega_bar"]
    chi_scale  = 1.0 / (chi_bar * (1.0 - chi_bar))   # for eq (10)

    # Row 0 — IS / consumption Euler (eq 1)
    #   ĉ_t + (1/σ) î_t  =  E ĉ_{t+1} + (1/σ) E π̂_{t+1}
    A0[0, IDX["c"]]  = 1.0
    A0[0, IDX["pi"]] = 1.0 / sigma
    A1[0, IDX["c"]]  = 1.0
    A1[0, IDX["i"]]  = 1.0 / sigma

    # Row 1 — NK Phillips curve (eq 2)
    #   π̂_t − κ ŷ_t  =  β E π̂_{t+1}
    A0[1, IDX["pi"]] = beta_
    A1[1, IDX["pi"]] = 1.0
    A1[1, IDX["y"]]  = -kappa

    # Row 2 — Passive Taylor rule (eq 3)
    #   î_t − φ_π π̂_t − ûi_t = 0    (no t+1 terms; A0 row = 0)
    A1[2, IDX["i"]]   = 1.0
    A1[2, IDX["pi"]]  = -phi_pi
    A1[2, IDX["u_i"]] = -1.0

    # Row 3 — Long-bond fundamental price (eq 4)
    #   σ E ĉ_{t+1} + E π̂_{t+1} − η E Q̂L_{t+1}  =  σ ĉ_t − Q̂L,fund_t
    A0[3, IDX["c"]]       = sigma
    A0[3, IDX["pi"]]      = 1.0
    A0[3, IDX["QL"]]      = -eta
    A1[3, IDX["c"]]       = sigma
    A1[3, IDX["QL_fund"]] = -1.0

    # Row 4 — Wedge definition (eq 6)
    #   ω̂_t − Q̂L_t + Q̂L,fund_t = 0    (A0 row = 0)
    A1[4, IDX["omega"]]   = 1.0
    A1[4, IDX["QL"]]      = -1.0
    A1[4, IDX["QL_fund"]] = 1.0

    # Row 5 — Rent (eq 7)
    #   R̂_t − ω̂_t/ω̄ − λ̂L − V̂liab = 0
    A1[5, IDX["R"]]        = 1.0
    A1[5, IDX["omega"]]    = -1.0 / omega_bar
    A1[5, IDX["lambda_L"]] = -1.0
    A1[5, IDX["V_liab"]]   = -1.0

    # Row 6 — Real debt market value (eq 8)
    #   v̂_t = w_S (b̂S_{t-1} − π̂_t) + w_L (b̂L_{t-1} + η Q̂L_t − π̂_t)
    #   Using w_S + w_L = 1:
    #   v̂_t − w_S b̂S_lag − w_L b̂L_lag + π̂_t − w_L η Q̂L_t = 0
    A1[6, IDX["v"]]      = 1.0
    A1[6, IDX["bS_lag"]] = -wS
    A1[6, IDX["bL_lag"]] = -wL
    A1[6, IDX["pi"]]     = 1.0
    A1[6, IDX["QL"]]     = -wL * eta

    # Row 7 — FTPL identity (eq 9)
    #   β E v̂_{t+1} + β E π̂_{t+1}  =  v̂_t − (s̄/v) ŝ − (R̄/v) R̂ + β î_t
    A0[7, IDX["v"]]  = beta_
    A0[7, IDX["pi"]] = beta_
    A1[7, IDX["v"]]  = 1.0
    A1[7, IDX["s"]]  = -s_v
    A1[7, IDX["R"]]  = -R_v
    A1[7, IDX["i"]]  = beta_

    # Row 8 — Resource constraint (eq 11)
    #   (c̄/ȳ) ĉ + (ḡ/ȳ) ĝ − ŷ = 0
    A1[8, IDX["c"]] = c_y
    A1[8, IDX["g"]] = g_y
    A1[8, IDX["y"]] = -1.0

    # Row 9 — Primary surplus (eq 12)
    #   ŝ − (τ̄/ȳ) τ̂ + (ḡ/ȳ) ĝ = 0
    A1[9, IDX["s"]]   = 1.0
    A1[9, IDX["tau"]] = -tau_y
    A1[9, IDX["g"]]   = g_y

    # Row 10 — bS_lag dynamic (substitute eqs 5 and 10)
    #   b̂S_lag_{t+1} = b̂S_t = λ̂L + V̂liab − Q̂L − χ̂ / (χ̄(1-χ̄))
    A0[10, IDX["bS_lag"]]   = 1.0
    A1[10, IDX["lambda_L"]] = 1.0
    A1[10, IDX["V_liab"]]   = 1.0
    A1[10, IDX["QL"]]       = -1.0
    A1[10, IDX["chi"]]      = -chi_scale

    # Row 11 — bL_lag dynamic (substitute eq 5)
    #   b̂L_lag_{t+1} = b̂L_t = λ̂L + V̂liab − Q̂L
    A0[11, IDX["bL_lag"]]   = 1.0
    A1[11, IDX["lambda_L"]] = 1.0
    A1[11, IDX["V_liab"]]   = 1.0
    A1[11, IDX["QL"]]       = -1.0

    # Rows 12–17 — AR(1) laws
    ar1_specs = [
        ("lambda_L", "rho_lambda"),
        ("chi",      "rho_chi"),
        ("V_liab",   "rho_V"),
        ("g",        "rho_g"),
        ("tau",      "rho_tau"),
        ("u_i",      "rho_i"),
    ]
    for k, (var, rhopar) in enumerate(ar1_specs):
        row = 12 + k
        A0[row, IDX[var]] = 1.0
        A1[row, IDX[var]] = cal[rhopar]

    return A0, A1, B


# ------------------------------------------------------------------
# Klein solver
# ------------------------------------------------------------------

def klein_solve(A0: np.ndarray, A1: np.ndarray, n_pre: int) -> dict:
    """Generalized Schur on (A1, A0) sorted 'iuc'; Klein (1999) policy
    function. Returns a dict with policy matrices and diagnostics.

    Raises LinAlgError if Z11 is singular (and BK is satisfied).
    """
    n = A0.shape[0]
    n_fwd = n - n_pre

    AA, BB, alpha, beta_, Q_orth, Z = scipy.linalg.ordqz(
        A1, A0, sort="iuc", output="complex"
    )

    # Some α_i/β_i pairs may be 0/0 (numerical) or finite/0 (infinite eigenvalue
    # from a static equation with empty row in A0). Both are fine; suppress
    # the noisy divide-by-zero warnings.
    with np.errstate(divide="ignore", invalid="ignore"):
        eigenvalues = alpha / beta_
    moduli = np.abs(eigenvalues)
    n_stable   = int(np.sum(moduli < 1.0))
    n_unstable = int(np.sum(moduli > 1.0))
    n_unit     = int(np.sum(np.isclose(moduli, 1.0)))
    bk_satisfied = (n_unstable == n_fwd) and (n_stable == n_pre)

    sol = dict(
        AA=AA, BB=BB, alpha=alpha, beta=beta_,
        Q_orth=Q_orth, Z=Z,
        eigenvalues=eigenvalues,
        n_stable=n_stable, n_unstable=n_unstable, n_unit=n_unit,
        bk_satisfied=bk_satisfied,
    )

    if not bk_satisfied:
        # Leave P, Q_impact, F, M, N as None; caller handles.
        sol.update(F=None, M=None, P=None, N=None, Q_impact=None)
        return sol

    # Partition Z (Z is unitary; rotation y = Z^H x)
    Z11 = Z[:n_pre, :n_pre]
    Z21 = Z[n_pre:, :n_pre]
    # AA, BB upper triangular; stable block is the upper-left
    AA_ss = AA[:n_pre, :n_pre]
    BB_ss = BB[:n_pre, :n_pre]

    try:
        Z11_inv = scipy.linalg.solve(Z11, np.eye(n_pre, dtype=Z11.dtype))
    except scipy.linalg.LinAlgError as e:
        raise scipy.linalg.LinAlgError(
            "Z11 from generalized Schur is singular — "
            "Klein decomposition cannot proceed. "
            "Likely BK is technically met but the predetermined block "
            "is not spanned by the stable subspace. " + str(e)
        )
    try:
        BB_ss_inv = scipy.linalg.solve(BB_ss, np.eye(n_pre, dtype=BB_ss.dtype))
    except scipy.linalg.LinAlgError as e:
        raise scipy.linalg.LinAlgError(
            "BB_ss (stable block of BB) is singular — state-law cannot "
            "be inverted. " + str(e)
        )

    F = np.real(Z21 @ Z11_inv)                       # 10 × 8 policy function
    M = np.real(Z11 @ BB_ss_inv @ AA_ss @ Z11_inv)   # 8 × 8 state law

    # Shock-impact on next-period predetermined state.
    # Bond-lag rows (0, 1) get 0 (set by policy at t, not by t+1 shocks).
    # AR(1) rows (2..7) get an identity block, one shock per state.
    N_mat = np.zeros((n_pre, N_SHOCKS))
    for j, shock_name in enumerate(SHOCK_NAMES):
        N_mat[SHOCK_TO_AR1_ROW[shock_name], j] = 1.0

    # Full propagator P (18 × 18): x_{t+1} = P x_t (deterministic).
    # Jumps at t+1 are determined by k_{t+1} via the policy function.
    P = np.zeros((n, n))
    P[:n_pre, :n_pre] = M
    P[n_pre:, :n_pre] = F @ M

    # Initial-state matrix Q_impact (18 × 6):  x_0 = Q_impact ε_0.
    # The shock fires at t=0 directly on the AR(1) row; jumps follow
    # the policy function.
    pre_impact  = N_mat                       # 8 × 6
    jump_impact = F @ pre_impact              # 10 × 6
    Q_impact = np.vstack([pre_impact, jump_impact])

    sol.update(F=F, M=M, P=P, N=N_mat, Q_impact=Q_impact)
    return sol


# ------------------------------------------------------------------
# IRF computation
# ------------------------------------------------------------------

def compute_irfs(P: np.ndarray, Q_impact: np.ndarray, horizon: int = 40) -> Dict[str, pd.DataFrame]:
    """Iterate x_h = P x_{h-1} for h = 1..horizon-1, starting from
    x_0 = Q_impact[:, j] for shock j. Returns one DataFrame per shock
    with columns = variable names + derived bS, bL.
    """
    chi_scale = 1.0 / (CAL["chi_bar"] * (1.0 - CAL["chi_bar"]))
    irfs: Dict[str, pd.DataFrame] = {}
    for j, shock in enumerate(SHOCK_NAMES):
        path = np.zeros((horizon, N))
        path[0, :] = Q_impact[:, j].real
        for h in range(1, horizon):
            path[h, :] = P @ path[h - 1, :]
        df = pd.DataFrame(path, columns=VAR_NAMES)
        df.index.name = "h"
        # Derived: current-period bond stocks via eqs (5) and (10)
        df["bL"] = df["lambda_L"] + df["V_liab"] - df["QL"]
        df["bS"] = df["bL"] - chi_scale * df["chi"]
        irfs[shock] = df
    return irfs


# ------------------------------------------------------------------
# Plotting
# ------------------------------------------------------------------

def plot_irf_panel(irf_df: pd.DataFrame, shock_label: str, out_path: Path) -> None:
    """Five-panel plot: π̂, Q̂L, R̂, v̂, î over horizon."""
    target = ["pi", "QL", "R", "v", "i"]
    fig, axes = plt.subplots(1, len(target), figsize=(16, 3.2))
    for ax, var in zip(axes, target):
        ax.plot(irf_df.index, irf_df[var], lw=1.6)
        ax.axhline(0.0, color="0.6", lw=0.6)
        ax.set_title(rf"$\hat{{{var}}}$")
        ax.set_xlabel("h (quarters)")
        ax.grid(alpha=0.3)
    fig.suptitle(f"IRF to {shock_label} shock")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_sensitivity_phi_pi(cal_base: Dict, out_path: Path) -> None:
    """π̂ response to ε^λ for φ_π ∈ {0, 0.3, 0.5, 0.8, 0.95} overlaid."""
    fig, ax = plt.subplots(figsize=(8, 5))
    for phi_pi in (0.0, 0.3, 0.5, 0.8, 0.95):
        cal_mod = {**cal_base, "phi_pi": phi_pi}
        A0, A1, _ = build_system(cal_mod)
        sol = klein_solve(A0, A1, N_PRE)
        if not sol["bk_satisfied"]:
            print(f"  [sensitivity] BK failed for phi_pi={phi_pi}; skipped.")
            continue
        irfs = compute_irfs(sol["P"], sol["Q_impact"], horizon=40)
        ax.plot(irfs["eps_lambda"].index, irfs["eps_lambda"]["pi"],
                lw=1.6, label=rf"$\phi_\pi = {phi_pi}$")
    ax.axhline(0.0, color="0.6", lw=0.6)
    ax.set_xlabel("h (quarters)")
    ax.set_ylabel(r"$\hat\pi_t$")
    ax.set_title(r"Sensitivity of $\hat\pi$ to $\hat\lambda^L$ shock")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


# ------------------------------------------------------------------
# Diagnostics
# ------------------------------------------------------------------

def save_diagnostics(A0, A1, B, sol, irfs, cal, path: Path) -> None:
    diag = dict(
        A0=A0, A1=A1, B=B,
        var_names=VAR_NAMES,
        shock_names=SHOCK_NAMES,
        predetermined_idx=np.arange(N_PRE),
        forward_idx=np.arange(N_PRE, N),
        eigenvalues=sol.get("eigenvalues"),
        n_stable=sol.get("n_stable"),
        n_unstable=sol.get("n_unstable"),
        bk_satisfied=sol.get("bk_satisfied"),
        P=sol.get("P"),
        Q=sol.get("Q_impact"),
        F=sol.get("F"),
        M=sol.get("M"),
        irfs=irfs,
        calibration=cal,
    )
    with open(path, "wb") as f:
        pickle.dump(diag, f)


def print_bk_diagnostics(sol: dict) -> None:
    print()
    print(f"  predetermined: {N_PRE}    forward: {N_FWD}")
    print(f"  n_stable: {sol['n_stable']}    n_unstable: {sol['n_unstable']}    n_unit_circle: {sol['n_unit']}")
    mods = np.abs(sol["eigenvalues"])
    print("  eigenvalue moduli (ascending):")
    for m in np.sort(mods):
        marker = "stable" if m < 1 else ("unit" if np.isclose(m, 1.0) else "unstable")
        print(f"    {m:8.5f}   {marker}")
    if sol["bk_satisfied"]:
        print("  BK OK")
    else:
        print("  BK FAILED")
        delta = N_FWD - sol["n_unstable"]
        if delta > 0:
            print(f"    expected {N_FWD} unstable, found {sol['n_unstable']} — too few unstable.")
            print( "    likely cause: sign error or missing forward-looking term in one equation.")
        elif delta < 0:
            print(f"    expected {N_FWD} unstable, found {sol['n_unstable']} — too many unstable.")
            print( "    likely cause: missing predetermined link or typo in AR(1) block.")


def print_impact_responses(irfs: Dict[str, pd.DataFrame]) -> None:
    """Print h=0 responses of the 12 named endogenous variables."""
    named = ["pi", "i", "c", "y", "QL", "QL_fund", "bS", "bL", "omega", "R", "v", "s"]
    print()
    print("Impact (h=0) responses, all 12 endogenous variables:")
    cols = ["variable"] + SHOCK_NAMES
    rows = []
    for v in named:
        row = [v]
        for sh in SHOCK_NAMES:
            row.append(f"{irfs[sh][v].iloc[0]:+.4f}")
        rows.append(row)
    widths = [max(len(r[i]) for r in [cols] + rows) for i in range(len(cols))]
    print("  " + "  ".join(c.ljust(w) for c, w in zip(cols, widths)))
    for r in rows:
        print("  " + "  ".join(c.ljust(w) for c, w in zip(r, widths)))


def print_selected_horizons(irfs: Dict[str, pd.DataFrame]) -> None:
    print()
    print("Selected horizons (h = 0, 1, 4, 8, 20) for [pi, QL, R, v]:")
    for sh in SHOCK_NAMES:
        print(f"  shock {sh}")
        df = irfs[sh].loc[[0, 1, 4, 8, 20], ["pi", "QL", "R", "v"]]
        for h, row in df.iterrows():
            print(f"    h={h:>3}: " + "  ".join(f"{k}={v:+.4f}" for k, v in row.items()))


def check_stationarity(irfs: Dict[str, pd.DataFrame], h_check: int = 39, tol: float = 0.01) -> None:
    print()
    bad = []
    for sh, df in irfs.items():
        row = df.iloc[h_check]
        for v in VAR_NAMES:
            if abs(row[v]) > tol:
                bad.append((sh, v, row[v]))
    if not bad:
        print(f"  stationarity check: all |x_{{h={h_check}}}| < {tol} for every variable and shock.")
    else:
        print(f"  stationarity check: {len(bad)} variable(s) above tolerance at h={h_check}:")
        for sh, v, val in bad:
            print(f"    [{sh}] {v} = {val:+.5f}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main() -> int:
    print("Building system A0 E_t x_{t+1} = A1 x_t + B ε_t ...")
    A0, A1, B = build_system(CAL)
    print(f"  A0 {A0.shape}  A1 {A1.shape}  B {B.shape}")
    print(f"  variables (18): {VAR_NAMES}")
    print(f"  predetermined indices: {list(range(N_PRE))}")
    print(f"  forward       indices: {list(range(N_PRE, N))}")

    print()
    print("Klein solve (scipy.linalg.ordqz on (A1, A0), sort='iuc') ...")
    try:
        sol = klein_solve(A0, A1, N_PRE)
    except scipy.linalg.LinAlgError as e:
        print(f"  *** LinAlgError: {e}")
        traceback.print_exc()
        save_diagnostics(A0, A1, B, {
            "eigenvalues": np.zeros(N, complex),
            "n_stable": -1, "n_unstable": -1,
            "bk_satisfied": False,
            "P": None, "Q_impact": None, "F": None, "M": None,
        }, {}, CAL, DIAG_PATH)
        print("  matrices A0, A1 dumped to diagnostics.pkl.")
        raise
    except Exception as e:
        print(f"  *** Unexpected error in Klein solve: {e}")
        traceback.print_exc()
        save_diagnostics(A0, A1, B, {
            "eigenvalues": np.zeros(N, complex),
            "n_stable": -1, "n_unstable": -1,
            "bk_satisfied": False,
            "P": None, "Q_impact": None, "F": None, "M": None,
        }, {}, CAL, DIAG_PATH)
        raise

    print_bk_diagnostics(sol)

    if not sol["bk_satisfied"]:
        save_diagnostics(A0, A1, B, sol, {}, CAL, DIAG_PATH)
        print(f"\nBK failed — diagnostics.pkl written with P, Q = None. Stop.")
        return 1

    print()
    print("Computing IRFs (horizon = 40 quarters) ...")
    irfs = compute_irfs(sol["P"], sol["Q_impact"], horizon=40)

    print_impact_responses(irfs)
    print_selected_horizons(irfs)
    check_stationarity(irfs)

    print()
    print("Plotting IRFs and writing CSVs ...")
    shock_to_label = {
        "eps_lambda": "lambda",
        "eps_chi":    "chi",
        "eps_V":      "V",
        "eps_g":      "g",
        "eps_tau":    "tau",
        "eps_i":      "i",
    }
    for shock, label in shock_to_label.items():
        plot_irf_panel(irfs[shock], label, IRFS_DIR / f"irf_{label}.pdf")
        irfs[shock].to_csv(IRFS_DIR / f"irf_{label}.csv")
        print(f"  wrote irfs/irf_{label}.pdf and .csv")

    print()
    print("Sensitivity over φ_π ∈ {0, 0.3, 0.5, 0.8, 0.95} ...")
    plot_sensitivity_phi_pi(CAL, IRFS_DIR / "sensitivity_phi_pi.pdf")
    print("  wrote irfs/sensitivity_phi_pi.pdf")

    print()
    print(f"Saving diagnostics.pkl ...")
    save_diagnostics(A0, A1, B, sol, irfs, CAL, DIAG_PATH)
    print(f"  wrote {DIAG_PATH}")
    print()
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
