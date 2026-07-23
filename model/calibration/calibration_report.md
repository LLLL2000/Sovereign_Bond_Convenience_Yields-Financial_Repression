# §5.2 calibration — clean-sample headline ω̄

This report restricts the §3.4 calibration to the years where every input is either reported actual data or a transparent assumption anchored on a single DMO publication. It computes the implied steady-state wedge ω̄ on that window, runs the three sanity checks, and recommends a single headline value for §5.2 of the dissertation.

The math in `calibrate.py` is unchanged. β = 0.99 and δ = 0.96 conventions are preserved (δ is implied from `D` and β rather than fixed at 0.96; see §5 below).

---

## 1. Clean sample window and binding inputs

| Input | Cleanness | Binding window |
|---|---|---|
| `real_short_rate` | Parameter, constant `r = 1/β − 1` with β = 0.99 | All years (convention) |
| `primary_balance_over_GDP` | OBR PSF databank, auto-parsed | All years |
| `GDP_nominal_GBPm` | ONS YBHA, auto-parsed | All years |
| `V_liab_over_GDP` numerator | PB s179 actual (PPF 2025 p.14) + BoE Insurance Aggregate Q4 actual (CSV) | **2017–2024** (both actual) |
| Total conv. gilt MV (anchor for `bL_mkt + bS_mkt`) | DMO Annual Review, gross market value at fiscal year-end | **2021–2024** (4 fiscal-year-end snapshots covered by GAR 2022-23, 2023-24, 2024-25) |
| Conv. gilt modified duration (anchor for `D`) | DMO Annual Review, portfolio-wide, market-value-weighted | **2021–2024** (same source) |
| Long-share split `bL / (bL + bS)` | **Never directly reported** in any DMO publication. Nominal-weighted long share derived from QR Apr-Jun 2025 gilts-in-issue list (transparent assumption) | All years (single derived value applied throughout) |

**Joint clean-or-anchored window: 2021–2024 (4 years).**

The 15+ maturity bucket cannot be cleanly populated for *any* year — the DMO publishes only portfolio-wide market value and duration, never broken out by maturity bucket. I therefore make one explicit deviation from the original calibration semantics: `long_duration_years` and `long_gilt_mkt_val_over_GDP` are anchored on portfolio-wide conventional-gilt aggregates rather than on the 15+ segment specifically. The cost (model object widens from "15+ gilt" to "the whole conventional gilt portfolio treated as a single long bond at its portfolio duration") is the price of using only audit-able data. The benefit: every numerator and denominator in the clean window is either a DMO/ONS/OBR/PPF/BoE primary-source figure or a single transparent share derived from the same DMO PDF.

The long-share split itself remains an assumption — there is no DMO publication that breaks market value out by maturity bucket — so I derive it from the **nominal-weighted Short/Medium/Long classification of every conventional gilt in the QR Apr-Jun 2025 gilts-in-issue list (p.7)**. Summing nominal values by bucket and using the standard DMO 15+ cutoff for "Long" yields **0.3532**, marginally higher than the README's 32% best-guess. This is reported as the headline split and supplemented with a sensitivity band.

---

## 2. Empirical inputs by year

All values for calendar year *Y* anchor on the fiscal-year-end **31 March of *Y* + 1** (consistent with the OBR fiscal-to-calendar mapping baked into `build_inputs.py`).

| Year | GDP £m (ONS YBHA) | Primary balance (OBR) | Total conv. MV £bn (DMO) | DMO mod. duration y | PB s179 £bn (PPF p.14) | BoE Insurance TP Q4 £bn |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 2,322,652 | −2.980% | 1,748.0 | 11.47 | 1,673.8 | 2,378.97 |
| 2022 | 2,580,949 | −1.175% | 1,547.0 |  9.17 | 1,473.9 | 2,057.99 |
| 2023 | 2,752,164 | −1.866% | 1,612.0 |  8.39 | 1,031.5 | 2,246.02 |
| 2024 | 2,890,664 | −2.374% | 1,677.0 |  7.84 |   947.9 | 2,380.48 |

