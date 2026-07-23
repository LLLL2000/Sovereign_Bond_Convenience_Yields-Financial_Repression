"""Render calibration_and_irfs_summary.pdf — 4-page summary document.

Mirrors the structure of calibration_and_irfs_summary.tex. Saved alongside
the .tex source so you can compare them if you ever do compile the .tex.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
FIG = HERE / "nk" / "figures" / "irf_lambda.png"
FIG_SENS = HERE / "nk" / "figures" / "sensitivity_phi_pi.png"
OUT = HERE / "calibration_and_irfs_summary.pdf"

# Register Calibri (has the combining diacritics our math notation needs)
# and a bold variant. Build a font family so <b>...</b> picks up the bold.
pdfmetrics.registerFont(TTFont("Calibri",      r"C:\Windows\Fonts\calibri.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-Bold", r"C:\Windows\Fonts\calibrib.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-Italic", r"C:\Windows\Fonts\calibrii.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-BI",   r"C:\Windows\Fonts\calibriz.ttf"))
pdfmetrics.registerFontFamily(
    "Calibri", normal="Calibri", bold="Calibri-Bold",
    italic="Calibri-Italic", boldItalic="Calibri-BI",
)


def main():
    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="Identification of the Long-End Captive-Demand Wedge",
        author="Lucas Leturia",
    )

    base = getSampleStyleSheet()
    F = "Calibri"

    s_title = ParagraphStyle("Title", parent=base["Title"], fontName="Calibri-Bold",
                             fontSize=14, leading=17, spaceAfter=2, alignment=1)
    s_author = ParagraphStyle("Author", parent=base["Normal"], fontName=F,
                              fontSize=10, alignment=1, spaceAfter=10)
    s_h1 = ParagraphStyle("H1", parent=base["Heading1"], fontName="Calibri-Bold",
                          fontSize=11.5, textColor=colors.HexColor("#1f2937"),
                          spaceBefore=8, spaceAfter=3)
    s_body = ParagraphStyle("Body", parent=base["BodyText"], fontName=F,
                            fontSize=10, leading=12.5, alignment=TA_JUSTIFY,
                            spaceAfter=4)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=14,
                              bulletIndent=2, spaceAfter=2)
    s_math = ParagraphStyle("Math", parent=s_body, alignment=1,
                            fontName=F, fontSize=10.5, leading=14,
                            spaceBefore=3, spaceAfter=4)
    s_para_hdr = ParagraphStyle("ParaHdr", parent=s_body, fontName=F,
                                fontSize=10, spaceAfter=1, spaceBefore=3)
    s_caption = ParagraphStyle("Caption", parent=base["Normal"], fontName=F,
                               fontSize=9, alignment=1,
                               textColor=colors.HexColor("#374151"),
                               spaceBefore=2, spaceAfter=6)
    s_cell = ParagraphStyle("Cell", parent=base["BodyText"], fontName=F,
                            fontSize=9, leading=11, spaceAfter=0)
    s_cell_hdr = ParagraphStyle("CellHdr", parent=s_cell, fontName="Calibri-Bold",
                                textColor=colors.white)

    P = lambda t: Paragraph(t, s_body)
    H1 = lambda t: Paragraph(t, s_h1)
    M = lambda t: Paragraph(t, s_math)
    Bul = lambda t: Paragraph(t, s_bullet)
    CAP = lambda t: Paragraph(t, s_caption)

    def header_table(rows, col_widths, hdr_bg="#1f2937"):
        # Wrap every cell in a Paragraph so HTML entities/markup parse
        # and so the Calibri font is applied consistently.
        wrapped = []
        for r_idx, row in enumerate(rows):
            wrapped_row = []
            for c in row:
                style = s_cell_hdr if r_idx == 0 else s_cell
                wrapped_row.append(Paragraph(c, style))
            wrapped.append(wrapped_row)
        t = Table(wrapped, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(hdr_bg)),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",       (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING",   (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
        ]))
        return t

    story = []

    # ---- Title ----
    story += [
        Paragraph(
            "Identification of the Long-End Captive-Demand Wedge:"
            "<br/>Estimation, Convenience-Yield Comparison, and NK-FTPL Calibration with Inflation IRFs",
            s_title,
        ),
        Paragraph(
            "Lucas Leturia &middot; Master&rsquo;s Dissertation, PUC Chile &middot; Entrega III &middot; May 2026",
            s_author,
        ),
    ]

    # =================================================================
    # §1 Identity-Based Estimation
    # =================================================================
    story += [
        H1("1. Identity-Based Estimation of the Wedge Series {&omega;<sub>t</sub>}<sub>2010</sub><sup>2024</sup>"),
        P("The &sect;3.4 calibration recovers a time series of long-end captive-demand wedges &omega;<sub>t</sub> "
          "from a closed-form algebraic solve of the augmented FTPL identity. Six observables &mdash; the real "
          "short rate, the long-bond duration, the captive-demand scale V<sup>liab</sup>, the long- and short-bond "
          "market values, and the primary balance &mdash; are read from UK data, all scaled by nominal GDP "
          "(ONS series YBHA), and the seventh quantity &omega;<sub>t</sub> is implied algebraically year by year. "
          "There is no optimization or statistical estimation: the recovery is exact given the inputs."),
        M("&beta;<sub>t</sub> = 0.99 (constant; see &sect;3) &nbsp;&nbsp; "
          "&delta;<sub>t</sub> = (1 &minus; 1/D<sub>t</sub>)/&beta;<sub>t</sub> &nbsp;&nbsp; "
          "Q<sup>L,fund</sup><sub>t</sub> = &beta;<sub>t</sub>/(1 &minus; &beta;<sub>t</sub>&delta;<sub>t</sub>)"),
        M("v<sub>t</sub> = (b<sup>S</sup><sub>t</sub> + b<sup>L</sup><sub>t</sub>)/y&#772;<sub>t</sub> &nbsp;&nbsp; "
          "R<sub>t</sub> = (1&minus;&beta;<sub>t</sub>)&middot;v<sub>t</sub> &minus; s<sub>t</sub> &nbsp;&nbsp; "
          "&omega;<sub>t</sub> = [R<sub>t</sub>/b<sup>L</sup><sub>t</sub>] / [1 &minus; R<sub>t</sub>/b<sup>L</sup><sub>t</sub>]"),
        P("Data are compiled in <font face='Courier'>calibration/inputs_filled_v2.xlsx</font> from auto-downloaded "
          "ONS, OBR, BoE and TPR/PPF sources plus best-guess DMO inputs (the DMO data portal is JavaScript-rendered "
          "and not scriptable); each cell has a colour-coded provenance tag."),
        Paragraph("<b>One key deviation from the methodology PDF (&sect;3.4).</b> ", s_para_hdr),
        P("The real short rate r<sub>t</sub> entering &beta;<sub>t</sub> = 1/(1+r<sub>t</sub>) is set to the "
          "literature standard &beta; = 0.99 constant rather than read off the BoE GLC Real curve at 1y. "
          "The BoE does not publish below 2.5y on the linker curve, and the 2.5y proxy is deeply negative across "
          "the QE/ZLB sample because LDI captive demand compresses 2y+ real linker yields &mdash; precisely the "
          "channel the dissertation is identifying. Feeding the 2.5y proxy into &beta; = 1/(1+r) would partially "
          "double-count the wedge into the discount factor itself. The literature-standard &beta; = 0.99 sidesteps "
          "this; the original BoE-derived series is preserved in the input workbook for sensitivity exercises."),
        Paragraph("<b>Data provenance and an implementation detail.</b> ", s_para_hdr),
        P("Five of the seven inputs are auto-downloaded: nominal GDP (ONS YBHA via JSON API), the primary balance "
          "(OBR Public Sector Finances aggregates databank), the BoE GLC Real curve as informational fallback, the "
          "Purple Book aggregate DB liabilities (PPF 2025, Figure 4.2 historical table; linear interpolation for "
          "the four PB-non-publication years), and insurance technical provisions (BoE Insurance Aggregate CSV, "
          "Q4 readings 2017&ndash;2024 with 2017-ratio backward-extrapolation for 2010&ndash;2016). The two DMO "
          "inputs &mdash; 15+ Macaulay duration and the long / short-medium gilt market-value split &mdash; require "
          "manual entry because the DMO data portal is JavaScript-rendered; the values used are anchored to the "
          "end-March 2025 reading in the DMO Annual Review and shaped backwards along the QE expansion profile. "
          "The bond stocks b<sup>L</sup><sub>t</sub> and b<sup>S</sup><sub>t</sub> are substituted out of the "
          "explicit state vector using the captive-market clearing equation and the maturity-composition rule, "
          "and their lagged values are tracked as predetermined state with their own dynamic equations."),
    ]

    # =================================================================
    # §2 Comparison to Convenience Yields
    # =================================================================
    story += [
        H1("2. Comparison to Convenience-Yield Benchmarks"),
        P("The unit-comparable object is not &omega;<sub>t</sub> itself but the implied yield-space wedge "
          "1/Q<sup>L,fund</sup> &minus; 1/Q<sup>L</sup> &asymp; (1/Q<sup>L,fund</sup>) &middot; &omega;/(1+&omega;), "
          "in basis points."),
    ]

    yield_tbl = [
        ["Period",         "ω range",      "Yield wedge (bps)"],
        ["2010",           "0.52",         "~170"],
        ["2011–2014",      "0.20–0.33",    "~85–125"],
        ["2015–2019",      "0.05–0.14",    "~25–60"],
        ["2020",           "1.01",         "~225"],
        ["2021–2022",      "0.10–0.16",    "~45–70"],
        ["2023–2024",      "0.15–0.19",    "~65–90"],
    ]
    story.append(header_table(yield_tbl, [3.5 * cm, 3.5 * cm, 4.0 * cm]))
    story.append(Spacer(1, 4))

    story += [
        P("<b>The implied wedge series is broadly consistent in magnitude and direction with the literature "
          "on long-end captive-demand effects.</b>"),
        Bul("&bull; <b>Greenwood&ndash;Hanson&ndash;Vayanos</b> (2010, 2018) and <b>Vayanos&ndash;Vila</b> (2021) "
            "preferred-habitat estimates put long-end yield compression from segmented LDI/insurance demand at "
            "30&ndash;100 bps in steady state. The model&rsquo;s 2015&ndash;2019 and 2021&ndash;2024 readings "
            "(25&ndash;90 bps) sit in this band."),
        Bul("&bull; <b>Domanski&ndash;Shin&ndash;Sushko</b> (BIS, 2017) put UK LDI-specific yield compression at "
            "50&ndash;100 bps over 2014&ndash;2017; the model gives roughly 70 bps over that window."),
        Bul("&bull; <b>Krishnamurthy&ndash;Vissing-Jorgensen</b> (2012) put the US Treasury convenience yield at "
            "~70 bps on average over 1929&ndash;2008. The conceptual object is broader (safety+liquidity+scarcity, "
            "not just LDI), but the order-of-magnitude check passes."),
        Bul("&bull; The 2020 magnitude (~225 bps) is on the high end. It is sensitive to my best-guess DMO long-gilt "
            "market value: under-stating MV/GDP at the QE peak inflates the implied &omega;. A plausible "
            "DMO-corrected magnitude is 100&ndash;150 bps, closer to estimates of total QE-era long-end compression. "
            "A sweep over &omega;&#772; should accompany the headline series."),
        Bul("&bull; <b>Pinter&ndash;Walker</b> (BoE staff working paper, 2023) put the persistent post-mini-budget "
            "long-gilt LDI premium at ~50 bps. The model&rsquo;s 2022 figure (46 bps) is on target but smooths over "
            "the September spike because the calibration is annual."),
        P("Of the four &lsquo;regimes&rsquo; the dissertation can speak to &mdash; post-GFC fiscal expansion, ZLB "
          "calm, the 2020 stress, and the post-LDI normalisation &mdash; the model captures the level and the "
          "direction in each. The biggest caveat is the 2020 magnitude; the second is that annual frequency cannot "
          "capture the within-year 2022 tail event."),
        Paragraph("<b>The model&rsquo;s &omega; is narrower than &lsquo;convenience yield&rsquo;.</b> ", s_para_hdr),
        P("Krishnamurthy&ndash;Vissing-Jorgensen identify a Treasury convenience yield that bundles three components: "
          "money-like safety, liquidity, and supply scarcity. The model&rsquo;s &omega;<sub>t</sub> is conceptually "
          "narrower &mdash; it isolates the part of the long-end price premium attributable to "
          "<i>regulatory-mandated captive demand</i> from pension and insurance liabilities. This is the same "
          "object Greenwood&ndash;Hanson&ndash;Vayanos and the BIS LDI literature attempt to identify, and the "
          "model&rsquo;s contribution is to derive it from the augmented FTPL identity rather than from term-structure "
          "regressions. The directional and magnitudinal alignment with those independently estimated benchmarks is "
          "therefore the right cross-check, and the chapter&rsquo;s claim should be framed as recovery of "
          "<i>LDI-specific</i> long-end compression rather than total convenience yield."),
    ]

    # =================================================================
    # §3 NK calibration
    # =================================================================
    story += [
        H1("3. Calibration of Deep Parameters for the NK Embedding"),
        P("The &sect;3.4 exercise pins steady-state objects; the NK embedding adds a small forward-looking system "
          "that requires three additional parameters &mdash; the Calvo stickiness &theta;, the CRRA &sigma;, and "
          "the Taylor coefficient &phi;<sub>&pi;</sub>. The full calibration table is set as follows."),
    ]

    cal_tbl = [
        ["Parameter",                                  "Value",       "Source / rationale"],
        ["β (discount factor)",                        "0.99",        "Literature standard (annual). Cochrane FTPL book, Sims 2013."],
        ["σ (CRRA)",                                   "1",           "Log utility, NK convention (Galí 2015 Ch. 3)"],
        ["δ (long-bond decay)",                        "0.96",        "UK 15+ duration ≈ 20y → β·δ = 0.95"],
        ["ω̄ (wedge)",                                  "0.121",       "§3.4 sample average, 2010–2024, under β=0.99 calibration"],
        ["η = δQ<sup>L</sup>/(1+δQ<sup>L</sup>)",     "0.954",       "Derived; reflects long bond&rsquo;s near-perpetuity nature"],
        ["w<sub>S</sub>, w<sub>L</sub>",               "0.63, 0.37",  "§3.4: short+medium and long share of UK gilt market value"],
        ["s̄/v",                                        "−0.03",       "UK primary deficit / debt MV, 2010–2024 average (OBR)"],
        ["R̄/v",                                        "+0.04",       "Implied by FTPL: s̄/v + R̄/v = 1 − β = 0.01"],
        ["c̄/ȳ, ḡ/ȳ",                                   "0.60, 0.40",  "UK consumption and government spending shares"],
        ["τ̄/ȳ",                                        "0.37",        "Implied by s̄/ȳ = −0.03 and ḡ/ȳ"],
        ["χ̄ (long-share)",                             "0.37",        "DMO long-share of conventional gilt market value"],
        ["θ (Calvo)",                                  "0.75",        "Quarterly no-reset probability; 4-quarter avg reset (NK standard)"],
        ["κ (NKPC slope)",                             "0.086",       "(1−θ)(1−βθ)σ/θ"],
        ["φ<sub>π</sub>",                              "0.5",         "Passive monetary; mid-range of (0,1) determinacy region"],
        ["ρ<sub>z</sub> (all z)",                      "0.7",         "Conventional AR(1) persistence pending §3.5 estimation"],
    ]
    story.append(header_table(cal_tbl, [4.0 * cm, 2.4 * cm, 10.5 * cm]))
    story.append(Spacer(1, 3))

    story += [
        Paragraph("<b>Choices that bear scrutiny.</b> ", s_para_hdr),
        P("The single most consequential parameter is &omega;&#772;. It enters the rent equation as a coefficient "
          "1/&omega;&#772; &asymp; 8.26 on &omega;&#770;, and indirectly through &eta;. The 2020 &sect;3.4 reading "
          "of &omega;<sub>t</sub> = 1.01 suggests that the headline 0.121 average understates the stress regime; "
          "any IRF magnitude comparison across regimes should sweep &omega;&#772;. The Calvo parameter &theta; = 0.75 "
          "delivers &kappa; &asymp; 0.086 which is at the lower end of estimated NKPC slopes for advanced "
          "economies &mdash; a flatter Phillips curve makes inflation respond more slowly to output gaps, so the "
          "IRFs put more weight on the FTPL channel and less on the NKPC channel. The passive Taylor "
          "&phi;<sub>&pi;</sub> = 0.5 is the mid-range of the determinacy region under fiscal dominance; the "
          "boundary at &phi;<sub>&pi;</sub> = 1 is sharp (BK fails at &phi;<sub>&pi;</sub> = 1.01), confirming the "
          "regime switch described in &sect;6 of the embedding PDF."),
    ]

    # =================================================================
    # §4 Inflation IRFs
    # =================================================================
    story += [
        H1("4. Inflation Impulse Responses"),
        P("The headline result is the response of inflation to a positive shock to the regulatory intensity "
          "&lambda;&#770;<sup>L</sup> &mdash; a tightening of the LDI mandate. The model predicts on impact "
          "&pi;&#770;&darr;, Q&#770;<sup>L</sup>&uarr;, R&#770;&uarr;, v&#770;&uarr;, with all variables "
          "decaying monotonically at the AR(1) rate &rho;<sub>&lambda;</sub> = 0.7."),
        Image(str(FIG), width=17 * cm, height=3.5 * cm),
        CAP("Figure 1. IRF to a unit positive innovation to &lambda;&#770;<sup>L</sup>."),
        Paragraph("<b>Mechanism.</b> ", s_para_hdr),
        P("The chain runs: &lambda;&#770;<sup>L</sup>&uarr; &rarr; R&#770;&uarr; (mechanically, via the rent "
          "definition); R&#770;&uarr; &rarr; v&#770;&uarr; (augmented FTPL identity requires the present-value "
          "debt-backing to rise to match the higher rent stream); v&#770;&uarr; holding bond stocks given &rarr; "
          "&pi;&#770;&darr; (the coefficient on &pi;&#770; in the real-debt-value equation is exactly &minus;1: "
          "one percent of inflation destroys one percent of real debt, so v&#770; can only rise if &pi;&#770; "
          "falls). The NKPC is in the system but does not pin the price level &mdash; under passive monetary "
          "(&phi;<sub>&pi;</sub> &lt; 1) it is the augmented FTPL identity that does, and the NKPC determines the "
          "joint motion of inflation and output given the FTPL-required &pi;&#770; path. This is the formal "
          "definition of fiscal dominance and the substantive economic content of the chapter."),
        Paragraph("<b>Magnitude.</b> ", s_para_hdr),
        P("A unit positive shock to &lambda;&#770;<sup>L</sup> produces &pi;&#770;<sub>0</sub> = &minus;0.030 "
          "(3 basis points of disinflation on impact, in quarterly log-deviation units). Cumulative deflation over "
          "the first eight quarters is approximately &minus;0.14 log points. Higher persistence "
          "(&rho;<sub>&lambda;</sub> = 0.9) extends the trough out to 20 quarters without changing the impact sign."),
        Paragraph("<b>Fiscal expansion.</b> ", s_para_hdr),
        P("A positive &epsilon;<sup>g</sup> shock (government spending up, primary surplus down) raises inflation "
          "on impact (&pi;&#770;<sub>0</sub> = +0.057) &mdash; the standard FTPL prediction. Interestingly, "
          "&pi;&#770; turns negative around h = 4 as the discount-rate term &beta;(&iacute;&#770; &minus; "
          "E&pi;&#770;<sub>t+1</sub>) in the FTPL identity feeds back through forward expectations of higher "
          "v&#770;. The magnitude is roughly half that of the &lambda; shock because the fiscal channel works "
          "through s&#772;/v &asymp; &minus;0.03, while the captive-demand channel works through R&#772;/v &asymp; "
          "0.04 amplified by the wedge coefficient."),
        Paragraph("<b>Monetary tightening.</b> ", s_para_hdr),
        P("A positive &epsilon;<sup>i</sup> shock yields &pi;&#770;<sub>0</sub> = +0.146, the <i>opposite</i> sign "
          "from the standard active-NK prediction. Under fiscal dominance, a rise in the nominal rate raises the "
          "real rate if inflation were unchanged, lowering the present value of fiscal backing on the right-hand "
          "side of the FTPL identity. To restore the identity, the price level must revalue real debt downward "
          "&mdash; i.e., &pi;&#770; must <i>rise</i>. This is exactly the inversion &sect;6 of the embedding PDF "
          "predicts, and it is one of the headline empirical signatures distinguishing fiscal- from monetary-"
          "dominance regimes. The output response (&yacute;&#770;<sub>0</sub> = &minus;0.97) remains in the "
          "standard contractionary direction; only the price-level response inverts."),
        Paragraph("<b>Sensitivity to &phi;<sub>&pi;</sub>.</b> ", s_para_hdr),
        P("As &phi;<sub>&pi;</sub> &rarr; 1<sup>&minus;</sup>, |&pi;&#770;| in response to &epsilon;<sup>&lambda;</sup> "
          "<i>shrinks</i> from 0.030 at &phi;<sub>&pi;</sub> = 0.5 to 0.011 at &phi;<sub>&pi;</sub> = 0.99. Higher "
          "&phi;<sub>&pi;</sub> means the Taylor rule tracks inflation movements more closely; the real rate moves "
          "less when inflation moves, accommodating the FTPL adjustment and damping the inflation movement needed "
          "to clear the identity. At &phi;<sub>&pi;</sub> &gt; 1 the Blanchard&ndash;Kahn count flips (11 unstable "
          "eigenvalues vs. the required 10) and the price level becomes monetary-pinned &mdash; the determinacy "
          "boundary at exactly &phi;<sub>&pi;</sub> = 1 is the formal switch between fiscal and monetary dominance."),
        Image(str(FIG_SENS), width=12 * cm, height=6.5 * cm),
        CAP("Figure 2. &pi;&#770; response to &epsilon;<sup>&lambda;</sup> for "
            "&phi;<sub>&pi;</sub> ∈ {0, 0.3, 0.5, 0.8, 0.95}. The impact response peaks near "
            "&phi;<sub>&pi;</sub> = 0.5 and shrinks toward zero as &phi;<sub>&pi;</sub> approaches the "
            "determinacy boundary."),
        Paragraph("<b>Conclusions.</b> ", s_para_hdr),
        P("The captive-demand channel produces a robust and theoretically clean disinflation response to LDI "
          "tightening. Magnitudes at the headline calibration are modest but are governed by &omega;&#772;, which "
          "is itself estimated from the &sect;3.4 exercise with sensitivity to the DMO best-guesses. Two surface-level "
          "discrepancies between the model&rsquo;s predictions and the standard NK textbook &mdash; the "
          "monetary-shock sign and the &phi;<sub>&pi;</sub> sensitivity &mdash; are not bugs but the structural "
          "signature of fiscal dominance, and constitute testable empirical implications of the chapter."),
        Paragraph("<b>Next steps.</b> ", s_para_hdr),
        P("Three follow-ups propagate forward to &sect;3.5 and the empirical chapter. First, the &omega;&#772; "
          "sensitivity exercise should be reported alongside the headline IRFs, sweeping the &sect;3.4 DMO inputs "
          "to bound the implied compression magnitudes in 2020. Second, the AR(1) persistences "
          "&rho;<sub>z</sub> = 0.7 should be replaced with estimated values from the Kalman-filter likelihood "
          "&mdash; under more realistic persistences (e.g., &rho;<sub>&lambda;</sub> = 0.95) the inflation trough "
          "extends to 20+ quarters and the chapter speaks more directly to the LDI mandate-tightening trajectory "
          "the UK has been on since 2023. Third, the model&rsquo;s log-linearisation around steady state is local; "
          "the 2022 mini-budget V<sup>liab</sup> swing exits the neighbourhood where the first-order approximation "
          "is accurate, and a non-linear or piecewise treatment would let the model speak to the tail event itself "
          "rather than only to its annual smoothed shadow."),
    ]

    doc.build(story)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
