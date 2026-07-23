"""make_session_summary.py — render SESSION_SUMMARY.pdf.

A short, advisor-meeting-friendly summary of the microfounded captive-habitat
NK-FTPL work, built around the calibration "trilemma". Uses reportlab + Calibri
(handles the math diacritics), matching the project's other PDF generators.
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
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = Path(__file__).resolve().parent
OUT = HERE / "SESSION_SUMMARY.pdf"
CMP = HERE / "figures" / "hab_compare.png"

for name, fn in [("Calibri", "calibri.ttf"), ("Calibri-Bold", "calibrib.ttf"),
                 ("Calibri-Italic", "calibrii.ttf")]:
    try:
        pdfmetrics.registerFont(TTFont(name, rf"C:\Windows\Fonts\{fn}"))
    except Exception:
        pass
try:
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily("Calibri", normal="Calibri", bold="Calibri-Bold",
                       italic="Calibri-Italic")
    BASE = "Calibri"
except Exception:
    BASE = "Helvetica"

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName=BASE, fontSize=15,
                    spaceBefore=10, spaceAfter=5, textColor=colors.HexColor("#1a3b5c"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName=BASE, fontSize=11.5,
                    spaceBefore=9, spaceAfter=3, textColor=colors.HexColor("#27496d"))
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName=BASE, fontSize=9.7,
                      leading=13.5, alignment=TA_JUSTIFY, spaceAfter=5)
BUL = ParagraphStyle("BUL", parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2.5)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8.5, leading=11,
                       textColor=colors.HexColor("#444444"))
TITLE = ParagraphStyle("TITLE", parent=ss["Title"], fontName=BASE, fontSize=19,
                       textColor=colors.HexColor("#1a3b5c"), spaceAfter=2)

S = []
def P(t, st=BODY): S.append(Paragraph(t, st))
def bullets(items, st=BUL):
    for it in items:
        S.append(Paragraph(it, st, bulletText="•"))
def gap(h=5): S.append(Spacer(1, h))


def tbl(data, widths, header=True, font=8.6):
    t = Table(data, colWidths=widths, hAlign="LEFT")
    style = [("FONTNAME", (0, 0), (-1, -1), BASE), ("FONTSIZE", (0, 0), (-1, -1), font),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc"))]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27496d")),
                  ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("FONTNAME", (0, 0), (-1, 0), BASE),
                  ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#1a3b5c"))]
    t.setStyle(TableStyle(style))
    return t


# ============================== PAGE 1 =======================================
P("Captive-Habitat FTPL in an NK model", TITLE)
P("Session summary — numerical implementation, the calibration trilemma, and "
  "what it means", ParagraphStyle("sub", parent=BODY, fontSize=11,
  textColor=colors.HexColor("#27496d"), spaceAfter=8))
P("L. Leturia · prepared as a working note · code in <font face='%s'>nk/habitat/</font> "
  "(full detail in REPORT.md)" % BASE, SMALL)
gap(6)

P("Executive summary", H1)
P("We built the <b>microfounded</b> two-agent preferred-habitat FTPL model (the spec "
  "in <i>habitat_nk_spec.pdf</i>) that replaces the Entrega III reduced-form mandate: "
  "a short-habitat agent A and a long-habitat agent B optimise portfolios, a regulatory "
  "mandate forces B onto long gilts, A absorbs the residual, and the price wedge and "
  "fiscal rent <i>emerge</i> from this distortion. The steady state, log-linearisation, "
  "Klein/QZ solution and impulse responses all run and pass the spec's internal checks.")
P("The headline scientific result is a <b>calibration trilemma</b>: the microfoundation "
  "<b>cannot simultaneously</b> deliver (i) a plausible habitat-preference strength, "
  "(ii) a data-consistent debt maturity structure, and (iii) the measured 14% wedge. "
  "The reduced form hid this by conflating two different 'long shares'. Surfacing the "
  "trilemma is the sharp contribution of going micro.")

gap(4)
P("The trilemma in one table", H1)
P("Both columns use the same headline configuration (see p.2); the <b>only</b> difference "
  "is how the long-bond share χ̄ is interpreted. Both solve, pass all steady-state checks, "
  "and are determinate.")
gap(2)
data = [
    ["", "Cal A: χ̄ read as a\nquantity share", "Cal B: χ̄ set to the\ndata market value"],
    ["Quantity long-share χ̄", "0.353", "0.023"],
    ["Market-value long-share wL", "0.93", "0.35  (= DMO data)"],
    ["Habitat strength φ (to hit ω̄=14%)", "3.0  — plausible", "37.9 — implausibly large"],
    ["Fiscal rent  X̄ / debt", "0.34%", "0.11%"],
    ["λ +1% tightening → long price", "+0.15%", "+0.72%"],
    ["λ +1% tightening → inflation", "+0.47%", "+1.20%"],
    ["Monetary 25bp → output", "−25.2%", "−8.7%"],
]
S.append(tbl(data, [6.4*cm, 4.6*cm, 4.6*cm]))
gap(4)
P("<b>Read it diagonally.</b> Cal A buys a believable habitat penalty (φ≈3) but the debt "
  "is then 93% long by market value, which makes the price level hyper-sensitive (a 25bp "
  "rate move implies a 25% output swing). Cal B fixes the maturity to the data, which cuts "
  "that hyper-sensitivity roughly threefold — but the wedge now needs a habitat penalty an "
  "order of magnitude larger. You can move along this frontier; you cannot get off it.", BODY)

P("One-line version for the meeting", H2)
P("<i>“A 14% market-value wedge generated from a realistically small long-bond captive "
  "position requires an implausibly strong habitat preference; making the preference "
  "plausible instead forces a counterfactually long-dominated debt stock and a "
  "hyper-elastic price level. That trade-off is the result.”</i>", BODY)

S.append(PageBreak())

# ============================== PAGE 2 =======================================
P("What the model is, and how it solves", H1)
P("Two optimising agents (population split 50/50) hold one short and one long nominal "
  "bond subject to a quadratic 'habitat' penalty for deviating from a preferred long "
  "share θ. The regulator's mandate binds on B's long position and replaces B's long-bond "
  "Euler equation; A prices both bonds, so the government is priced by A's stochastic "
  "discount factor. The block sits inside a standard NK environment (Calvo Phillips curve, "
  "passive Taylor rule). We compute the distorted, binding-mandate steady state "
  "numerically, log-linearise (20 equations), and solve with the Entrega III Klein/QZ "
  "routine.")
P("Internal checks the implementation passes", H2)
bullets([
    "All six of the spec's steady-state sanity checks (interior allocations, positive "
    "wedge, mandate binds with margin, correct determinant sign, …).",
    "The −1 inflation-revaluation coefficient (an identity that must hold exactly).",
    "Blanchard–Kahn determinacy: 9 stable / 11 unstable roots, with the relative-wealth "
    "'closing device' root sitting just inside the unit circle at 1−ε, as required.",
    "A non-trivial cross-check: the fiscal rent computed from the cross-sectional "
    "portfolio formula equals what the government valuation identity independently "
    "requires, to machine precision.",
])

P("The key modelling decisions we made", H1)
P("<b>Decision A — the mandate redistributes, it does not expand supply.</b> In the first "
  "pass the aggregate long supply expanded one-for-one with the mandate, so agent A was "
  "never actually squeezed and the long price <i>fell</i> on a tightening (wrong sign). "
  "Switching to a non-accommodating issuance rule — the mandate redistributes a fixed long "
  "stock from A to B — squeezes A off habitat, widens the wedge, and makes the long price "
  "<b>rise</b> on a tightening, as the financial-repression story requires.")
P("<b>Vayanos–Vila term premium (calibrated to gilt data).</b> Agent A is the arbitrageur; "
  "it demands a duration-risk premium that captive demand <i>compresses</i>. We calibrated "
  "its strength to UK gilt data (Bloomberg pull): a ~1%/yr term premium at the model's "
  "duration gives θ_tp ≈ 0.05. It more than doubles the long-price response on a tightening "
  "(good for the mechanism) but is far too small to cure the hyper-elasticity.")
P("<b>Realistic shock sizes.</b> The early 'insane' numbers were partly a unit-shock "
  "artifact (a unit innovation here is a ~100% / thousands-of-bp shock). Responses are now "
  "reported per 1% regulatory tightening and per 25bp monetary move.")

P("Two things that do NOT fix the hyper-elastic price level", H1)
bullets([
    "<b>Stickier prices — wrong lever.</b> Inflation here is pinned by the fiscal "
    "valuation identity, not by the Phillips curve; the Phillips curve only backs out the "
    "output needed to deliver that inflation (ŷ ≈ π̂ / κ). Making prices stickier (smaller "
    "κ) leaves inflation unchanged and makes output <i>explode</i>. We verified this.",
    "<b>A Bohn-style surplus-feedback / s-shaped surplus — helps the path, not the "
    "impact.</b> Cochrane's partial-repayment device smooths inflation over time and avoids "
    "the deficits-cause-deflation puzzle, but the impact jump is set by the valuation "
    "identity, so it barely moves on impact. The only lever that touches the monetary "
    "impact is reducing long-debt dominance — i.e. the calibration choice above.",
])

S.append(PageBreak())

# ============================== PAGE 3 =======================================
P("A clarification you flagged — Leeper (1991) and 'partial Ricardian'", H1)
P("The <b>regime</b> is genuinely either/or: a unique equilibrium needs exactly one active "
  "and one passive authority (active money + passive fiscal, or passive money + active "
  "fiscal). You cannot blend regimes. <b>But 'passive fiscal' is a threshold, not a point.</b> "
  "A surplus rule that responds to debt with coefficient γ is still <i>active</i> fiscal "
  "(still FTPL, still determinate under passive money) for any γ below the debt-stabilising "
  "threshold. So a positive-but-below-threshold debt response — 'partial Ricardian' — "
  "changes magnitudes without changing the regime. And Cochrane's s-shaped surplus is a "
  "<i>different axis entirely</i>: it shapes the time-series of surplus innovations "
  "(deficit-then-repayment), which is orthogonal to the active/passive classification, so "
  "it never touches the Leeper threshold. Both of these are consistent with your reading; "
  "they live <i>inside</i> the active-fiscal region, not across the regime boundary.")

P("Why the signs and magnitudes come out as they do", H1)
P("Two of the spec's predicted signs are conditional and come out 'against' the reduced "
  "form, and the price level is hyper-elastic. Both trace to a single fact: with a long "
  "perpetuity (decay δ=0.96, duration ~5y, priced at ~23), even a modest quantity share is "
  "a dominant <i>market-value</i> share, so the long-bond revaluation channel governs the "
  "price level (the FTPL-with-long-term-debt regime of Cochrane and Corhay–Kung–Morales). "
  "In that regime a contractionary monetary shock is <b>disinflationary</b> — this is "
  "documented in the literature and can be kept and cited. And because the fiscal rent is "
  "small relative to the debt (0.1–0.3%), the valuation identity ties the long price and "
  "inflation together: you cannot get 'long price rises' <i>and</i> 'inflation falls' at "
  "the same time unless the rent is a materially larger share of backing.")

P("What I'd raise with the advisor", H1)
bullets([
    "<b>The calibration choice is yours to make and it is the headline.</b> Report Cal B "
    "(data-consistent dynamics, honest about the large φ) as the main case, Cal A as the "
    "'what makes the penalty plausible' comparison — and let the gap between them be the "
    "result. Or accept the trilemma framing explicitly.",
    "<b>Can the rent be made first-order?</b> A larger captive sector μ_B (the rent scales "
    "with it) might relieve the trilemma by raising X̄/debt so the rent genuinely backs the "
    "price level — worth a quick exploration.",
    "<b>Duration vs the captive bucket.</b> The model's δ implies a 5-year bond, but the "
    "LDI/insurance captive demand is for 15–30y gilts. Matching the long end deepens the "
    "long-debt dominance — the same tension as the trilemma.",
    "<b>Deferred (your call):</b> a genuinely risk-based, time-varying term premium needs a "
    "higher-order / Epstein–Zin solution; we used a reduced-form stand-in for now.",
])

if CMP.exists():
    gap(4)
    P("Impulse responses under the two calibrations (λ at +1%, monetary at 25bp)", H2)
    S.append(Image(str(CMP), width=17*cm, height=6.9*cm))
    P("Solid = Cal A (χ̄ as quantity); dashed = Cal B (data market value). Note how Cal B "
      "(dashed) damps the monetary output and inflation responses.", SMALL)

gap(8)
P("Code &amp; artifacts: <font face='%s'>nk/habitat/</font> — params.py, steady_state.py, "
  "linearize.py, klein.py, run_habitat.py, calibrate.py, sweeps.py, "
  "compare_calibrations.py; full write-up in REPORT.md; figures in figures/." % BASE, SMALL)

SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=1.4*cm, bottomMargin=1.3*cm,
                  leftMargin=1.7*cm, rightMargin=1.7*cm,
                  title="Captive-Habitat FTPL — session summary").build(S)
print("wrote", OUT)
