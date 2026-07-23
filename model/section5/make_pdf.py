"""Render section5.pdf via reportlab — a readable PDF version of section5.md."""

from __future__ import annotations
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
OUT = HERE / "section5.pdf"

# Calibri family for combining-diacritic rendering
pdfmetrics.registerFont(TTFont("Calibri",        r"C:\Windows\Fonts\calibri.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-Bold",   r"C:\Windows\Fonts\calibrib.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-Italic", r"C:\Windows\Fonts\calibrii.ttf"))
pdfmetrics.registerFont(TTFont("Calibri-BI",     r"C:\Windows\Fonts\calibriz.ttf"))
pdfmetrics.registerFontFamily(
    "Calibri", normal="Calibri", bold="Calibri-Bold",
    italic="Calibri-Italic", boldItalic="Calibri-BI",
)


def main():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
        title="Section 5 — Mapping to UK Observables",
        author="Lucas Leturia",
    )
    base = getSampleStyleSheet()
    F = "Calibri"

    s_title = ParagraphStyle("Title", parent=base["Title"], fontName="Calibri-Bold",
                             fontSize=14, leading=17, spaceAfter=2, alignment=1)
    s_author = ParagraphStyle("Author", parent=base["Normal"], fontName=F,
                              fontSize=10, alignment=1, spaceAfter=10)
    s_h1 = ParagraphStyle("H1", parent=base["Heading1"], fontName="Calibri-Bold",
                          fontSize=12.5, textColor=colors.HexColor("#1f2937"),
                          spaceBefore=10, spaceAfter=4)
    s_h2 = ParagraphStyle("H2", parent=base["Heading2"], fontName="Calibri-Bold",
                          fontSize=11, textColor=colors.HexColor("#374151"),
                          spaceBefore=7, spaceAfter=3)
    s_body = ParagraphStyle("Body", parent=base["BodyText"], fontName=F,
                            fontSize=10, leading=12.5, alignment=TA_JUSTIFY,
                            spaceAfter=4)
    s_bullet = ParagraphStyle("Bullet", parent=s_body, leftIndent=14,
                              bulletIndent=2, spaceAfter=2)
    s_math = ParagraphStyle("Math", parent=s_body, alignment=1,
                            fontName=F, fontSize=10.5, leading=14,
                            spaceBefore=3, spaceAfter=5)
    s_caption = ParagraphStyle("Caption", parent=base["Normal"], fontName=F,
                               fontSize=9, alignment=1,
                               textColor=colors.HexColor("#374151"),
                               spaceBefore=2, spaceAfter=8)
    s_cell = ParagraphStyle("Cell", parent=base["BodyText"], fontName=F,
                            fontSize=8.5, leading=10.5, spaceAfter=0,
                            alignment=TA_LEFT)
    s_cell_hdr = ParagraphStyle("CellHdr", parent=s_cell, fontName="Calibri-Bold",
                                textColor=colors.white)
    s_cell_num = ParagraphStyle("CellNum", parent=s_cell, alignment=2)

    P = lambda t: Paragraph(t, s_body)
    H1 = lambda t: Paragraph(t, s_h1)
    H2 = lambda t: Paragraph(t, s_h2)
    M = lambda t: Paragraph(t, s_math)
    Bul = lambda t: Paragraph(t, s_bullet)
    CAP = lambda t: Paragraph(t, s_caption)

    def make_table(rows, col_widths, num_cols=None, hdr_bg="#1f2937"):
        num_cols = num_cols or []
        wrapped = []
        for r_idx, row in enumerate(rows):
            wrapped_row = []
            for c_idx, c in enumerate(row):
                if r_idx == 0:
                    style = s_cell_hdr
                elif c_idx in num_cols:
                    style = s_cell_num
                else:
                    style = s_cell
                wrapped_row.append(Paragraph(str(c), style))
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
        Paragraph("Section 5 — Mapping to UK Observables", s_title),
        Paragraph("Lucas Leturia &middot; Master&rsquo;s Dissertation, PUC Chile &middot; Entrega III &middot; May 2026",
                  s_author),
        P("Operationalises the captive-demand FTPL model of Section 4 against UK data. Four subsections: postwar repression "
          "context (1945–1980), steady-state mapping, year-by-year wedge identification, and the wedge time series with "
          "convenience-yield comparison."),
        M("v<sub>t</sub> = E<sub>t</sub> ∑<sub>j ≥ 0</sub> (∏<sub>k=1</sub><sup>j</sup> M<sub>t+k</sub>) (s<sub>t+j</sub> + R<sub>t+j</sub>)"),
    ]

    # =================================================================
    # §5.1
    # =================================================================
    story += [
        H1("5.1 UK Postwar Episode as Late-Stage Repression"),
        P("The UK 1945–1980 period operationalises Jeanne&rsquo;s (2025) &lsquo;third stage&rsquo; of fiscal repression: "
          "after conventional taxation and bank-balance-sheet absorption are exhausted, the sovereign reaches into "
          "regulated long-term savings pools (pensions, insurers, captive banks) at administered prices."),

        H2("Institutional instruments (annotated outline)"),
        Bul("&bull; <b>Capital Issues Committee (CIC), 1936–1959.</b> Pre-1958 control over new long-dated sterling issues; "
            "voluntary by statute but enforced via Bank moral suasion plus the Borrowing (Control and Guarantees) Act 1946. "
            "<i>Capie (2010) Ch. 7; Cairncross (1985) Ch. 4; BoE Quarterly Bulletins 1955–1965.</i>"),
        Bul("&bull; <b>Exchange controls (Exchange Control Act 1947 → abolition 1979).</b> Investment-dollar premium plus "
            "approval-required outflows kept savings inside the gilt market. Howe&rsquo;s October 1979 abolition is the "
            "cleanest single break-point. <i>Capie (2010) Ch. 14; Mills (2014).</i>"),
        Bul("&bull; <b>Building society Recommended Rate System (1939–1983).</b> Coordinated deposit rates kept retail savings "
            "in mortgage assets at negative real returns. <i>Boddy (1980); Davies &amp; Davies (2014).</i> Indirect channel; "
            "less load-bearing for the long end."),
        Bul("&bull; <b>Pension and insurance regulation of gilt holdings.</b> Pre-1986 reserve and solvency requirements de "
            "facto channelled life-insurer and DB-pension assets into long-dated gilts — the historical analog of the modern "
            "LDI mandate. <i>Hannah (1986); BoE QB sector accounts 1965–1978.</i>"),
        Bul("&bull; <b>Bank of England operational practices in the gilt market.</b> Government Broker (Mullens &amp; Co. to 1986) "
            "and the Bank&rsquo;s market-making functioned as a long-end price stabiliser. Big Bang 1986 is the second clean "
            "break. <i>Allen (2014); Roberts (2013).</i>"),

        H2("Quantitative magnitudes (Table 5.1)"),
        make_table(
            [["Year", "Nom. GDP (£m)", "Debt par (£m)", "Debt/GDP par", "Debt/GDP MV", "10y gilt (%)", "CPI inflation (%)"],
             ["1945", "9,697",   "23,466",   "2.42", "2.35", "2.64",  "2.80"],
             ["1960", "26,412",  "28,122",   "1.06", "0.93", "5.82",  "0.79"],
             ["1980", "258,411", "109,924",  "0.43", "0.31", "13.91", "15.15"],
             ["1945–1980 avg", "—", "—", "1.13", "1.03", "6.85", "6.65"]],
            col_widths=[2.7*cm, 2.4*cm, 2.2*cm, 2.0*cm, 2.0*cm, 1.9*cm, 2.1*cm],
            num_cols=[1, 2, 3, 4, 5, 6],
        ),
        Spacer(1, 3),
        P("UK central-government debt-to-GDP fell from <b>235%</b> (1945, market value) to <b>31%</b> (1980, market value), "
          "a reduction of roughly 200 percentage points over 35 years. Running real yield averages near zero (6.85% running "
          "yield vs. 6.65% inflation); the substantive liquidation channel is the revaluation of long-duration gilts issued "
          "at low coupons during the early-period administered-yield regime. Reinhart–Sbrancia (2015) Table 8 capture this "
          "by computing a <i>total return</i> including capital losses: <b>average annual real return of approximately "
          "&minus;1.6 to &minus;2.0 percent</b> for UK gilts 1945–1980."),
        P("Decomposition by instrument is <i>not</i> separately identified in aggregate sources. Reinhart–Sbrancia themselves do "
          "not decompose. The recommendation is to report aggregate magnitudes and describe each instrument qualitatively."),

        # =============================================================
        # §5.2
        # =============================================================
        H1("5.2 Steady-State Mapping to Data"),
        P("Reference period: <b>2015–2019</b> — post-GFC, pre-COVID, pre-mini-budget. Five years of stable macro and "
          "pension-regulatory conditions, the narrowest window in the sample where all six FTPL inputs are credibly stationary."),

        H2("Mapping table (Table 5.2)"),
        make_table(
            [["Symbol", "Name", "Source", "Value"],
             ["v̄", "Real debt MV / GDP", "Millennium A1 col 77 / col 23", "1.07"],
             ["s̄/ȳ", "Primary balance / GDP", "Millennium A1 col 71 / col 23", "−0.036"],
             ["s̄/v̄", "Primary balance / debt MV", "derived from above", "−0.033"],
             ["w<sub>S</sub>, w<sub>L</sub>", "Short+med, Long shares of debt MV", "DMO Annual Review 2024–25 (§3.4 inheritance)", "0.63, 0.37"],
             ["χ̄", "Long-bond share of issuance", "DMO Annual Review", "0.37"],
             ["b̄<sup>L</sup>/ȳ", "Long-bucket gilt MV / GDP", "DMO 15+ bucket (§3.4 best-guess)", "0.18"],
             ["b̄<sup>S</sup>/ȳ", "Short+med gilt MV / GDP", "DMO 0–15y bucket", "0.37"],
             ["λ̄<sup>L</sup>V̄<sup>liab</sup>/ȳ", "Captive-demand pool / GDP", "PPF Purple Book s179 + BoE Insurance Aggregate TPs (2015–2019 avg)", "≈ 1.30"],
             ["ω̄", "Long-end wedge", "§3.4 sample average (literature-β)", "0.121"],
             ["R̄/v̄", "Rent / debt MV", "Implied: 1 − β − s̄/v̄", "0.04"]],
            col_widths=[2.8*cm, 4.6*cm, 6.8*cm, 2.0*cm],
            num_cols=[3],
        ),
        Spacer(1, 3),

        H2("Closed-form ω̄ from the derivation note"),
        M("ω̄ = [λ̄<sup>L</sup>V̄<sup>liab</sup>(1 − βδ) − β·b̄<sup>L</sup>] / [β(b̄<sup>L</sup> + δ·λ̄<sup>L</sup>V̄<sup>liab</sup>)]"),
        P("The closed form connects ω̄ directly to the captive pool, the long stock, and the deep parameters. Evaluated at "
          "β = 0.99, δ = 0.96 with the 2015–2019 averages, this delivers a value that should equal the §3.4 sample mean "
          "ω̄ = 0.121 up to measurement error and within-sample drift. The closed-form / sample-mean gap is itself a useful "
          "diagnostic of mis-measurement in V<sup>liab</sup>; the FTPL identity over-identifies ω̄."),

        # =============================================================
        # §5.3
        # =============================================================
        H1("5.3 Identifying the Wedge from Gilt Yields"),
        P("The §3.4 calibration recovers ω<sub>t</sub> year-by-year from the FTPL identity. This subsection specifies an "
          "independent yield-based identification."),

        H2("Approach: 10y gilt minus 10y OIS spread"),
        P("The swap spread ss<sub>t</sub> ≡ y<sup>gilt</sup><sub>10,t</sub> − y<sup>OIS</sup><sub>10,t</sub> is the long-"
          "standing UK measure of gilt-specific premium. Negative swap spreads (gilt yield below the OIS rate) indicate "
          "convenience-yield demand for gilts above and beyond the credit-risk-free OIS reference. We construct "
          "ω<sub>t</sub> from the spread via the model&rsquo;s duration approximation:"),
        M("ω<sub>t</sub> ≈ −D &middot; ss<sub>t</sub>, &nbsp;&nbsp; D = 1/(1 − βδ) ≈ 19.8 years."),

        H2("Identification assumptions (flag explicitly)"),
        Bul("&bull; <b>OIS as risk-free reference.</b> OIS curves out to 10y exist on BoE data from 2009 onward only; "
            "pre-2009 we cannot apply this approach. Earlier literature uses LIBOR swap rates, gilt-Bund spreads, or AAA-corp "
            "spreads — each with their own confounds."),
        Bul("&bull; <b>OIS carries no captive-demand premium of its own.</b> Approximately right for the UK because OIS "
            "counterparties aren&rsquo;t subject to LDI-style mandates, but during liquidity events (March 2020, September 2022) "
            "bank-balance-sheet constraints distort OIS pricing too. Retained as headline; flagged as a known caveat."),
        Bul("&bull; <b>The duration mapping is first-order accurate near steady state.</b> For large wedges (2020 spike, "
            "September 2022) the linearisation understates the magnitude."),

        H2("Considered alternatives, rejected for this draft"),
        Bul("&bull; <b>AAA-corp-minus-gilt spread.</b> UK sterling AAA effective yield not on free APIs; ICE-BofA series on "
            "Bloomberg/Refinitiv but not in convenient FRED form. Flagged for future extension."),
        Bul("&bull; <b>Term-structure model fit to non-captive curve segments.</b> Out of scope; a full structural estimation "
            "in its own right."),
        Bul("&bull; <b>Reis (2025) supranational-spread method.</b> Requires AAA-supranational (EIB) bond yields by maturity; "
            "replication data not pursued per agreed scope."),
        Bul("&bull; <b>Bahaj–Czech–Ding–Reis (2025) UK convenience-yield series.</b> Replication-data availability not verified."),

        # =============================================================
        # §5.4
        # =============================================================
        H1("5.4 Wedge Time Series and Convenience-Yield Comparison"),
        Image(str(FIG / "fig1_omega_overlay.png"), width=15.5*cm, height=8.5*cm),
        CAP("<b>Figure 1.</b> UK long-end wedge ω, two identification approaches. Top: FTPL-identity ω from §3.4 (red squares), "
            "annual 2010–2024. Bottom: swap-spread ω = −D &middot; (10y gilt − 10y OIS), annual mean of monthly BoE data, "
            "2009–2024. Vertical dashed lines: 2008 (QE begins), 2022 Q3 (mini-budget). Note the very different vertical "
            "scales — the two series disagree in level."),
        Image(str(FIG / "fig2_conv_yield_bps.png"), width=15.5*cm, height=7.0*cm),
        CAP("<b>Figure 2.</b> Yield wedge implied by 10y gilt − OIS spread in basis points (blue). Green band: "
            "Greenwood–Hanson–Vayanos / Vayanos–Vila steady-state range (30–100 bps)."),

        H2("Subperiod statistics (Table 5.3)"),
        make_table(
            [["Period", "n", "FTPL mean", "FTPL SD", "Swap mean", "Swap SD", "Corr."],
             ["Liberalised 1996–2007", "12", "—",      "—",     "—",      "—",     "—"],
             ["Post-crisis 2008–2019", "12", "+0.198", "0.150", "−0.042", "0.025", "+0.37"],
             ["Post-2020",             "5",  "+0.321", "0.386", "−0.027", "0.029", "+0.15"]],
            col_widths=[4.0*cm, 1.0*cm, 2.3*cm, 1.8*cm, 2.2*cm, 1.8*cm, 1.6*cm],
            num_cols=[1, 2, 3, 4, 5, 6],
        ),
        Spacer(1, 4),

        H2("A substantive finding the chapter should report honestly"),
        P("The two identification approaches <b>disagree in level by an order of magnitude</b> over the overlapping sample. "
          "Over 2008–2019 the FTPL-implied ω averages +0.198 (long gilts ~20% above unconstrained fundamental price) while the "
          "swap-spread-implied ω averages −0.042 (gilts ~4% <i>below</i> the OIS-implied fundamental, carrying a small "
          "fiscal/term premium). Correlation is positive but modest (+0.37 over 2008–2019, +0.15 post-2020). The 2020 episode "
          "is the most extreme divergence: FTPL ω = 1.01 (driven by the COVID primary deficit) while swap-spread ω = −0.015."),
        P("Three non-mutually-exclusive interpretations:"),
        Bul("1. <b>FTPL over-attributes the wedge</b> because λ̄<sup>L</sup>V̄<sup>liab</sup> overstates the <i>binding</i> "
            "portion of LDI demand. Purple Book DB liabilities and total insurance TPs include LDI-binding and non-binding "
            "portions; if only a fraction is binding, effective λV is smaller and ω is smaller."),
        Bul("2. <b>The OIS curve is not a clean fundamental.</b> Bank dealer constraints distort OIS pricing during stress "
            "episodes, biasing swap-spread ω toward smaller values."),
        Bul("3. <b>The two approaches measure different objects.</b> FTPL recovers all fiscal-backing premium (not just "
            "captive-demand-driven), while swap-spread picks up the convenience-yield component only. The two coincide if "
            "captive demand is the only deviation, but diverge whenever there are other deviations (e.g., a fiscal-risk "
            "premium that depresses gilt prices, partly offsetting the LDI premium)."),
        P("Interpretation (3) is most likely closest to right; (1) and (2) are empirically plausible and worth robustness "
          "checks. The 2020 episode in particular illustrates (3): the FTPL identity attributes the COVID primary deficit to "
          "the residual it labels as ω, when the underlying economic story is closer to &lsquo;fiscal absorption&rsquo; than to "
          "&lsquo;captive-demand intensification.&rsquo;"),

        H2("Interpretive frame (deliberately tentative)"),
        P("The chapter&rsquo;s substantive claim — that <b>the same wedge has different drivers in different regimes</b> — is "
          "partially testable in our 2008–2024 sample but not directly testable for the 1945–1980 episode. In repressed "
          "periods (1945–1980), the implied wedge would have been much larger and unambiguously positive (no fiscal-risk "
          "premium when the sovereign can&rsquo;t default under exchange controls). In post-2008 periods, the captive-demand "
          "channel and a small fiscal-risk premium work in opposite directions and the observed gilt price reflects their net."),
        P("Extending the time series back to 1945 requires reconstructing V<sup>liab</sup><sub>t</sub> from BoE Quarterly "
          "Bulletin sector accounts, a labour-intensive archival project beyond the scope of this draft."),

        # =============================================================
        # Caveats
        # =============================================================
        PageBreak(),
        H1("Caveats and limitations (consolidated)"),
        Bul("1. <b>V<sup>liab</sup> pre-1995</b> not directly available. Purple Book starts 2006; Solvency II 2016. "
            "Pre-1995 pension/insurance gilt holdings in BoE Quarterly Bulletin sector accounts require archival extraction."),
        Bul("2. <b>DMO bucket-level market values pre-2010</b> partial; anchored on 2024–25 Annual Review and propagated "
            "backward via long-gilt share. Robustness check sweeping long share over 30–45% recommended."),
        Bul("3. <b>The 2020 magnitude (FTPL ω ≈ 1.0)</b> is most sensitive to DMO best-guess inputs. A plausible DMO-corrected "
            "magnitude is 100–150 bps yield wedge (vs. our 225 bps headline)."),
        Bul("4. <b>Annual frequency cannot speak to September 2022</b>; the within-year spike is smoothed."),
        Bul("5. <b>Duration mapping ω ≈ −D &middot; ss</b> first-order near steady state; degrades for large wedges."),
        Bul("6. <b>Swap-spread identification assumes OIS has no captive-demand premium of its own.</b> May be violated in "
            "stress episodes."),
        Bul("7. <b>Instrument-level decomposition of 1945–1980 real liquidation</b> not feasible from aggregate data."),
        Bul("8. <b>The level disagreement between FTPL-identity ω and swap-spread ω is itself a research finding.</b> "
            "Robustness on (i) the binding-fraction of λ̄V̄ and (ii) OIS-as-fundamental should be done. Neither pursued in "
            "this draft."),
        Bul("9. <b>Reinhart–Sbrancia (2015) total-return number for 1945–1980 (−1.6 to −2.0%/yr)</b> is cited from their "
            "published table; my running-yield calculation from the Millennium data gives a near-zero average over the same "
            "period. The R–S number is the more meaningful object for the liquidation narrative."),

        # =============================================================
        # Data appendix
        # =============================================================
        H1("Data appendix"),
        H2("Series catalogue"),
        make_table(
            [["Series", "Freq", "Sample", "Source", "Transformation"],
             ["Nominal UK GDP", "annual", "1700–2016", "Millennium A1 col 23/24", "none"],
             ["Central Govt debt par", "annual", "1700+", "Millennium A1 col 76", "none"],
             ["Central Govt debt MV", "annual", "1900+", "Millennium A1 col 77", "÷ GDP"],
             ["Public sector net borrowing", "annual", "1700+", "Millennium A1 col 71", "÷ GDP"],
             ["10y gilt yield (calendar avg)", "annual", "1700+", "Millennium A1 col 47", "none"],
             ["CPI inflation", "annual", "1700+", "Millennium A1 col 42", "none"],
             ["10y gilt nominal spot rate", "monthly", "1970–", "BoE GLC Nominal sheet 4. spot curve", "annual mean"],
             ["10y OIS rate", "monthly", "2009–", "BoE OIS sheets 2. or 4. spot curve", "annual mean"],
             ["FTPL-identity ω<sub>t</sub>", "annual", "2010–2024", "§3.4 outputs_filled_v2.xlsx", "as derived"],
             ["Swap-spread ω<sub>t</sub>", "annual", "2009–2026", "derived: −D &middot; (gilt − OIS), D = 19.8", "annual mean"]],
            col_widths=[4.5*cm, 1.6*cm, 2.0*cm, 5.5*cm, 3.5*cm],
            num_cols=[],
        ),
        Spacer(1, 4),

        H2("Splicing / vintage notes"),
        Bul("&bull; Millennium debt-MV series (col 77) splices ESA conventions across the 1968 and 1995 ESA revisions; "
            "BoE compilers handle the splicing. Used as-is."),
        Bul("&bull; 10y gilt yield from Millennium A1 col 47 (calendar-year average of monthly observations) differs slightly "
            "from BoE GLC Nominal at month-end. Difference is at the second decimal; doesn&rsquo;t affect results."),
        Bul("&bull; OIS sheet name differs across BoE OIS files (2009–2015 uses &lsquo;2. spot curve&rsquo;, 2016+ uses "
            "&lsquo;4. spot curve &rsquo; with trailing space). The build script tries both names."),

        H2("Code"),
        P("All deliverables reproducible from a single <font face='Courier'>python build.py</font> in "
          "<font face='Courier'>section5/</font>:"),
        Bul("&bull; <font face='Courier'>download.py</font> — fetch BoE Millennium + GLC Nominal + OIS into raw/"),
        Bul("&bull; <font face='Courier'>build.py</font> — compute series, tables, figures into figures/"),
        Bul("&bull; <font face='Courier'>section5.md</font> — markdown source with LaTeX equations + booktabs tables"),
        Bul("&bull; <font face='Courier'>make_pdf.py</font> — this PDF rendering"),
        P("The §3.4 ω series is read from <font face='Courier'>../calibration/outputs_filled_v2.xlsx</font>."),
    ]

    doc.build(story)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
