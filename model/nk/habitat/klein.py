"""klein.py — Klein (1999) generalized-Schur (QZ) solver.

Drop-in reuse of the Entrega III solver (`../nk_ftpl_solve.py`), Section 6.1 of
the spec: only the matrices change.  Solves

        A0 · E_t x_{t+1} = A1 · x_t   (+ shocks via initial state)

with the first `n_pre` variables predetermined and the rest forward-looking.
Returns the policy function F, state law M, full propagator P, the eigenvalue
table, and the BK flag.
"""

from __future__ import annotations

from typing import Optional
import numpy as np
import scipy.linalg


def klein_solve(A0: np.ndarray, A1: np.ndarray, n_pre: int,
                shock_to_state: Optional[dict] = None,
                n_shocks: int = 0) -> dict:
    n = A0.shape[0]
    n_fwd = n - n_pre

    AA, BB, alpha, beta_, Q_orth, Z = scipy.linalg.ordqz(
        A1, A0, sort="iuc", output="complex")

    with np.errstate(divide="ignore", invalid="ignore"):
        eigenvalues = alpha / beta_
    moduli = np.abs(eigenvalues)
    n_stable = int(np.sum(moduli < 1.0 - 1e-9))
    n_unit = int(np.sum(np.abs(moduli - 1.0) <= 1e-6))
    n_unstable = int(np.sum(moduli > 1.0 + 1e-9))
    bk_satisfied = (n_unstable == n_fwd) and (n_stable == n_pre)

    sol = dict(eigenvalues=eigenvalues, moduli=moduli,
               n_stable=n_stable, n_unstable=n_unstable, n_unit=n_unit,
               n_pre=n_pre, n_fwd=n_fwd, bk_satisfied=bk_satisfied,
               F=None, M=None, P=None, Q_impact=None)
    if not bk_satisfied:
        return sol

    Z11 = Z[:n_pre, :n_pre]
    Z21 = Z[n_pre:, :n_pre]
    AA_ss = AA[:n_pre, :n_pre]
    BB_ss = BB[:n_pre, :n_pre]
    Z11_inv = scipy.linalg.solve(Z11, np.eye(n_pre, dtype=Z11.dtype))
    BB_ss_inv = scipy.linalg.solve(BB_ss, np.eye(n_pre, dtype=BB_ss.dtype))

    F = np.real(Z21 @ Z11_inv)                      # n_fwd × n_pre
    M = np.real(Z11 @ BB_ss_inv @ AA_ss @ Z11_inv)  # n_pre × n_pre

    P = np.zeros((n, n))
    P[:n_pre, :n_pre] = M
    P[n_pre:, :n_pre] = F @ M

    Q_impact = None
    if shock_to_state is not None and n_shocks > 0:
        pre_impact = np.zeros((n_pre, n_shocks))
        for j, st in enumerate(shock_to_state):
            pre_impact[st, j] = 1.0
        jump_impact = F @ pre_impact
        Q_impact = np.vstack([pre_impact, jump_impact])

    sol.update(F=F, M=M, P=P, Q_impact=Q_impact)
    return sol


def eigenvalue_table(sol: dict) -> str:
    lines = []
    lines.append(f"  predetermined: {sol['n_pre']}    forward: {sol['n_fwd']}")
    lines.append(f"  n_stable: {sol['n_stable']}   n_unstable: {sol['n_unstable']}   "
                 f"n_unit: {sol['n_unit']}")
    lines.append("  eigenvalue moduli (ascending):")
    for m in np.sort(sol["moduli"]):
        if np.isinf(m):
            tag = "inf (static)"
        elif m < 1 - 1e-9:
            tag = "stable"
        elif abs(m - 1) <= 1e-6:
            tag = "unit"
        else:
            tag = "unstable"
        ms = "   inf" if np.isinf(m) else f"{m:8.5f}"
        lines.append(f"    {ms}   {tag}")
    lines.append("  BK OK" if sol["bk_satisfied"] else "  BK FAILED")
    return "\n".join(lines)
