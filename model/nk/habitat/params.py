"""params.py — calibration for the microfounded captive-habitat NK-FTPL model.

This is the parameter set for the *microfounded* spec (`habitat_nk_spec.pdf`,
"A Captive-Habitat FTPL Model Embedded in New Keynesian Structure"), NOT the
Entrega III reduced form in `../nk_ftpl_solve.py`.

Conventional parameters follow Section 4.3 of the spec.  The structural
parameters that the spec leaves open (population shares, the two habitats, the
debt level and wealth split) are set here with explicit JUDGMENT CALLS; every
one is documented in REPORT.md.  Where a number is inherited from Entrega III /
the §5.2 clean-window calibration it is flagged.

The habitat penalty strength `phi` is NOT a free parameter: it is the object the
steady-state solver inverts for so that the model reproduces the empirical wedge
target omega_bar (Section 4.3).  It therefore does not appear here.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, replace


@dataclass(frozen=True)
class Params:
    # ---- Conventional macro / pricing parameters (Section 4.3, fixed) -------
    beta: float = 0.99      # discount factor (literature standard, §3.4)
    sigma: float = 1.0      # inverse IES (log utility)
    delta: float = 0.96     # perpetuity decay (inherited)
    pi_bar: float = 1.0     # gross inflation target
    theta_C: float = 0.75   # Calvo non-reoptimisation probability
    phi_pi: float = 0.5     # passive Taylor coefficient (<1)

    # ---- Habitat / two-agent block (JUDGMENT CALLS — see REPORT.md) ---------
    mu_A: float = 0.5       # population share of short-habitat agent A
    mu_B: float = 0.5       # population share of long-habitat agent B
    theta_A: float = 0.25   # A's preferred long share (short-habitat)
    theta_B: float = 0.55   # B's preferred long share (long-habitat)
    #   theta_bar (equal-wealth weights) = 0.40 > chi_bar = 0.353, so both
    #   agents are pushed *below* habitat and the long-Euler wedge is positive.

    # ---- Supply side (Section 4.3) ------------------------------------------
    chi_bar: float = 0.353  # aggregate fresh-bond long-quantity share (E3 §5.2)
    D_bar: float = 0.459    # aggregate per-capita real debt stock b^S + b^L.
    #   Chosen so the implied market value of debt v̄/ȳ ≈ 4 (≈100% of annual GDP
    #   at quarterly ȳ = 1).  Pure level normalisation; documented in REPORT.md.

    # ---- Income / fiscal block ----------------------------------------------
    y_bar: float = 1.0      # output normalisation
    g_y: float = 0.20       # ḡ/ȳ government spending share

    # ---- Calibration target -------------------------------------------------
    omega_bar: float = 0.14  # §5.2 clean-window headline wedge (2021-2024)

    # ---- Closing device (Section 2.3, DECISION 1) ---------------------------
    #   Recommended spec (i): convex portfolio-holding cost.  Implemented in the
    #   linear block as a small wealth-elastic short-return wedge (eq 6).
    psi: float = 1e-3       # closing-device elasticity (small)

    # ---- Policy / market-structure knobs (sessions 2–3, see REPORT.md) ------
    #   accom: government accommodation of the captive mandate via long issuance.
    #     0 = Decision A (mandate redistributes a fixed aggregate long stock;
    #         agent A is squeezed off habitat → wedge widens, long price rises).
    #     1 = Entrega III rule (aggregate long supply expands with the mandate).
    accom: float = 0.0
    #   theta_tp: Vayanos–Vila term premium sensitivity, τ̂p = θ_tp·b̂^{L,A}.
    #     Structural map θ_tp = D·τ̄p (duration × steady-state term premium).
    #     CALIBRATED to Bloomberg gilt data (calibration/Bloomberg_Data_Pull (1)):
    #     D ≈ 20.2q (model duration from δ=0.96); τ̄p ≈ 1.0%/yr — between the
    #     full-sample (2004-2025) 5y–bank spread (0.36%) and 10y–1y spread (0.90%);
    #     20y–bank is 1.27%.  θ_tp = 20.2 × (0.010/4) ≈ 0.05.  Sensitivity band
    #     [0.025, 0.064] for τ̄p ∈ [0.5%, 1.27%]/yr.
    theta_tp: float = 0.0505
    #   gamma_rep: Cochrane s-shaped / partial-repayment surplus on lagged debt
    #     (path-smoothing; negligible on impact).  Default off.
    gamma_rep: float = 0.0

    # ---- Exogenous AR(1) persistence ----------------------------------------
    rho_lambda: float = 0.7
    rho_chi: float = 0.7
    rho_V: float = 0.7
    rho_g: float = 0.7
    rho_tau: float = 0.7
    rho_i: float = 0.7

    # ---- Derived ------------------------------------------------------------
    @property
    def kappa(self) -> float:
        """NKPC slope, eq (20)."""
        return (1 - self.theta_C) * (1 - self.beta * self.theta_C) * self.sigma / self.theta_C

    @property
    def QL_fund(self) -> float:
        """Fundamental long price, eq (30): β/π̄ / (1 − βδ/π̄)."""
        return (self.beta / self.pi_bar) / (1 - self.beta * self.delta / self.pi_bar)

    @property
    def QL_target(self) -> float:
        """Long price at the wedge target, eq (31): (1+ω̄)·Q̄^{L,fund}."""
        return (1 + self.omega_bar) * self.QL_fund

    @property
    def theta_bar(self) -> float:
        """Wealth-weighted average habitat.  At the W̄^A=W̄^B closure the wealth
        weights equal the population shares."""
        return self.mu_A * self.theta_A + self.mu_B * self.theta_B

    def with_(self, **kw) -> "Params":
        return replace(self, **kw)

    def as_dict(self) -> dict:
        return asdict(self)


DEFAULT = Params()


if __name__ == "__main__":
    p = DEFAULT
    print("Q^L_fund      =", round(p.QL_fund, 4))
    print("Q^L_target    =", round(p.QL_target, 4))
    print("theta_bar     =", round(p.theta_bar, 4), "  chi_bar =", p.chi_bar,
          "  gap =", round(p.theta_bar - p.chi_bar, 4))
    print("kappa         =", round(p.kappa, 4))
    print("beta*delta/pi =", round(p.beta * p.delta / p.pi_bar, 4), "(<1 check)")