Source citations:
- GDP: [ONS series YBHA](https://www.ons.gov.uk/economy/grossdomesticproductgdp/timeseries/ybha/pn2) (`raw/ons_ybha.json`).
- Primary balance: OBR PSF databank, sheet "Aggregates (per cent of GDP)" col "Primary balance"; fiscal year *YYYY*–(YY+1) mapped to calendar *YYYY* (`raw/obr_psf_databank.xlsx`).
- DMO conv. gilt MV and mod. duration: [GAR 2022-23 Tables 19-20](https://www.dmo.gov.uk/media/tfidb5fy/gar2023.pdf), [GAR 2023-24 Tables 19-20](https://www.dmo.gov.uk/media/5rqb2scf/gar2024_final.pdf), [GAR 2024-25 Table 20](https://www.dmo.gov.uk/media/dmgaetip/gar2025a.pdf) (`pdfs/dmo_annual_review_2024_25.pdf`). Gross values, including DMO holdings.
- PB s179: [PPF Purple Book 2025 p.14 Figure 4.2](https://www.thepensionsregulator.gov.uk/en/document-library/research-and-analysis/purple-book) (`pdfs/ppf_purple_book_2025.pdf`).
- BoE Insurance TP Q4: [BoE Insurance Aggregate quarterly returns](https://www.bankofengland.co.uk/prudential-regulation/regulatory-reporting) (`pdfs/boe_insurance_aggregate.csv`), Life + Non-Life sum.
- Long-share split = 0.3532 from [DMO QR Apr-Jun 2025 p.7 gilts-in-issue list](https://www.dmo.gov.uk/media/opunj3ps/apr-jun25.pdf), nominal-weighted (`pdfs/dmo_quarterly_apr_jun_2025.pdf`).

Derived inputs fed to `calibrate.py`:

| Year | v = total MV / GDP | bL = 0.3532·v | bS = 0.6468·v | V_liab / GDP |
|---|---:|---:|---:|---:|
| 2021 | 0.7526 | 0.2658 | 0.4868 | 1.7449 |
| 2022 | 0.5994 | 0.2117 | 0.3877 | 1.3684 |
| 2023 | 0.5857 | 0.2069 | 0.3789 | 1.1909 |
| 2024 | 0.5801 | 0.2049 | 0.3753 | 1.1514 |

---

## 3. Implied ω̄ on the clean window

Run: `python calibrate.py --input inputs_clean.xlsx --output outputs_clean.xlsx`

### Headline (long-share = 0.3532, DMO-derived)

| Year | ω | Q_L | λ_L |
|---|---:|---:|---:|
| 2021 | 0.1633 | 13.21 | 0.1523 |
| 2022 | 0.0915 |  9.91 | 0.1547 |
| 2023 | 0.1345 |  9.42 | 0.1737 |
| 2024 | 0.1684 |  9.07 | 0.1780 |
| **Average 2021–2024** | **0.1394** | 10.40 | 0.1647 |

### Sensitivity to the long-share assumption

ω̄ depends only on β, total MV, primary balance, and the long-share split (duration enters only `Q_L_fund`, `Q_L`, and `β·δ`, not ω). The split is the dominant uncertainty in the calibration. Varying it across plausible values:

| Year | ω @ 25% | ω @ 32% (README guess) | ω @ 35.3% (DMO QR derived) | ω @ 40% |
|---|---:|---:|---:|---:|
| 2021 | 0.2475 | 0.1834 | **0.1634** | 0.1415 |
| 2022 | 0.1343 | 0.1019 | **0.0915** | 0.0799 |
| 2023 | 0.2011 | 0.1505 | **0.1344** | 0.1169 |
| 2024 | 0.2558 | 0.1892 | **0.1685** | 0.1459 |
| **Average** | **0.2097** | **0.1563** | **0.1394** | **0.1211** |

Reading the band: the 4-year average ω̄ lies between roughly **0.12 and 0.21**, with the DMO-derived headline at **0.14**.

---

## 4. Sanity checks (per §5 of the methodology)

All three checks pass for every year in the clean window:

| Year | ω > 0 | λ_L ∈ (0,1) | β·δ < 1 |
|---|---|---|---|
| 2021 | ✓ (0.163) | ✓ (0.152) | ✓ (0.913; δ=0.922 from D=11.47) |
| 2022 | ✓ (0.092) | ✓ (0.155) | ✓ (0.891; δ=0.900 from D=9.17) |
| 2023 | ✓ (0.135) | ✓ (0.174) | ✓ (0.881; δ=0.890 from D=8.39) |
| 2024 | ✓ (0.168) | ✓ (0.178) | ✓ (0.872; δ=0.881 from D=7.84) |

Assumption 1 binds (ω > 0), the long bond is a proper fraction of captive liabilities (λ_L well inside the unit interval, all four years), and the long-bond price is finite.

---

## 5. Recommended headline value

**ω̄ = 0.14** (4-year average 2021–2024 at the DMO QR-derived long-share of 0.3532).

Justification: this is the average across four post-COVID-acute fiscal years using DMO-anchored gilt totals, actual PB s179, actual BoE Insurance TP, and a long-share derived from the gilts-in-issue list rather than guessed; it sits squarely within the README's prior best-guess range (0.10–0.19) but rests on cleaner provenance. The full sensitivity band 0.12–0.21 should be stated in the dissertation as the headline uncertainty driven by the unobservable long-share split.

If the dissertation prefers a single-year anchor over a multi-year average, **ω̄ = 0.17 (2024 only)** is the appropriate alternative — most recent, post-mini-budget normalization, and identical in clean-provenance status to the other three years.

### Notes on deviations from the original §3.4 calibration

- `long_duration_years` is anchored on the **portfolio-wide** market-value-weighted modified duration of conventional gilts (DMO GAR), not the 15+ segment specifically. The 15+ segment duration is not published by the DMO in any of the available PDFs. Because ω is mathematically independent of D (it depends only on β, v, s, and the long-share split), this deviation moves `Q_L`, `Q_L_fund`, and the yield wedge — not the headline ω.
- The long-share split (35.32%) is derived nominal-weighted from the QR Jun-2025 gilts-in-issue list. MV-weighted shares would be slightly lower (longer-maturity gilts trade at deeper price discounts when yields rise), so the headline ω̄ at the MV-weighted share would be marginally higher than 0.14 — well within the reported sensitivity band.
- Calendar-year mapping uses the same OBR fiscal-to-calendar convention as the rest of the pipeline: calendar year *Y* anchors on the fiscal-year-end 31 March of *Y* + 1.

### Artifacts

- `inputs_clean.xlsx` — restricted-sample input workbook (4 years, every cell either actual data, OBR/ONS auto-parsed, or transparent QR-derived split).
- `outputs_clean.xlsx` — calibration output produced by running `calibrate.py --input inputs_clean.xlsx` unchanged.
- `build_inputs_clean.py` — builder script for `inputs_clean.xlsx`; reads the same `raw/` and `pdfs/` directories as the original pipeline.
