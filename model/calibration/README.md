# §3.4 Calibration — pipeline

Two paths to a populated input workbook: a "real-data, MANUAL-where-not-scriptable" path
(`inputs.xlsx`) and a "best-guess everywhere" path (`inputs_filled.xlsx`).

```
calibration/
├── download.py             fetch raw API/CSV/zip data into ./raw/
├── download_pdfs.py        fetch DMO + PPF + BoE Insurance PDFs/CSV into ./pdfs/
├── build_inputs.py         parse raw/ -> inputs.xlsx (auto + MANUAL cells)
├── build_inputs_filled.py  parse raw/ + pdfs/ -> inputs_filled.xlsx (no MANUAL cells)
├── calibrate.py            inputs*.xlsx -> outputs*.xlsx; takes --input
├── raw/                    auto-downloaded JSON / Excel / zip
├── pdfs/                   downloaded reference PDFs and CSVs
├── inputs.xlsx             4 fields per row left MANUAL (verify yourself)
├── inputs_filled.xlsx      every field populated; cells colour-coded by provenance
├── outputs.xlsx            calibration on inputs.xlsx (empty until MANUAL filled)
├── outputs_filled.xlsx     calibration on inputs_filled.xlsx (all 15 years)
└── README.md
```

Run order:

```powershell
python download.py             # ~3 MB,  3 sources
python download_pdfs.py        # ~9 MB,  4 PDFs/CSV (Annual Review, Quarterly, Purple Book, BoE Insurance)
python build_inputs.py         # writes inputs.xlsx (MANUAL placeholders for DMO/TPR/PRA)
python build_inputs_filled.py  # writes inputs_filled.xlsx (no MANUAL — best-guess + interp)
python calibrate.py --input inputs.xlsx          # writes outputs.xlsx
python calibrate.py --input inputs_filled.xlsx   # writes outputs_filled.xlsx
```

## What auto-fills

| Field | Source | Notes |
|---|---|---|
| `GDP_nominal_GBPm` | ONS YBHA, JSON API | current-price annual, £m |
| `primary_balance_over_GDP` | OBR PSF databank, "Aggregates (per cent of GDP)" col "Primary balance" | fiscal year `YYYY-(YY+1)` mapped to calendar year `YYYY`; stored as decimal |
| `real_short_rate` | BoE GLC Real, sheet "4. spot curve" | shortest populated maturity per month, annual mean, decimal |
| `real_rate_mean_maturity_y` | derived from above | informational; lets you see the proxy maturity per year |

## What needs MANUAL entry

The four amber-coloured cells per row in `inputs.xlsx`. Sources and access notes:

