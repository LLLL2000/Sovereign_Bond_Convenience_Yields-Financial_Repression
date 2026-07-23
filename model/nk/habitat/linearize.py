"""linearize.py — log-linearized microfounded captive-habitat NK-FTPL (Section 5).

Builds A0, A1 of  A0 E_t x_{t+1} = A1 x_t  for the Klein/QZ solver, with
coefficients from the numerical steady state (steady_state.py).

COMPACT form (DECISION 3) + marginal-agent IS (DECISION 2, option 1 — the
spec's recommended baseline):
  * agent A's short Euler IS the IS curve; agent B's consumption is residual via
    the resource constraint (B's flow budget is redundant by Walras's law, so it
    is dropped — see REPORT.md);
  * aggregate current bond stocks follow the captive-demand issuance rule
    b̂L = λ̂L + V̂liab − Q̂L (the Entrega III closure, reinterpreted: the
    government sizes long issuance to captive demand), so the augmented FTPL
    identity (with the structural rent X̂) is the independent price-level
    equation — exactly as in Entrega III;
  * agent-level portfolio objects (α̂^A, the determinant in the rent) are
    reconstructed analytically from the retained variables.

VARIABLE ORDER (N = 20)
  States (predetermined, 9):
     0 bS_lag   1 bL_lag   2 WtA  (relative-wealth, level dev)
     3 lambda_L 4 chi 5 V_liab 6 g 7 tau 8 u_i   (six AR(1))
  Jumps (forward-looking, 11):
     9 cA 10 cB 11 y 12 pi 13 i 14 QL 15 QL_fund 16 omega 17 X 18 v 19 s

UPGRADES vs the Entrega III reduced form (../nk_ftpl_solve.py):
  * ω̂ is endogenous & forward-looking, driven by agent A's LONG habitat wedge
    (row R5) — not a reduced-form rent identity;
  * the fiscal rent X̂ (row R6) is the structural cross-sectional determinant of
    eq (13), front factor α^A/(α^A−θ^A) from the SS;
  * relative-wealth state WtA with a closing device places the A–B distribution
    root at 1−ε just inside the unit circle.
"""

from __future__ import annotations

from typing import Dict
import numpy as np

from params import Params
from steady_state import solve_steady_state

VAR = ["bS_lag", "bL_lag", "WtA",
       "lambda_L", "chi", "V_liab", "g", "tau", "u_i",
       "cA", "cB", "y", "pi", "i", "QL", "QL_fund", "omega", "X", "v", "s"]
IDX = {v: i for i, v in enumerate(VAR)}
N = len(VAR)            # 20
N_PRE = 9
N_FWD = N - N_PRE       # 11

SHOCKS = ["eps_lambda", "eps_chi", "eps_V", "eps_g", "eps_tau", "eps_i"]
SHOCK_TO_STATE = [IDX["lambda_L"], IDX["chi"], IDX["V_liab"],
                  IDX["g"], IDX["tau"], IDX["u_i"]]


def lin(*terms) -> Dict[int, float]:
    e: Dict[int, float] = {}
    for name, c in terms:
        e[IDX[name]] = e.get(IDX[name], 0.0) + c
    return e


def scale(expr: Dict[int, float], k: float) -> Dict[int, float]:
    return {i: c * k for i, c in expr.items()}


def add(*exprs: Dict[int, float]) -> Dict[int, float]:
    out: Dict[int, float] = {}
    for e in exprs:
        for i, c in e.items():
            out[i] = out.get(i, 0.0) + c
    return out


