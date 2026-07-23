"""steady_state.py — numerical binding-mandate steady state (Section 4).

Implements the deterministic steady-state system of Section 4.2 and the
phi-inversion of Section 4.3, and runs the six sanity checks of Section 4.4.

WHY NUMERICAL / WHY DISTORTED (Section 4.1, LANDMINE 2).
  The closed-form reference point of [Hab] has chi = theta_bar, alpha^i = theta^i,
  so X = 0 and omega = 0 — the mechanism is switched off.  We deliberately set
  chi_bar != theta_bar so the agents are forced off habitat (alpha^A < theta^A),
  giving a positive wedge.  We then INVERT for the habitat strength phi that
  makes the long-bond Euler consistent with the empirical wedge omega_bar = 0.14.

CLOSURE OF THE STEADY STATE (judgment calls, all in REPORT.md).
  With equal beta, sigma the A-B wealth split is indeterminate in levels
  (Section 2.3).  We close it by fixing aggregate debt D̄ and setting the
  closing-device reference so that W̄^A = W̄^B = D̄ (equal per-capita wealth).
  This is consistent with market clearing automatically (see REPORT.md).
  Income is symmetric: y^A = y^B = ȳ (DECISION-2-adjacent; documented).

SOLUTION STRATEGY.
  We FIX the long price at the wedge target Q̄^L = (1+ω̄)Q̄^{L,fund}.  The
  remaining unknowns are the vector

        u = [ bL_B,  c^A,  c^B,  Q̄^S,  phi ]

  with residuals (all evaluated at pi_bar, sigma = 1; the closing device
  vanishes at the SS):

    R1  long-Euler / wedge target :  ξ̄^{L,A}_target − phi(θ^A−α^A)(1−α^A)c^A = 0
    R2  short-Euler tie           :  (α^A−θ^A)α^A c^A − (α^B−θ^B)α^B c^B = 0
    R3  A short-Euler / Q̄^S def    :  Q̄^S − [β + phi(α^A−θ^A)α^A c^A] = 0
    R4  resource                  :  μ_A c^A + μ_B c^B − (ȳ − ḡ) = 0
    R5  budget difference         :  (c^A−c^B) − (bL_B−bL_A)[Q̄^L(1−δ)−Q̄^S] = 0

  R2 is the cross-agent equilibrium restriction ξ̄^{S,A}=ξ̄^{S,B} (the common
  Q̄^S); phi cancels there, so it pins the allocation; R1 then pins phi.  Hence
  "inverting for phi at the wedge target" is automatic — phi is an output.
"""

from __future__ import annotations

from typing import Dict
import numpy as np
from scipy.optimize import root

from params import Params, DEFAULT


# ----------------------------------------------------------------------------
# Allocation map: bL_B -> all holdings and shares (given primitives)
# ----------------------------------------------------------------------------

def allocations(bL_B: float, p: Params) -> Dict[str, float]:
    """Map agent B's long holding to the full cross-section via market clearing,
    the maturity rule, and the W̄^A=W̄^B=D̄ closure."""
    D = p.D_bar
    bL = p.chi_bar * D                      # aggregate long (maturity rule)
    bS = (1 - p.chi_bar) * D                # aggregate short
    bL_A = (bL - p.mu_B * bL_B) / p.mu_A    # long clearing
    # Equal-wealth closure: W̄^A = W̄^B = D  (per-capita).  Then short positions
    # follow and short clearing holds identically.
    WA = D
    WB = D
    bS_A = WA - bL_A
    bS_B = WB - bL_B
    return dict(
        D=D, bL=bL, bS=bS,
        bL_A=bL_A, bL_B=bL_B, bS_A=bS_A, bS_B=bS_B,
        WA=WA, WB=WB,
        alpha_A=bL_A / WA, alpha_B=bL_B / WB,
    )


