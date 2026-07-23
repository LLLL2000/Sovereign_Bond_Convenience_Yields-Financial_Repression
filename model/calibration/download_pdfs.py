"""Fetch authoritative PDFs / CSVs that document the four MANUAL inputs.

Sources:
  - DMO Annual Review 2024-25 (gilt 15+ duration and market values by bucket).
  - DMO Quarterly Review Apr-Jun 2025 (end-Mar 2025 snapshot; calendar-year cross-check).
  - PPF Purple Book 2025 (DB s179 aggregate liabilities, historical table to 2006).
  - BoE Insurance Aggregate Annual Data file (Solvency II technical provisions, 2016-2024).
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
PDFS = HERE / "pdfs"
PDFS.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

SOURCES = [
    {
        "name": "dmo_annual_review_2024_25.pdf",
        "url": "https://dmo.gov.uk/media/dmgaetip/gar2025a.pdf",
        "note": "DMO Annual Review 2024-25 (published Aug 2025). Portfolio duration and market-value-by-bucket tables.",
    },
    {
        "name": "dmo_quarterly_apr_jun_2025.pdf",
        "url": "https://www.dmo.gov.uk/media/opunj3ps/apr-jun25.pdf",
        "note": "DMO Quarterly Review Apr-Jun 2025. End-Mar 2025 snapshot.",
    },
    {
        "name": "ppf_purple_book_2025.pdf",
        "url": "https://ppf.co.uk/-/media/PPF-Website/Public/Purple-Book-Data-2025/Pension-Protection-Fund-Purple-Book-2025-accessible.pdf",
        "note": "Purple Book 2025. DB s179 aggregate liabilities back to 2006 (Mar year-ends).",
    },
    {
        "name": "boe_insurance_aggregate.csv",
        "url": "https://www.bankofengland.co.uk/-/media/boe/files/statistics/insurance-aggregate/insurance-aggregate-data-file.csv",
        "note": "BoE Insurance Aggregate Annual Data (Solvency II QRTs, UK insurers, 2016-).",
    },
]


def fetch(src: dict) -> bool:
    out = PDFS / src["name"]
    print(f"[fetch] {src['name']}")
    try:
        r = requests.get(src["url"], headers=UA, timeout=120, allow_redirects=True)
        r.raise_for_status()
        out.write_bytes(r.content)
        print(f"  saved {out.name}  ({len(r.content):,} bytes)")
        return True
    except Exception as e:
        print(f"  !! FAILED: {e}")
        return False


def main() -> int:
    errors = sum(0 if fetch(s) else 1 for s in SOURCES)
    print()
    print(f"done; {len(SOURCES) - errors}/{len(SOURCES)} files fetched")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