### `long_duration_years`
DMO modified Macaulay duration, 15+ year segment, annual snapshot (year-end or annual average).
- Source: DMO Quarterly Review (e.g. <https://www.dmo.gov.uk/responsibilities/gilt-market/quarterly-reviews/>) or the DMO data portal (<https://www.dmo.gov.uk/data/>).
- The DMO data portal is JavaScript-rendered, so direct CSV download isn't scriptable without a headless browser. Easiest path: open the Annual Review and read off the 15+ duration figure.

### `V_liab_over_GDP`
Numerator = TPR Purple Book DB s179 liabilities + PRA Solvency II insurance technical reserves (matching-adjustment portfolio for annuity writers).
Denominator = ONS YBHA (already in column `GDP_nominal_GBPm`).
- Purple Book: <https://www.thepensionsregulator.gov.uk/en/document-library/research-and-analysis/purple-book> — one PDF per year.
- PRA Solvency II returns: <https://www.bankofengland.co.uk/prudential-regulation/regulatory-reporting> — annual aggregate tables.
- Headline calibration uses s179 (not buyout) basis.

### `long_gilt_mkt_val_over_GDP` and `short_gilt_mkt_val_over_GDP`
DMO gilt portfolio market values by maturity bucket / nominal GDP.
- DMO portfolio statistics, conventional gilts only for headline (sensitivity includes linkers per §2 of the methodology).
- Source: <https://www.dmo.gov.uk/data/> (manual download — JS-rendered portal).

## Convention choices baked into the scripts

1. **Fiscal-year mapping (OBR)**. OBR labels rows as `YYYY-(YY+1)`. We map this to calendar year `YYYY` — the year in which the fiscal year begins. This is the convention with most overlap (Apr `YYYY` → Mar `YYYY+1` is mostly in `YYYY`). The methodology PDF doesn't specify; document this in the dissertation appendix.

2. **BoE real-rate proxy**. The methodology asks for the **1-year** point of the BoE real spot curve. BoE does not publish below 2.5 years for the linker curve, and the front-end maturity that is populated varies month to month (2.5y in most months; 3y or 3.5y when the curve fit truncates). The script uses the **shortest populated maturity per month-end**, averaged over 12 month-ends per calendar year. The mean maturity per year is reported in the input sheet so the proxy is auditable.
   - Headline rate is therefore approximately a 2.5–3y real spot, not a 1y real spot.
   - For a robustness check, swap in the alternative source from the methodology: 1y nominal gilt yield (BoE GLC Nominal) minus realized 1y-ahead inflation (ONS CHAW or D7G7). This is straightforward to add later.

3. **Units**. `real_short_rate` and `primary_balance_over_GDP` are stored as **decimals** (not percent). Market-value-to-GDP fields are decimals as well (e.g. 0.85 = 85% of GDP). GDP is in £m. The calibration math assumes these conventions.

## Outputs

`outputs.xlsx` has four sheets:

- **`inputs (echo)`** — what the calibration actually consumed (after parsing).
- **`calibration`** — `year, beta, delta, Q_L_fund, v, R, rent_share, omega, Q_L, lambda_L, b_L, yield_wedge, zeta` per Listing 1.
- **`sanity`** — three checks per year per §5: `omega > 0` (Assumption 1 binds), `lambda_L in (0,1)`, `beta*delta < 1` (long-bond price finite). Cells coloured green/red.
- **`missing inputs`** — years that were skipped because a MANUAL cell wasn't filled, with the list of fields per year.

Once all four MANUAL fields are populated for at least one year, that year will appear in `calibration` and `sanity`; the rest stay in `missing inputs`.

## `inputs_filled.xlsx` — provenance of each manual cell

The second pipeline (`build_inputs_filled.py`) populates every cell. Cells are colour-coded:

- **Green** — actual reported value from the primary source
- **Amber** — interpolated/extrapolated between actual data points
- **Blue** — best-guess by Claude (cross-check before thesis use)

Per-cell sources:

| Field | Years filled from source | Years interpolated / guessed |
|---|---|---|
| `V_liab_over_GDP` numerator: PB s179 (PPF 2025 p.14 Figure 4.2) | 2011, 2016–2024 actual | 2010, 2012, 2013, 2014, 2015 (linear interp between 2006, 2011, 2016) |
| `V_liab_over_GDP` numerator: BoE Insurance Aggregate Q4 (CSV) | 2017–2024 actual | 2010–2016 (extrapolated by holding 2017 TP/GDP ratio constant) |
| `long_duration_years` | none actual | All best-guess (17–22 years, peaking 2020), anchored on DMO Annual Review 2024-25 p.54 conventional-portfolio-wide modified duration of 7.84y for end-Mar 2025 — the 15+ segment is materially longer |
| `long_gilt_mkt_val_over_GDP` | end-2024 anchored on DMO AR p.54 (conv. gilt £1,612bn × 32% long share) | 2010–2023 best-guess, reflecting QE expansion 2010–2020 and post-2022 normalisation |
| `short_gilt_mkt_val_over_GDP` | as above with 68% short+medium share | 2010–2023 best-guess |

A `provenance` sheet inside `inputs_filled.xlsx` shows the £bn numerator each year so you can audit the divisions.

## β choice — DEVIATION from methodology §2

The headline rate column (`real_short_rate`) is now set to `r = 1/β − 1` with **β = 0.99 constant** — the literature-standard FTPL discount factor; the methodology PDF §4 worked example uses exactly this value ("evaluates to approximately 19.8 at β = 0.99, δ = 0.96").

Why deviate from the methodology's stated primary source:
1. BoE doesn't publish the 1y point on the linker curve. The 2.5y proxy I have to use is deeply negative across the QE / ZLB / pre-2022 sample because LDI captive demand compresses 2y+ real yields — *exactly the channel the model is trying to identify*. Feeding that proxy into β = 1/(1+r) gives β > 1 in most years and partially double-counts the very wedge ω is meant to recover.
2. Standard FTPL calibration practice (Cochrane FTPL book, Sims 2013, Leeper–Leith) fixes β = 0.99 annual as a deep parameter rather than reading it off the cyclical curve.

The BoE-observed annual mean is preserved in the `real_short_rate_BoE_observed` column for reference but isn't consumed by `calibrate.py`.

## Headline calibration result on `inputs_filled_v2.xlsx` (β = 0.99)

| Year | ω | Q_L | λ_L | β·δ | Notes |
|---|---|---|---|---|---|
| 2010 | 0.52 | 25.5 | 0.13 | <1 | post-GFC high wedge |
| 2011-2014 | 0.33 → 0.20 | ~24 | 0.15 | <1 | declining toward calm |
| 2015-2019 | 0.05 → 0.08 | ~22 | 0.15 | <1 | low-wedge period |
| 2020 | **1.01** | 44.7 | 0.15 | <1 | COVID-driven primary-deficit spike |
| 2021-2022 | 0.10–0.16 | ~22 | 0.15-0.16 | <1 | post-COVID, includes mini-budget pressure |
| 2023-2024 | 0.15–0.19 | ~21 | 0.16 | <1 | normalising above pre-COVID baseline |

**All 15 years pass all three sanity checks** (`ω > 0`, `λ_L ∈ (0,1)`, `β·δ < 1`). The pattern matches §6 of the methodology's expected narrative: ZLB calm 2015-2019, COVID spike 2020, mini-budget aftershock 2022, post-intervention normalisation 2023-2024.

The 2020 magnitude (ω ≈ 1.0) is large but consistent: COVID drove a -13% primary balance into the augmented FTPL identity. Worth flagging in the dissertation. If you want to dampen it, refine the DMO best-guesses (long-gilt market value moved sharply in 2020 too).

## Reproducing the data

`download.py` is idempotent — re-running overwrites `raw/`. Sources update annually:
- ONS YBHA: revised at every quarterly GDP release.
- OBR PSF databank: monthly (filename like `PSF_aggregates_databank_Apr-5.xlsx`); the script targets the public-finances-databank landing page redirect.
- BoE GLC Real: refreshed monthly; zip contains three xlsx (1979-2015 / 2016-2024 / 2025-present).