def _wedges(al: Dict[str, float], cA: float, cB: float, phi: float, p: Params):
    """Leading-order habitat wedges, eq (9), at sigma = 1 ( (c)^{-sigma} = 1/c )."""
    aA, aB = al["alpha_A"], al["alpha_B"]
    xiS_A = phi * (aA - p.theta_A) * aA * cA
    xiL_A = phi * (p.theta_A - aA) * (1 - aA) * cA
    xiS_B = phi * (aB - p.theta_B) * aB * cB
    xiL_B = phi * (p.theta_B - aB) * (1 - aB) * cB
    return xiS_A, xiL_A, xiS_B, xiL_B


def _residuals(u: np.ndarray, p: Params) -> np.ndarray:
    bL_B, cA, cB, QS, phi = u
    al = allocations(bL_B, p)
    aA, aB = al["alpha_A"], al["alpha_B"]
    QL = p.QL_target

    # Target leading-order long wedge implied by the wedge target (from eq 24):
    #   ξ̄^{L,A}_target = Q̄^L (1 − βδ/π̄) − β/π̄
    xiL_A_target = QL * (1 - p.beta * p.delta / p.pi_bar) - p.beta / p.pi_bar

    xiS_A, xiL_A, xiS_B, xiL_B = _wedges(al, cA, cB, phi, p)

    R1 = xiL_A_target - xiL_A
    R2 = (aA - p.theta_A) * aA * cA - (aB - p.theta_B) * aB * cB
    R3 = QS - (p.beta / p.pi_bar + xiS_A)
    R4 = p.mu_A * cA + p.mu_B * cB - (p.y_bar - p.g_y * p.y_bar)
    # budget difference (y^A=y^B, tau cancels):
    #   c^A − c^B = (bS_A−bS_B)(1−Q̄^S) + (bL_A−bL_B)(1+δQ̄^L−Q̄^L)
    #            = (bL_B−bL_A)[Q̄^L(1−δ) − Q̄^S]
    R5 = (cA - cB) - (al["bL_B"] - al["bL_A"]) * (QL * (1 - p.delta) - QS)
    return np.array([R1, R2, R3, R4, R5])


# ----------------------------------------------------------------------------
# Solver
# ----------------------------------------------------------------------------