def build(ss: Dict, p: Params, psi: float | None = None, phi_scale: float = 1.0,
          agg_closure: str = "partial", accom: float | None = None,
          gamma_v: float = 0.0, gamma_rep: float | None = None,
          theta_tp: float | None = None):
    """Return (A0, A1, ss, meta).  A0 E_t x_{t+1} = A1 x_t.

    phi_scale ∈ [0,1] scales the habitat channel (the wedge-law forcing and the
    rent's entry into the FTPL identity).  phi_scale=0 is the φ→0 counterfactual
    of Section 6.5 (the rent channel is shut).

    agg_closure selects how the AGGREGATE current bond stocks are pinned:
      'mandate' — Entrega III rule b̂L = λ̂L+V̂liab−Q̂L (aggregate long supply
                  EXPANDS one-for-one with the captive mandate).  Under this rule
                  agent A is never squeezed off habitat, so the wedge response is
                  weak and the long price falls (the v1 problem).
      'value'   — DECISION A: the aggregate long supply follows the government's
                  maturity policy on its total debt (pinned by the FTPL value v and
                  χ), NOT the mandate.  The mandate then merely REDISTRIBUTES a
                  roughly-fixed aggregate long stock from A to B, squeezing A off
                  habitat and widening the wedge — the actual model mechanism.
    """
    if psi is None:
        psi = p.psi
    if accom is None:
        accom = getattr(p, "accom", 0.0)
    if gamma_rep is None:
        gamma_rep = getattr(p, "gamma_rep", 0.0)
    if theta_tp is None:
        theta_tp = getattr(p, "theta_tp", 0.0)
    b, sig, dlt = p.beta, p.sigma, p.delta
    eta, kap, phi_pi = ss["eta"], p.kappa, p.phi_pi
    QS, QL, QLf = ss["QS"], ss["QL"], ss["QL_fund"]
    bS, bL = ss["bS"], ss["bL"]
    bS_A, bL_A, bS_B, bL_B = ss["bS_A"], ss["bL_A"], ss["bS_B"], ss["bL_B"]
    WA = ss["WA"]
    aA = ss["alpha_A"]
    cA, cB = ss["cA"], ss["cB"]
    phi = ss["phi"]
    xiSA, xiLA = ss["xiS_A"], ss["xiL_A"]
    v_bar, X_bar, Dn = ss["v"], ss["X"], ss["det"]
    muA, muB = p.mu_A, p.mu_B
    wS, wL = ss["wS"], ss["wL"]
    s_v = 1.0 / v_bar
    X_v = X_bar / v_bar
    sc_A, sc_B = ss["sc_A"], ss["sc_B"]
    c_agg, g_bar, tau_bar = ss["c_agg"], ss["g"], ss["tau"]
    kchi = 1.0 / (p.chi_bar * (1 - p.chi_bar))
    Delta = ss["omega"] * QLf                       # Δ̄ = ω̄ Q̄^{L,fund}

    # --- aggregate current stocks ---------------------------------------------
    if agg_closure == "partial":
        # DECISION A (the headline closure):  b̂L = accom·(λ̂L+V̂liab) − Q̂L.
        #   accom=1 → Entrega III full-accommodation rule (aggregate long EXPANDS
        #            one-for-one with the mandate; agent A is NOT squeezed → weak
        #            wedge, long price falls — the v1 problem).
        #   accom=0 → price-responsive issuance with NO mandate accommodation: the
        #            mandate (which forces B's long up) purely REDISTRIBUTES the
        #            aggregate long stock, so A holds LESS and is pushed further
        #            below habitat → the wedge widens and the long price rises.
        #   The −Q̂L term (debt-management responding to the long price) is kept in
        #   all cases; it carries the asset-price/debt-revaluation unstable root
        #   that delivers FTPL determinacy.
        bLhat = lin(("lambda_L", accom), ("V_liab", accom), ("QL", -1.0))
    elif agg_closure == "mandate":
        # Entrega III captive-demand issuance rule (== partial with accom=1)
        bLhat = lin(("lambda_L", 1.0), ("V_liab", 1.0), ("QL", -1.0))
    elif agg_closure == "value":
        # aggregate long follows maturity policy on total debt, pinned by the
        # FTPL value v and χ — NOT the mandate.  (Breaks determinacy in v1.)
        bLhat = lin(("v", 1.0), ("chi", bS * kchi / v_bar),
                    ("QL", -dlt * QL * bL / v_bar))
    elif agg_closure == "fixed_total":
        # DECISION A: the government does NOT accommodate the mandate with new
        # long issuance — the aggregate real debt quantity is fixed in the short
        # run and only the maturity policy χ reshuffles it.  Then the mandate
        # (which forces B to hold more long) purely REDISTRIBUTES the fixed
        # aggregate long stock, so agent A holds LESS (the squeeze) and is pushed
        # further below habitat → the wedge widens.  Coefficients from the
        # fixed-total maturity linearisation: b̂L = χ̂/χ̄, b̂S = −χ̂/(1−χ̄),
        # which satisfy b̂L−b̂S = κχ χ̂.
        bLhat = lin(("chi", 1.0 / p.chi_bar))
    else:
        raise ValueError(f"unknown agg_closure {agg_closure!r}")
    bShat = add(bLhat, lin(("chi", -kchi)))

    # --- agent-level reconstruction ------------------------------------------
    bLB = lin(("lambda_L", 1.0), ("V_liab", 1.0), ("QL", -1.0))         # mandate
    bLA = scale(add(scale(bLhat, bL), scale(bLB, -muB * bL_B)),
                1.0 / (muA * bL_A))                                     # long clearing
    WAhat = lin(("WtA", 1.0 / WA))                                      # ŴA = WtA/W̄A
    bSA = scale(add(scale(WAhat, WA), scale(bLA, -bL_A)), 1.0 / bS_A)   # W^A=bS_A+bL_A
    bSB = scale(add(scale(bShat, bS), scale(bSA, -muA * bS_A)),
                1.0 / (muB * bS_B))                                     # short clearing
    aAhat = add(bLA, scale(WAhat, -1.0))                               # α̂^A = b̂L_A − ŴA

    # --- habitat wedges (level deviations), eq (9) linearised ----------------
    dxiSA = add(scale(aAhat, phi * cA * (2 * aA - p.theta_A) * aA), lin(("cA", xiSA)))
    dxiLA = add(scale(aAhat, phi * cA * (2 * aA - 1 - p.theta_A) * aA), lin(("cA", xiLA)))

    # DETERMINACY CHOICE (v1, documented in REPORT.md, exactly the §6.2
    # subtlety): in the FORWARD wedge law (R5) the long habitat wedge is driven
    # by the mandate/wealth reallocation, NOT by agent A's contemporaneous
    # own-price feedback.  Including the −Q̂L term inside α̂^A there makes the
    # wedge partly self-fulfilling and pulls its forward root from 1/(βδ)≈1.05
    # below 1 (indeterminacy).  We therefore strip the Q̂L term from α̂^A *only*
    # in R5; it is retained everywhere else (rent R6, clearing, shares).
    aAhat_R5 = {i: c for i, c in aAhat.items() if i != IDX["QL"]}
    dxiLA_R5 = add(scale(aAhat_R5, phi * cA * (2 * aA - 1 - p.theta_A) * aA),
                   lin(("cA", xiLA)))

    A0 = np.zeros((N, N))
    A1 = np.zeros((N, N))

    def put(row, A0row, A1row):
        for i, c in A0row.items():
            A0[row, i] += c
        for i, c in A1row.items():
            A1[row, i] += c

    zS = 1.0 / (b * sig)                # ζ^S scaling on the level short wedge

    # R0 — IS / agent-A short Euler:
    #   E cA' + (1/σ)E π' = cA + (1/σ)i − ζS dξ^{S,A}
    #   The closing-device feedback −ψW̃A (spec row 1) is omitted in v1: with the
    #   marginal-agent IS (DECISION 2 option 1) the A–B distribution is a benign
    #   sideshow, and the +ψWtA term perturbs the near-unit WtA root and flips
    #   the BK count at ψ=1e-3.  WtA remains a stationary state (root 1−ψ) driven
    #   by the consumption differential but not fed back — see R13 and REPORT.md.
    put(0, lin(("cA", 1.0), ("pi", 1.0 / sig)),
        add(lin(("cA", 1.0), ("i", 1.0 / sig)), scale(dxiSA, -zS)))

    # R1 — NKPC:  β E π' = π − κ y
    put(1, lin(("pi", b)), lin(("pi", 1.0), ("y", -kap)))

    # R2 — Taylor rule (static):  0 = i − φπ π − u_i
    put(2, {}, lin(("i", 1.0), ("pi", -phi_pi), ("u_i", -1.0)))

    # R3 — fundamental long price:
    #   σ E cA' + E π' − η E QL_fund' = σ cA − QL_fund
    put(3, lin(("cA", sig), ("pi", 1.0), ("QL_fund", -eta)),
        lin(("cA", sig), ("QL_fund", -1.0)))

    # R4 — long-price identity with a VAYANOS–VILA term premium (static):
    #   Q̂L = Q̂L_fund + ω̂ − τp ,   τp = θ_tp · b̂^{L,A}
    #   θ_tp = a·D²·σ_r²  (arbitrageur risk-bearing × duration² × rate variance).
    #   Agent A is the arbitrageur; τp is the duration-risk premium it demands.
    #   When the mandate forces B to hold more long, market clearing makes A hold
    #   LESS (b̂^{L,A}↓), so the premium it requires FALLS and the long price RISES
    #   — the captive-demand-compresses-the-term-premium channel (financial
    #   repression).  θ_tp=0 recovers the no-premium baseline.
    put(4, {}, add(lin(("QL", 1.0), ("QL_fund", -1.0), ("omega", -1.0)),
                   scale(bLA, theta_tp)))

    # R5 — wedge law (agent-A long Euler):  βδ E ω' = ω − dξ^{L,A}/Δ̄
    put(5, lin(("omega", b * dlt)),
        add(lin(("omega", 1.0)), scale(dxiLA_R5, -phi_scale / Delta)))

    # R6 — fiscal rent X̂ (static), eq (13):
    #   X̂ = [α^A/(α^A−θA)] α̂A + det_elast + σ ĉA − ŴA
    det_elast = scale(add(scale(add(bLA, bSB), bL_A * bS_B),
                          scale(add(bSA, bLB), -bS_A * bL_B)), 1.0 / Dn)
    X_rhs = add(scale(aAhat, aA / (aA - p.theta_A)), det_elast,
                lin(("cA", sig)), scale(WAhat, -1.0))
    put(6, {}, add(lin(("X", 1.0)), scale(X_rhs, -1.0)))

    # R7 — real debt market value (static), row 13:
    #   v = wS(bS_lag − π) + wL(bL_lag + η QL − π);  coeff on π = −(wS+wL) = −1
    put(7, {}, lin(("v", 1.0), ("bS_lag", -wS), ("bL_lag", -wL),
                   ("pi", wS + wL), ("QL", -wL * eta)))

    # R8 — augmented FTPL identity, row 14:
    #   β E v' + β E π' = v − (1/v̄) s − (X̄/v̄) X̂ + β i
    put(8, lin(("v", b), ("pi", b)),
        lin(("v", 1.0), ("s", -s_v), ("X", -X_v * phi_scale), ("i", b)))

    # R9 — primary surplus with (i) a Bohn (1998) contemporaneous debt feedback
    # and (ii) a COCHRANE s-shaped / partial-repayment term on LAGGED (accumulated)
    # debt:
    #   s = τ̄ τ̂ − ḡ ĝ + γ_v · v̂ + γ_rep · (wS·bŜ_lag + wL·bL̂_lag)
    # γ_rep>0 makes future surpluses rise with ACCUMULATED inherited debt, so a
    # deficit/revaluation today is partly repaid later — Cochrane's device that
    # turns a one-off price-level jump into a smooth, drawn-out inflation and avoids
    # the "deficits → deflation" puzzle.  It operates through the EXPECTED surplus
    # path (lagged, predetermined debt), NOT a contemporaneous feedback, so it
    # shapes dynamics without tipping the active/passive (Leeper) classification
    # for small γ_rep.  Both default to 0.
    put(9, {}, lin(("s", 1.0), ("tau", -tau_bar), ("g", g_bar), ("v", -gamma_v),
                   ("bS_lag", -gamma_rep * wS), ("bL_lag", -gamma_rep * wL)))

    # R10 — resource / aggregation (static):  c̄ ĉ + ḡ ĝ = ȳ ŷ, ĉ=sc_A ĉA+sc_B ĉB
    put(10, {}, lin(("cA", c_agg * sc_A), ("cB", c_agg * sc_B),
                    ("g", g_bar), ("y", -p.y_bar)))

    # R11 — bS_lag law:  bS_lag' = b̂S_t
    put(11, lin(("bS_lag", 1.0)), bShat)
    # R12 — bL_lag law:  bL_lag' = b̂L_t
    put(12, lin(("bL_lag", 1.0)), bLhat)
    # R13 — relative-wealth law (closing device, DECISION 1 variant ii):
    #   WtA' = (1−ψ) WtA − κ_rev (λ̂L + V̂liab)
    #   Own-wealth-elastic ⇒ guaranteed root 1−ψ just inside the unit circle
    #   (LANDMINE 1 resolved).  Driven by the long-bond REVALUATION channel: a
    #   mandate tightening (λ,V) raises the long price, revaluing the long-habitat
    #   agent B up relative to A, so A's relative wealth falls.  The driver is
    #   state-to-state (predetermined → predetermined), so it does NOT perturb the
    #   forward/jump determinacy and the macro IRFs are invariant as ψ→0 (the
    #   spec's test).  κ_rev = (b̄L_B − b̄L_A)/W̄A · η  (differential long exposure
    #   × duration).  WtA does not feed back into the macro block in v1 (benign
    #   closing device); the full two-way A–B dynamics are a v2 item.
    kappa_rev = (bL_B - bL_A) / WA * eta
    put(13, lin(("WtA", 1.0)),
        lin(("WtA", 1.0 - psi), ("lambda_L", -kappa_rev), ("V_liab", -kappa_rev)))

    # R14–R19 — AR(1) laws
    ar1 = [("lambda_L", p.rho_lambda), ("chi", p.rho_chi), ("V_liab", p.rho_V),
           ("g", p.rho_g), ("tau", p.rho_tau), ("u_i", p.rho_i)]
    for k, (name, rho) in enumerate(ar1):
        put(14 + k, lin((name, 1.0)), lin((name, rho)))

    meta = dict(bLhat=bLhat, bShat=bShat, bLA=bLA, bLB=bLB, bSA=bSA, bSB=bSB,
                aAhat=aAhat, WAhat=WAhat, inflation_coeff_R7=-(wS + wL))
    return A0, A1, ss, meta


def build_default(p: Params, psi: float | None = None, phi_scale: float = 1.0,
                  agg_closure: str = "partial", accom: float = 0.0):
    ss = solve_steady_state(p)
    return build(ss, p, psi=psi, phi_scale=phi_scale,
                 agg_closure=agg_closure, accom=accom)
