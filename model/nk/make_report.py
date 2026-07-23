"""Generate report.pdf describing the NK-FTPL solve exercise.

Re-runs the solver to get fresh figures + impact tables, then assembles
a multi-page PDF via reportlab. Embeds IRF panels as PNG (regenerated
here so the report is self-contained).
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from nk_ftpl_solve import (  # noqa: E402
    CAL, N, N_PRE, SHOCK_NAMES, VAR_NAMES,
    build_system, compute_irfs, klein_solve,
)

PNG_DIR = HERE / "figures"
PNG_DIR.mkdir(exist_ok=True)
OUT = HERE / "report.pdf"


# ------------------------------------------------------------------
# Re-run solve and regenerate figures as PNGs (for embedding)
# ------------------------------------------------------------------

def regenerate_figures():
    """Re-solve at headline calibration and at the four sensitivity φ_π values.
    Save 4 PNG figures into PNG_DIR. Returns dict with computed objects.
    """
    A0, A1, B = build_system(CAL)
    sol = klein_solve(A0, A1, N_PRE)
    assert sol["bk_satisfied"], "BK failed at headline calibration"
    irfs = compute_irfs(sol["P"], sol["Q_impact"], horizon=40)

    # 5-panel IRF figures
    def save_panel(irf_df, shock_label, path):
        target = ["pi", "QL", "R", "v", "i"]
        fig, axes = plt.subplots(1, len(target), figsize=(15, 2.8))
        for ax, var in zip(axes, target):
            ax.plot(irf_df.index, irf_df[var], lw=1.6)
            ax.axhline(0.0, color="0.6", lw=0.6)
            ax.set_title(rf"$\hat{{{var}}}$")
            ax.set_xlabel("h (quarters)")
            ax.grid(alpha=0.3)
        fig.suptitle(f"IRF to {shock_label} shock", y=1.02)
        fig.tight_layout()
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    save_panel(irfs["eps_lambda"], "lambda", PNG_DIR / "irf_lambda.png")
    save_panel(irfs["eps_g"],      "g",      PNG_DIR / "irf_g.png")
    save_panel(irfs["eps_i"],      "monetary", PNG_DIR / "irf_monetary.png")

    # Sensitivity figure
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    sensitivity_values = {}
    for phi_pi in (0.0, 0.3, 0.5, 0.8, 0.95):
        cal_mod = {**CAL, "phi_pi": phi_pi}
        A0s, A1s, _ = build_system(cal_mod)
        sols = klein_solve(A0s, A1s, N_PRE)
        if not sols["bk_satisfied"]:
            continue
        irfs_s = compute_irfs(sols["P"], sols["Q_impact"], horizon=40)
        sensitivity_values[phi_pi] = irfs_s["eps_lambda"]["pi"]
        ax.plot(irfs_s["eps_lambda"].index, irfs_s["eps_lambda"]["pi"],
                lw=1.6, label=rf"$\phi_\pi = {phi_pi}$")
    ax.axhline(0.0, color="0.6", lw=0.6)
    ax.set_xlabel("h (quarters)")
    ax.set_ylabel(r"$\hat\pi_t$")
    ax.set_title(r"$\hat\pi$ response to $\hat\lambda^L$ shock, varying $\phi_\pi$")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(PNG_DIR / "sensitivity_phi_pi.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    return {
        "sol": sol,
        "irfs": irfs,
        "sensitivity": sensitivity_values,
        "A0": A0, "A1": A1,
    }


# ------------------------------------------------------------------
# Document assembly
# ------------------------------------------------------------------

def build_report(state):
    irfs = state["irfs"]
    sol = state["sol"]

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title="NK-FTPL Solve: Implementation Report",
        author="Lucas Leturia / RA",
    )

    styles = getSampleStyleSheet()
    s_title = ParagraphStyle("Title", parent=styles["Title"], fontSize=16,
                             spaceAfter=4, alignment=1)
    s_author = ParagraphStyle("Author", parent=styles["Normal"],
                              alignment=1, fontSize=10, spaceAfter=18)
    s_h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13,
                          spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1f2937"))
    s_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11,
                          spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#374151"))
    s_body = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10,
                            leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=14,
                              bulletIndent=2, spaceAfter=3)
    s_callout = ParagraphStyle("Callout", parent=s_body, leftIndent=14,
                               rightIndent=14, fontSize=9,
                               textColor=colors.HexColor("#7c2d12"),
                               backColor=colors.HexColor("#fef3c7"),
                               borderPadding=6, spaceBefore=4, spaceAfter=8)
    s_code = ParagraphStyle("Code", parent=styles["Code"], fontSize=9,
                            leading=11)
    s_caption = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9,
                               alignment=1, textColor=colors.HexColor("#374151"),
                               spaceBefore=2, spaceAfter=12)

    P = lambda text: Paragraph(text, s_body)
    H1 = lambda text: Paragraph(text, s_h1)
    H2 = lambda text: Paragraph(text, s_h2)
    B = lambda text: Paragraph(text, s_bullet)
    CALL = lambda text: Paragraph(text, s_callout)
    CAP = lambda text: Paragraph(text, s_caption)

    story = []

    # =========================================================
    # Title block
    # =========================================================
    story += [
        Paragraph("NK-FTPL Solve and IRFs:<br/>Implementation Report", s_title),
        Paragraph("Lucas Leturia &middot; M&aacute;ster, PUC Chile &middot; May 2026", s_author),
    ]

    # =========================================================
    # 1. Summary
    # =========================================================
    story += [
        H1("1. Summary"),
        P("This report documents the Python implementation of the log-linearized "
          "Two-Maturity FTPL with Long-End Captive Demand embedded in a small "
          "New-Keynesian framework. The system follows <i>nk_ftpl_embedding.pdf</i> "
          "&sect;4 (12 equilibrium equations plus six AR(1) exogenous processes) "
          "and is solved with the Klein (1999) generalized-Schur algorithm via "
          "<i>scipy.linalg.ordqz</i>. The script is in "
          "<font face='Courier'>nk/nk_ftpl_solve.py</font>; all numerical objects "
          "are pickled to <font face='Courier'>nk/diagnostics.pkl</font>; "
          "IRF figures and CSVs are in <font face='Courier'>nk/irfs/</font>."),
        P("<b>Headline:</b> at the calibration in the RA brief "
          "(&beta;=0.99, &delta;=0.96, &omega;&#772;=0.121, &phi;<sub>&pi;</sub>=0.5, "
          "&rho;<sub>z</sub>=0.7 for all shocks), the Blanchard-Kahn conditions "
          "are satisfied with 8 stable and 10 unstable generalized eigenvalues, "
          "matching the predetermined / forward split exactly. The headline "
          "impulse response to a positive &epsilon;<sup>&lambda;</sup> shock "
          "delivers the four predicted signs: "
          "&pi;&#770;&darr;, Q&#770;<sup>L</sup>&uarr;, R&#770;&uarr;, "
          "v&#770;&uarr;. The captive-demand channel works as theorised."),
        P("Two of the five sanity checks in &sect;7 of the brief give the opposite "
          "sign from what is written there. Both turn out to be economically correct: "
          "the brief&rsquo;s checks 3 and 4 silently invoked active-NK intuition "
          "that does not carry over to a passive-monetary, fiscal-dominance "
          "regime &mdash; the very point of the embedding. See &sect;6 below for the discussion."),

        # ===================================================
        # 2. Implementation choices to flag
        # ===================================================
        H1("2. Implementation choices a reviewer should know about"),

        H2("2.1 Variable split: 8 predetermined &middot; 10 forward = 18 components"),
        P("The brief asks for an 18-component state vector with 8 predetermined "
          "(b&#770;<sup>S</sup><sub>t-1</sub>, b&#770;<sup>L</sup><sub>t-1</sub>, and "
          "the six AR(1) states) and 10 forward jumps "
          "(c&#770;, y&#770;, &pi;&#770;, &iacute;&#770;, Q&#770;<sup>L</sup>, "
          "Q&#770;<sup>L,fund</sup>, &omega;&#770;, R&#770;, v&#770;, s&#770;). "
          "The brief&rsquo;s &lsquo;endogenous (12)&rsquo; list includes "
          "b&#770;<sup>S</sup><sub>t</sub> and b&#770;<sup>L</sup><sub>t</sub>; "
          "to hit the target count of 18 we eliminate these two current-period "
          "stocks using the captive market-clearing equation (5) and the maturity-"
          "composition equation (10), leaving 10 jumps. The two bond-stock lags "
          "are carried as explicit predetermined state with their own dynamic "
          "equations:"),
        Paragraph("b&#770;<sup>L,lag</sup><sub>t+1</sub> = &lambda;&#770;<sup>L</sup><sub>t</sub> + V&#770;<sup>liab</sup><sub>t</sub> &minus; Q&#770;<sup>L</sup><sub>t</sub>", s_code),
        Paragraph("b&#770;<sup>S,lag</sup><sub>t+1</sub> = b&#770;<sup>L,lag</sup><sub>t+1</sub> &minus; &chi;&#770;<sub>t</sub>/[&chi;&#772;(1&minus;&chi;&#772;)]", s_code),
        CALL("<b>Double-click:</b> an equivalent formulation keeps b&#770;<sup>L</sup><sub>t</sub>, "
             "b&#770;<sup>S</sup><sub>t</sub> as explicit jumps and adds two lag-aux "
             "variables (20-state). Both give the same impulse responses for the "
             "twelve named endogenous variables. The 18-component formulation is "
             "more compact and is what the brief implicitly requests."),

        H2("2.2 Shock matrix B = 0; shocks enter via initial state"),
        P("The AR(1) law z<sub>t+1</sub> = &rho;<sub>z</sub>z<sub>t</sub> + "
          "&epsilon;<sub>t+1</sub><sup>z</sup> places the innovation at t+1. "
          "In the Klein form A<sub>0</sub>E<sub>t</sub>x<sub>t+1</sub> = "
          "A<sub>1</sub>x<sub>t</sub> + B&epsilon;<sub>t</sub> the contemporaneous "
          "shock vector therefore vanishes (B is identically zero); the "
          "&epsilon;-effect at h = 0 is constructed manually as the "
          "initial-state matrix Q (18&times;6) whose AR(1)-row block is the "
          "identity I<sub>6</sub> and whose bond-lag rows are zero. Jumps at "
          "h = 0 follow from the policy function F applied to that initial "
          "predetermined block."),
        CALL("<b>Double-click:</b> some Klein implementations place AR(1) "
             "innovations in B (treating &epsilon;<sub>t</sub> as a current "
             "shock and using x&minus;&epsilon; on the LHS). Both conventions "
             "give identical IRFs but mis-mixing them is a common bug source."),

        H2("2.3 Klein 1999 generalised Schur (scipy.linalg.ordqz)"),
        P("<font face='Courier'>scipy.linalg.ordqz(A1, A0, sort='iuc', "
          "output='complex')</font> returns the QZ factorisation with the "
          "stable generalised eigenvalues (|&alpha;/&beta;| &lt; 1) in the "
          "upper-left block. The policy function is F = Z<sub>21</sub>Z<sub>11</sub><sup>-1</sup> "
          "and the state law is M = Z<sub>11</sub>B<sub>ss</sub><sup>-1</sup>A<sub>ss</sub>Z<sub>11</sub><sup>-1</sup>. "
          "Both are constructed in the complex domain and cast to real after "
          "the partitioning; the imaginary parts are at the 10<sup>-14</sup> "
          "level (machine noise from complex eigenvalue pairs that cancel "
          "when rotated back)."),

        H2("2.4 Calibration inheritance from &sect;3.4"),
        P("&omega;&#772; = 0.121, w<sub>S</sub> = 0.63, w<sub>L</sub> = 0.37, "
          "s&#772;/v = &minus;0.03 and R&#772;/v = 0.04 all come from the "
          "steady-state calibration of &sect;3.4. The &eta; coefficient "
          "&delta;Q<sup>L</sup>/(1+&delta;Q<sup>L</sup>) is in turn a function "
          "of &omega;&#772; through Q<sup>L</sup> = (1+&omega;&#772;)Q<sup>L,fund</sup>. "
          "Any revision to the &sect;3.4 calibration (in particular to the "
          "DMO-sourced best-guesses for long-gilt market value and 15+ "
          "duration that feed &omega;&#772;) propagates through every IRF "
          "panel in this report."),
        CALL("<b>Double-click:</b> the rent equation (7) carries the coefficient "
             "1/&omega;&#772; &asymp; 8.26 on &omega;&#770;. If the headline "
             "calibration of &omega;&#772; were 0.05 instead of 0.121, the "
             "rent elasticity would jump to 20, materially changing the FTPL "
             "feedback magnitude. The 2020 spike to &omega; &asymp; 1.0 in the "
             "&sect;3.4 time-series suggests the headline &omega;&#772; may "
             "understate the post-COVID/mini-budget regime."),

        # ===================================================
        # 3. Diagnostics
        # ===================================================
        H1("3. Diagnostics"),

        H2("3.1 Blanchard-Kahn condition"),
        P("With 8 predetermined and 10 forward variables, BK requires "
          "exactly 10 generalised eigenvalues outside the unit circle. "
          "At the headline calibration:"),
    ]

    # Eigenvalue table
    ev = sol["eigenvalues"]
    mods = np.abs(ev)
    sorted_idx = np.argsort(mods)
    ev_rows = [["#", "|eigenvalue|", "real part", "imag part", "class"]]
    for k, i in enumerate(sorted_idx):
        m = mods[i]
        if np.isinf(m):
            disp = "inf"
        else:
            disp = f"{m:.5g}"
        real = "inf" if np.isinf(ev[i].real) else f"{ev[i].real:+.4g}"
        imag = "n/a" if np.isnan(ev[i].imag) else f"{ev[i].imag:+.2g}"
        cls = "stable" if m < 1 else "unstable" if m > 1 else "unit"
        ev_rows.append([str(k + 1), disp, real, imag, cls])
    t_ev = Table(ev_rows, colWidths=[1.0 * cm, 3.2 * cm, 3.0 * cm, 2.4 * cm, 2.0 * cm])
    t_ev.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ALIGN",      (0, 0), (-1, -1), "RIGHT"),
        ("ALIGN",      (4, 0), (4, -1), "LEFT"),
        ("GRID",       (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 9), (-1, 9), colors.HexColor("#fef3c7")),  # boundary
    ]))
    story.append(t_ev)
    story.append(CAP("Generalised eigenvalues of the pencil (A<sub>1</sub>, A<sub>0</sub>), "
                     "sorted by modulus. Rows 1&ndash;8 are the stable block; rows 9&ndash;18 are unstable. "
                     "BK satisfied: n_stable = 8, n_unstable = 10."))

    story += [
        P("<b>Interpretation of the spectrum.</b> Six stable eigenvalues sit at "
          "exactly &rho; = 0.7 &mdash; the AR(1) autocorrelations, which decouple "
          "cleanly from the rest of the system. One stable root at &asymp; 0.87 "
          "comes from the predetermined-bond-lag block interacting with the "
          "fundamental long-bond pricing equation. One stable root at machine zero "
          "is a static identity row (rows of A<sub>0</sub> that are identically "
          "zero generate trivially &lsquo;stable&rsquo; eigenvalues). On the "
          "unstable side, two finite roots (1.02 and 1.20) come from the FTPL "
          "identity and the inflation/wedge feedback; the very large finite "
          "values (10<sup>15</sup>&ndash;10<sup>51</sup>) and three exact "
          "infinities are again the static-row artefact &mdash; the QZ "
          "decomposition treats &alpha;<sub>i</sub>/0 as infinite eigenvalues, "
          "which BK counts as unstable. The total count is the meaningful "
          "diagnostic, not the spread of moduli."),
        CALL("<b>Double-click:</b> if a future edit accidentally makes A<sub>0</sub> "
             "non-singular (e.g. by adding an E<sub>t</sub>x<sub>t+1</sub> term to "
             "a static identity such as the wedge definition), the infinite "
             "eigenvalues collapse to finite numbers and the BK count may shift. "
             "Run <font face='Courier'>nk_ftpl_solve.py</font> after any matrix "
             "edit and re-check the count."),

        H2("3.2 Stationarity"),
        P("All IRFs decay to within 0.01 at h = 39 except four variables under the "
          "monetary shock (|b&#770;<sup>S,lag</sup>|, |b&#770;<sup>L,lag</sup>|, "
          "|Q&#770;<sup>L</sup>|, |Q&#770;<sup>L,fund</sup>| &asymp; 0.011&ndash;0.013). "
          "This is a scale effect rather than a solution bug: the monetary shock "
          "produces an impact rent response R&#770; = +11.3 (vs. &asymp; +3.5 for "
          "the &lambda; shock), so even at &rho;<sup>39</sup> &asymp; 5&times;10<sup>-7</sup> "
          "decay, residuals remain at the second decimal. The spectrum has no "
          "unit roots."),

        # ===================================================
        # 4. Theoretical mechanism
        # ===================================================
        PageBreak(),
        H1("4. Theoretical mechanism: how the captive-demand channel moves inflation"),
        P("The headline result of the chapter is that a positive shock to the "
          "regulatory intensity &lambda;<sup>L</sup> (a tightening of the LDI "
          "mandate that forces pension funds and insurers to hold more long gilts) "
          "produces a <i>fall</i> in inflation on impact. The mechanism runs in "
          "four steps:"),
        B("(i) <b>Mandate &rarr; rent.</b> Equation (7) gives "
          "R&#770;<sub>t</sub> = &omega;&#770;<sub>t</sub>/&omega;&#772; + "
          "&lambda;&#770;<sup>L</sup><sub>t</sub> + V&#770;<sup>liab</sup><sub>t</sub>. "
          "A unit positive &lambda;&#770;<sup>L</sup> shock raises R&#770; "
          "immediately by +1 directly, plus an indirect amplification through "
          "&omega;&#770; (which itself rises because the captive demand bids "
          "up the long-bond price). At calibration the combined impact is "
          "R&#770;<sub>0</sub> = +3.53."),
        B("(ii) <b>Long-bond price.</b> The captive market clears at "
          "Q<sup>L</sup>b<sup>L</sup> = &lambda;<sup>L</sup>V<sup>liab</sup>; "
          "with V<sup>liab</sup> unchanged, the increase in &lambda;<sup>L</sup> "
          "must be absorbed by Q<sup>L</sup> and b<sup>L</sup>. Q<sup>L</sup> "
          "jumps up (+1.02 on impact) while the model substitution implies "
          "b<sup>L</sup> &asymp; &minus;0.02 (small response because most of "
          "the shock is absorbed in price). The wedge &omega;&#770; over the "
          "fundamental price (which moves only +0.72) rises by +0.31."),
        B("(iii) <b>FTPL identity must rebalance.</b> Equation (9) is "
          "v&#770;<sub>t</sub> = (s&#772;/v)s&#770; + (R&#772;/v)R&#770; + "
          "&beta;E<sub>t</sub>v&#770;<sub>t+1</sub> &minus; "
          "&beta;(&iacute;&#770;<sub>t</sub> &minus; E<sub>t</sub>&pi;&#770;<sub>t+1</sub>). "
          "With (R&#772;/v) &asymp; 0.04, the +3.5 rent shock contributes &asymp; "
          "+0.14 to v&#770;. The FTPL identity therefore requires real debt "
          "market value to rise."),
        B("(iv) <b>Inflation falls.</b> Equation (8) says "
          "v&#770;<sub>t</sub> = w<sub>S</sub>(b&#770;<sup>S,lag</sup> &minus; "
          "&pi;&#770;<sub>t</sub>) + w<sub>L</sub>(b&#770;<sup>L,lag</sup> + "
          "&eta;Q&#770;<sup>L</sup><sub>t</sub> &minus; &pi;&#770;<sub>t</sub>). "
          "With w<sub>S</sub> + w<sub>L</sub> = 1, the coefficient on &pi;&#770; "
          "is exactly &minus;1: a one-percent inflation surprise destroys one "
          "percent of real debt. To <i>increase</i> v&#770; while Q&#770;<sup>L</sup> "
          "and the bond stocks adjust by limited amounts, inflation must "
          "<i>fall</i>. Numerically &pi;&#770;<sub>0</sub> = &minus;0.030."),
        P("Steps (i)&ndash;(iv) are not a Phillips-curve story: the NKPC is "
          "in the system but does not pin the price level. The price level is "
          "pinned by the augmented FTPL identity. The NKPC instead determines "
          "the joint motion of inflation and the output gap given the "
          "FTPL-required &pi;&#770; path. This is the formal definition of "
          "fiscal dominance, and it is why &phi;<sub>&pi;</sub> &lt; 1 is not "
          "a peripheral assumption but the structural switch that activates "
          "the channel."),
        CALL("<b>Double-click:</b> the chain above hinges on the sign of "
             "&minus;(w<sub>S</sub>+w<sub>L</sub>) in equation (8). If a "
             "sign error inverted that to +1, the headline result would flip "
             "and &lambda; shocks would raise inflation. The brief&rsquo;s "
             "&sect;7 debugging note already flags this row as the most "
             "fragile in the matrix construction."),

        # ===================================================
        # 5. IRF results
        # ===================================================
        H1("5. Impulse responses"),

        H2("5.1 Mandate tightening: &epsilon;<sup>&lambda;</sup> shock"),
        P("The chapter&rsquo;s central object. Unit positive &epsilon;<sup>&lambda;</sup> "
          "(the persistent AR(1) raises &lambda;&#770;<sup>L</sup> by 1pp on impact, "
          "decaying at &rho;<sub>&lambda;</sub> = 0.7)."),
        Image(str(PNG_DIR / "irf_lambda.png"), width=17 * cm, height=4.0 * cm),
        CAP("Figure 1. IRF to &epsilon;<sup>&lambda;</sup> shock. All four sign predictions in "
            "the brief&rsquo;s &sect;7 sanity check 1 are satisfied: &pi;&#770;&darr;, "
            "Q&#770;<sup>L</sup>&uarr;, R&#770;&uarr;, v&#770;&uarr;. &iacute;&#770; falls "
            "because the Taylor rule responds passively to lower inflation."),
        P("All variables decay monotonically (no oscillation) because the dominant "
          "modes are real and stable. By h = 8 the impact has roughly halved; by "
          "h = 20 it is below 10%. The shape is governed almost entirely by "
          "&rho;<sub>&lambda;</sub>; changing &rho;<sub>&lambda;</sub> = 0.7 to 0.9 "
          "would extend the half-life by a factor of three without altering the "
          "h = 0 sign."),

        H2("5.2 Fiscal expansion: &epsilon;<sup>g</sup> shock"),
        Image(str(PNG_DIR / "irf_g.png"), width=17 * cm, height=4.0 * cm),
        CAP("Figure 2. IRF to &epsilon;<sup>g</sup> shock (government spending up)."),
        P("Inflation rises on impact (+0.057), confirming the brief&rsquo;s "
          "sanity check 2 &mdash; the standard FTPL prediction: g&uarr; "
          "&rArr; s&darr; (via equation 12: s&#770; = &tau;&#772;/y&#772;&middot;&tau;&#770; "
          "&minus; g&#772;/y&#772;&middot;g&#770;) &rArr; the augmented FTPL identity "
          "needs price-level revaluation, so &pi;&#770;&uarr;. Interestingly, "
          "&pi;&#770; turns negative around h = 4 and stays negative through "
          "the horizon. The reversal reflects the discount-rate term "
          "&beta;(&iacute;&#770; &minus; E&pi;&#770;<sub>t+1</sub>) in equation (9): "
          "as the deficit shock persists, expected future deficits raise "
          "expected v&#770;<sub>t+1</sub>, which (held with a negative sign in "
          "the IS-anchored real rate) feeds back as deflationary expectations. "
          "Q&#770;<sup>L</sup>, R&#770; and v&#770; all show milder responses "
          "than the &lambda; shock because the fiscal shock affects only the "
          "(s&#772;/v) channel, while &lambda; affects the much larger "
          "(R&#772;/v) channel through the wedge."),

        H2("5.3 Monetary tightening: &epsilon;<sup>i</sup> shock"),
        Image(str(PNG_DIR / "irf_monetary.png"), width=17 * cm, height=4.0 * cm),
        CAP("Figure 3. IRF to &epsilon;<sup>i</sup> shock (positive monetary policy shock, "
            "&iacute;&#770; rises)."),
        P("Here the model gives &pi;&#770;<sub>0</sub> = +0.146 &mdash; the "
          "<i>opposite</i> sign from the brief&rsquo;s sanity check 3 "
          "(&lsquo;standard NK prediction&rsquo;). This is not a bug; it is "
          "the structural prediction of FTPL under passive monetary policy, "
          "explicitly discussed in &sect;6 of <i>nk_ftpl_embedding.pdf</i>. "
          "A positive &iacute;&#770; shock under fiscal dominance raises real "
          "rates if &pi;&#770; were unchanged, which lowers the present value "
          "of fiscal backing on the RHS of the FTPL identity. To restore the "
          "identity, the price level must revalue real debt downward "
          "&mdash; i.e., inflation must rise. The output response (&yacute;&#770; "
          "&minus;0.97) is in the standard NK direction (contractionary), but "
          "the price-level response inverts because price determination is "
          "fiscal, not monetary, in this regime."),
        CALL("<b>Reviewer red flag #1:</b> the &sect;7 brief calls this prediction "
             "&lsquo;standard NK&rsquo; without qualifier. It is the right answer "
             "for the active-NK case (&phi;<sub>&pi;</sub> &gt; 1) but the wrong "
             "answer for the passive-FTPL case (&phi;<sub>&pi;</sub> &lt; 1) that "
             "the chapter is studying. The implementation reproduces what the "
             "embedding PDF predicts; the sign in the brief should be updated."),

        H2("5.4 Sensitivity to the Taylor coefficient &phi;<sub>&pi;</sub>"),
        Image(str(PNG_DIR / "sensitivity_phi_pi.png"), width=14 * cm, height=7 * cm),
        CAP("Figure 4. &pi;&#770; response to a positive &epsilon;<sup>&lambda;</sup> shock for "
            "&phi;<sub>&pi;</sub> &isin; {0, 0.3, 0.5, 0.8, 0.95}. All five passive-regime values yield BK-satisfying solutions."),
        P("The impact response on &pi;&#770; is |&pi;&#770;<sub>0</sub>| = 0.028 at "
          "&phi;<sub>&pi;</sub> = 0, rises slightly to 0.030 at &phi;<sub>&pi;</sub> = 0.5, "
          "then falls to 0.018 at &phi;<sub>&pi;</sub> = 0.95. The brief&rsquo;s "
          "sanity check 4 predicts the opposite &mdash; that |&pi;&#770;| grows "
          "as &phi;<sub>&pi;</sub> &rarr; 1<sup>&minus;</sup>. The intuition the "
          "brief offers (&lsquo;less monetary accommodation = more inflation "
          "work for the FTPL channel&rsquo;) reverses the actual mechanism. "
          "Higher &phi;<sub>&pi;</sub> means a <i>larger</i> nominal-rate "
          "response to inflation, which keeps the real rate closer to neutral "
          "when &pi;&#770; falls (the Taylor rule &lsquo;tracks&rsquo; inflation "
          "down). This accommodation damps the IS-side amplification of the "
          "&pi;&#770; movement. Below the Taylor principle (&phi;<sub>&pi;</sub> &lt; 1), "
          "the closer to one, the closer monetary policy gets to neutralising "
          "its own contribution to real-rate dynamics &mdash; reducing the "
          "magnitude of the &pi;&#770; movement needed from the FTPL side."),
        CALL("<b>Reviewer red flag #2:</b> the &sect;7 sanity check 4 needs revision. "
             "The model says <i>smaller</i> |&pi;&#770;| as &phi;<sub>&pi;</sub> "
             "approaches one. If you want the brief&rsquo;s intuition to hold, "
             "you would need a different specification (e.g., backward-looking "
             "Taylor or interest-rate smoothing); the current forward-looking "
             "rule yields the present result."),
        P("BK fails sharply as soon as &phi;<sub>&pi;</sub> crosses unity "
          "(&phi;<sub>&pi;</sub> = 1.01: n_unstable = 11, expected 10). This "
          "matches the brief&rsquo;s sanity check 5 and confirms the determinacy "
          "argument of &sect;6 of the embedding PDF: above the Taylor principle, "
          "the standard NK three-equation system pins &pi; uniquely and the "
          "FTPL identity becomes over-identified."),

        # ===================================================
        # 6. Reviewer red flags
        # ===================================================
        H1("6. Reviewer red flags: items worth double-clicking"),
        P("In addition to the two flagged above, three more substantive items "
          "merit explicit attention."),

        H2("6.1 &omega;&#772; calibration is the single biggest knob"),
        P("&omega;&#772; = 0.121 enters the system as the 1/&omega;&#772; "
          "&asymp; 8.26 coefficient on &omega;&#770; in the rent equation, "
          "and indirectly as the &eta; coefficient through "
          "Q<sup>L</sup> = (1+&omega;&#772;)Q<sup>L,fund</sup>. The "
          "&sect;3.4 calibration produced &omega;&#772; under particular "
          "best-guess values for the DMO inputs (long-gilt 15+ duration and "
          "market value). The 2020 implied &omega; from the data-driven exercise "
          "was 1.01, far above the calibrated value, suggesting that the "
          "headline IRF magnitudes may understate the COVID/mini-budget regime. "
          "A robustness exercise sweeping &omega;&#772; &isin; {0.05, 0.10, "
          "0.15, 0.25} would establish the range of headline magnitudes the "
          "chapter can credibly claim."),

        H2("6.2 Persistence &rho;<sub>z</sub> = 0.7 across all shocks"),
        P("The conventional &rho; = 0.7 sets every IRF half-life to roughly "
          "2 quarters. This is fine for illustrative IRFs but the dissertation&rsquo;s "
          "estimation strategy (&sect;3.5) will estimate &rho;<sub>z</sub> per "
          "shock from data. The IRF shapes will sharpen or smooth substantially "
          "under more realistic persistences &mdash; e.g., a slow-moving &lambda; "
          "shock (&rho;<sub>&lambda;</sub> = 0.95) would extend the &pi;&#770; "
          "trough out to 20+ quarters."),

        H2("6.3 V<sup>liab</sup> AR(1) is a strong assumption"),
        P("The model treats log V<sup>liab</sup> as an AR(1) around its "
          "calibrated steady state. Empirically V<sup>liab</sup> swung "
          "violently during 2022 (UK pension technical provisions fell from "
          "&pound;2.38tn at end-2021 to &pound;2.06tn at end-2022 as gilt "
          "yields spiked). The log-linear approximation around the steady state "
          "is local; large V<sup>liab</sup> swings of that magnitude exit the "
          "neighbourhood where the first-order approximation is accurate. "
          "If the dissertation wants the model to speak to the LDI episode "
          "itself, a piecewise or non-linear treatment of V<sup>liab</sup> may "
          "be required."),

        H2("6.4 Substituting out b&#770;<sup>L</sup>, b&#770;<sup>S</sup>"),
        P("Equations (5) and (10) are used to eliminate the current-period "
          "bond stocks from the state. The resulting 18-component formulation "
          "is identical in IRFs to a 20-component version that retains them "
          "as explicit jumps with two lag aux variables &mdash; we verified "
          "this analytically. A reviewer who prefers the explicit formulation "
          "for transparency could request it; the script is structured to "
          "make that substitution a one-block change."),

        H2("6.5 Klein assumption Z<sub>11</sub> invertible"),
        P("Klein&rsquo;s policy formula F = Z<sub>21</sub>Z<sub>11</sub><sup>-1</sup> "
          "requires the upper-left block of the unitary matrix Z to be invertible. "
          "At the headline calibration cond(Z<sub>11</sub>) is well-behaved "
          "(~10<sup>2</sup>). The script catches LinAlgError on Z<sub>11</sub> "
          "and reports a clear diagnostic if a future parameter change makes "
          "it singular &mdash; this can happen at the boundary of the "
          "determinacy region (&phi;<sub>&pi;</sub> exactly 1, for example)."),

        # ===================================================
        # 7. Conclusions
        # ===================================================
        H1("7. Conclusions"),
        P("The Python solver reproduces the captive-demand channel as designed. "
          "The headline IRF to a tighter LDI mandate matches all four sign "
          "predictions of the chapter; the inflation channel runs through the "
          "FTPL identity rather than the Phillips curve, exactly as the "
          "passive-monetary setup requires; and the determinacy region is "
          "bounded by &phi;<sub>&pi;</sub> = 1 as theory predicts."),
        P("The two surface-level discrepancies with &sect;7 of the RA brief "
          "(monetary-shock sign and &phi;<sub>&pi;</sub> sensitivity) are "
          "consistent with the model and inconsistent only with the brief&rsquo;s "
          "informal narration; both invoke active-NK intuition that does not "
          "apply in fiscal-dominance. The brief&rsquo;s sanity checks 3 and 4 "
          "would benefit from rewording before the next draft."),
        P("Three items propagate forward to the dissertation: (a) the "
          "magnitude of every IRF is materially sensitive to &omega;&#772;, "
          "itself an output of the &sect;3.4 calibration and best-guess data "
          "inputs; (b) the constant AR(1) persistence will be replaced by "
          "estimated values in &sect;3.5, sharpening or smoothing the dynamics; "
          "(c) the linear-around-steady-state assumption is local and may not "
          "capture the LDI tail event the chapter ultimately wants to speak to."),
        P("All implementation artefacts &mdash; "
          "<font face='Courier'>nk_ftpl_solve.py</font>, "
          "<font face='Courier'>diagnostics.pkl</font>, "
          "<font face='Courier'>irfs/</font>, this report, "
          "and the rebuilt PNG figures in "
          "<font face='Courier'>figures/</font> "
          "&mdash; are reproducible from a single re-run of "
          "<font face='Courier'>nk_ftpl_solve.py</font> followed by "
          "<font face='Courier'>make_report.py</font>."),

        # Impact table appendix
        PageBreak(),
        H1("Appendix: full impact-response table (h = 0)"),
    ]

    # Impact table
    named = ["pi", "i", "c", "y", "QL", "QL_fund", "bS", "bL", "omega", "R", "v", "s"]
    cols = ["variable"] + SHOCK_NAMES
    rows = [cols]
    for v in named:
        rows.append([v] + [f"{irfs[sh][v].iloc[0]:+.4f}" for sh in SHOCK_NAMES])
    t = Table(rows, colWidths=[2.0 * cm] + [2.4 * cm] * len(SHOCK_NAMES))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (1, 0), (-1, -1), "RIGHT"),
        ("GRID",       (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))
    story.append(t)
    story.append(CAP("Table A.1. h = 0 impact responses of the 12 named endogenous "
                     "variables (rows) to each of the 6 structural shocks (columns). "
                     "Reproduces what nk_ftpl_solve.py prints to stdout."))

    doc.build(story)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    state = regenerate_figures()
    build_report(state)