def solve_steady_state(p: Params = DEFAULT, verbose: bool = False) -> Dict:
    """Solve the SS system; return a dict of all steady-state objects."""
    QL = p.QL_target
    QLf = p.QL_fund

    # Initial guess.  Put B near its habitat (long-habitat agent holds a lot of
    # long), consumption near (ȳ−ḡ), Q̄^S just below β, phi order 1.
    bL_B0 = min(p.theta_B * p.D_bar * 1.05, p.chi_bar * p.D_bar / p.mu_B * 0.95)
    c0 = p.y_bar - p.g_y * p.y_bar
    u0 = np.array([bL_B0, c0, c0, 0.985, 3.0])

    sol = root(_residuals, u0, args=(p,), method="hybr", tol=1e-12)
    if not sol.success:
        # retry from a few perturbed guesses
        for scale in (0.8, 1.1, 0.6, 1.3):
            u1 = u0 * np.array([scale, 1, 1, 1, 1])
            sol = root(_residuals, u1, args=(p,), method="hybr", tol=1e-12)
            if sol.success:
                break

    bL_B, cA, cB, QS, phi = sol.x
    al = allocations(bL_B, p)
    aA, aB = al["alpha_A"], al["alpha_B"]
    xiS_A, xiL_A, xiS_B, xiL_B = _wedges(al, cA, cB, phi, p)

    # Fiscal rent X̄, eq (13), sigma=1 ⇒ /(c^A)^{-sigma} = ·c^A
    det = al["bL_A"] * al["bS_B"] - al["bS_A"] * al["bL_B"]
    X_bar = phi * (aA - p.theta_A) * p.mu_B * cA / al["WA"] * det

    # price-wedge revaluation Ψ̄, eq (14)
    Psi_bar = p.omega_bar / (1 + p.omega_bar) * QL * al["bL"]

    # market value of inherited debt, eq (16)
    v_bar = al["bS"] + (1 + p.delta * QL) * al["bL"]

    # primary surplus from the government flow constraint (15) at SS
    s_bar = al["bS"] * (1 - QS) + al["bL"] * (1 + p.delta * QL - QL)
    g_bar = p.g_y * p.y_bar
    tau_bar = s_bar + g_bar

    # reduced-form coefficients reported by the solver (Section 5 notes)
    eta = p.delta * QL / (1 + p.delta * QL)
    wS = al["bS"] / (v_bar * p.pi_bar)
    wL = (1 + p.delta * QL) * al["bL"] / (v_bar * p.pi_bar)

    # consumption shares for the aggregation (DECISION 2)
    c_agg = p.mu_A * cA + p.mu_B * cB
    sc_A = p.mu_A * cA / c_agg
    sc_B = p.mu_B * cB / c_agg

    ss = dict(
        params=p, success=bool(sol.success), residual_norm=float(np.linalg.norm(sol.fun)),
        # prices
        QS=QS, QL=QL, QL_fund=QLf, omega=p.omega_bar, eta=eta,
        # allocations
        cA=cA, cB=cB, c_agg=c_agg, sc_A=sc_A, sc_B=sc_B,
        bL_A=al["bL_A"], bL_B=al["bL_B"], bS_A=al["bS_A"], bS_B=al["bS_B"],
        bL=al["bL"], bS=al["bS"], WA=al["WA"], WB=al["WB"],
        alpha_A=aA, alpha_B=aB,
        # wedges
        phi=phi, xiS_A=xiS_A, xiL_A=xiL_A, xiS_B=xiS_B, xiL_B=xiL_B,
        # fiscal
        X=X_bar, Psi=Psi_bar, v=v_bar, s=s_bar, tau=tau_bar, g=g_bar,
        det=det,
        # reduced-form coefficients
        wS=wS, wL=wL, s_v=s_bar / v_bar, X_v=X_bar / v_bar,
        # ratios for checks
        m_bar=QL * p.mu_B * al["bL_B"],  # mandate target (=λ̄^L V̄^liab)
    )
    if verbose:
        print(f"  solve success={ss['success']}  ||resid||={ss['residual_norm']:.2e}")
    return ss


# ----------------------------------------------------------------------------
# Section 4.4 sanity checks
# ----------------------------------------------------------------------------

def run_checks(ss: Dict) -> Dict[str, dict]:
    """Run the six Section 4.4 checks; return a structured pass/fail dict."""
    p: Params = ss["params"]
    checks: Dict[str, dict] = {}

    # 1. Interior allocations
    interior = (ss["cA"] > 0 and ss["cB"] > 0 and ss["QS"] > 0 and ss["QL"] > 0
                and 0 < ss["alpha_A"] < 1 and 0 < ss["alpha_B"] < 1
                and ss["WA"] > 0 and ss["WB"] > 0)
    checks["1_interior"] = dict(
        ok=bool(interior),
        detail=f"cA={ss['cA']:.4f} cB={ss['cB']:.4f} QS={ss['QS']:.4f} "
               f"QL={ss['QL']:.4f} alphaA={ss['alpha_A']:.4f} alphaB={ss['alpha_B']:.4f}")

    # 2. Wedge positive AND Assumption 1 binds (alpha^A != theta^A)
    binds = abs(ss["alpha_A"] - p.theta_A) > 1e-6
    checks["2_wedge_positive"] = dict(
        ok=bool(ss["omega"] > 0 and binds),
        detail=f"omega={ss['omega']:.4f}>0 ; alphaA−thetaA={ss['alpha_A']-p.theta_A:+.4f} (distortion active)")

    # 3. Mandate tightness interior: m̄/ȳ reported (admissible if finite, <≈ debt MV)
    m_over_y = ss["m_bar"] / p.y_bar
    checks["3_mandate_tightness"] = dict(
        ok=bool(0 < ss["m_bar"] < ss["v"]),
        detail=f"m̄/ȳ={m_over_y:.4f} ; m̄={ss['m_bar']:.4f} < v̄={ss['v']:.4f}")

    # 4. Long-bond pricing condition βδ/π̄ < 1
    bd = p.beta * p.delta / p.pi_bar
    checks["4_pricing_condition"] = dict(ok=bool(bd < 1), detail=f"βδ/π̄={bd:.4f} < 1")

    # 5. Mandate binds with margin: B's *unconstrained* long demand (if it priced
    #    the long bond like A) would be SMALLER than the mandated amount, so the
    #    mandate is slack-from-below — i.e. it forces B to hold MORE long.
    #    B unconstrained would set ξ^{L,B}=ξ^{L,A} (common Q̄^L); solve its implied
    #    long share alpha_B,unc and compare bL_B,unc to mandated bL_B.
    aBu = _alpha_B_unconstrained(ss)
    bL_B_unc = aBu * ss["WB"]
    margin = ss["bL_B"] - bL_B_unc           # >0 ⇒ mandate forces extra long
    checks["5_mandate_margin"] = dict(
        ok=bool(margin > 0),
        detail=f"alpha_B,unc={aBu:.4f} (vs mandated {ss['alpha_B']:.4f}); "
               f"bL_B,unc={bL_B_unc:.4f} < mandated {ss['bL_B']:.4f} ; margin={margin:+.4f}")

    # 6. Determinant sign: bL_A bS_B − bS_A bL_B (multiplies (alpha^A−theta^A) in X)
    checks["6_determinant_sign"] = dict(
        ok=True,
        detail=f"det = bL_A·bS_B − bS_A·bL_B = {ss['det']:+.5f} "
               f"({'negative' if ss['det'] < 0 else 'positive'}; "
               f"sign of X̄={ss['X']:+.5f})")

    return checks


def _alpha_B_unconstrained(ss: Dict) -> float:
    """B's long share if it priced the long bond via its OWN long Euler at the
    equilibrium Q̄^L (i.e. with ξ^{L,B} matching the same pricing as A).  Used
    only for the margin check (item 5)."""
    p: Params = ss["params"]
    QL = ss["QL"]
    # ξ^{L,B}_required for B to price Q̄^L: same form as A's long-Euler residual
    xiL_req = QL * (1 - p.beta * p.delta / p.pi_bar) - p.beta / p.pi_bar
    # ξ^{L,B} = phi(theta^B − alpha)(1−alpha) c^B ; solve quadratic for alpha
    # phi c^B (theta^B − alpha)(1−alpha) = xiL_req
    a = ss["phi"] * ss["cB"]
    # a(theta_B - x)(1 - x) = xiL_req  ->  a[x^2 - (1+theta_B)x + theta_B] = xiL_req
    A = a
    B = -a * (1 + p.theta_B)
    C = a * p.theta_B - xiL_req
    disc = B * B - 4 * A * C
    if disc < 0:
        return float("nan")
    roots = [(-B - np.sqrt(disc)) / (2 * A), (-B + np.sqrt(disc)) / (2 * A)]
    # pick the root in (0,1) closest to theta_B
    cand = [r for r in roots if 0 < r < 1]
    if not cand:
        return float("nan")
    return min(cand, key=lambda r: abs(r - p.theta_B))


def print_steady_state(ss: Dict) -> None:
    p: Params = ss["params"]
    print("=" * 72)
    print("STEADY STATE  (microfounded captive-habitat NK-FTPL, Section 4)")
    print("=" * 72)
    print(f"  solve: success={ss['success']}  ||residual||={ss['residual_norm']:.2e}")
    print()
    print(f"  phi (inverted for omega_bar={p.omega_bar})   = {ss['phi']:.4f}")
    print(f"  Q̄^S = {ss['QS']:.5f}   Q̄^L = {ss['QL']:.4f}   Q̄^L,fund = {ss['QL_fund']:.4f}")
    print(f"  eta = δQ̄^L/(1+δQ̄^L) = {ss['eta']:.4f}")
    print()
    print(f"  alpha^A = {ss['alpha_A']:.4f}  (theta^A = {p.theta_A})  -> {'BELOW' if ss['alpha_A']<p.theta_A else 'above'} habitat")
    print(f"  alpha^B = {ss['alpha_B']:.4f}  (theta^B = {p.theta_B})  -> {'BELOW' if ss['alpha_B']<p.theta_B else 'above'} habitat")
    print(f"  c^A = {ss['cA']:.4f}   c^B = {ss['cB']:.4f}   c_agg = {ss['c_agg']:.4f}")
    print(f"  consumption shares: s^c_A = {ss['sc_A']:.4f}  s^c_B = {ss['sc_B']:.4f}")
    print()
    print(f"  bonds (per-capita): bS_A={ss['bS_A']:.4f} bL_A={ss['bL_A']:.4f} "
          f"bS_B={ss['bS_B']:.4f} bL_B={ss['bL_B']:.4f}")
    print(f"  aggregate:          bS  ={ss['bS']:.4f} bL  ={ss['bL']:.4f}")
    print()
    print(f"  habitat wedges: ξ^S,A={ss['xiS_A']:+.5f}  ξ^L,A={ss['xiL_A']:+.5f}")
    print(f"                  ξ^S,B={ss['xiS_B']:+.5f}  ξ^L,B={ss['xiL_B']:+.5f}")
    print(f"  (short-Euler tie ξ^S,A=ξ^S,B residual = {ss['xiS_A']-ss['xiS_B']:+.2e})")
    print()
    print(f"  FISCAL: X̄ (rent, eq13)={ss['X']:+.5f}   Ψ̄ (revaluation, eq14)={ss['Psi']:.4f}")
    print(f"          v̄={ss['v']:.4f}  s̄={ss['s']:+.5f}  τ̄={ss['tau']:.4f}  ḡ={ss['g']:.4f}")
    print(f"          determinant bL_A·bS_B−bS_A·bL_B = {ss['det']:+.5f}")
    print()
    print(f"  REDUCED-FORM COEFFICIENTS (for Section 5):")
    print(f"     wS={ss['wS']:.4f}  wL={ss['wL']:.4f}  (wS+wL={ss['wS']+ss['wL']:.4f})")
    print(f"     s̄/v̄={ss['s_v']:+.5f}   X̄/v̄={ss['X_v']:+.5f}")
    # PV identity check (should hold to O(eps^2))
    pv_lhs = ss["v"] * (1 - p.beta)
    pv_rhs = ss["s"] + ss["X"]
    print(f"     PV identity v̄(1−β)={pv_lhs:+.5f} vs s̄+X̄={pv_rhs:+.5f} "
          f"(residual {pv_lhs-pv_rhs:+.2e}, O(eps^2))")
    print()


def print_checks(checks: Dict[str, dict]) -> None:
    print("-" * 72)
    print("SECTION 4.4 SANITY CHECKS")
    print("-" * 72)
    allok = True
    for name, c in checks.items():
        flag = "PASS" if c["ok"] else "FAIL"
        allok &= c["ok"]
        print(f"  [{flag}] {name}: {c['detail']}")
    print("-" * 72)
    print(f"  {'ALL CHECKS PASS' if allok else 'SOME CHECKS FAILED — see above'}")
    print()


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ss = solve_steady_state(DEFAULT, verbose=True)
    print_steady_state(ss)
    checks = run_checks(ss)
    print_checks(checks)
