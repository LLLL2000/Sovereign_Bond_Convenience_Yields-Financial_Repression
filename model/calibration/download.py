"""Fetch raw data files for the §3.4 calibration into ./raw/.

Sources that auto-download:
  - ONS YBHA            nominal GDP (annual, current prices, £m)
  - OBR PSF databank    primary balance, % of GDP
  - BoE GLC Real        1y real spot rate, month-end

Sources that require manual entry (see README.md):
  - DMO 15+ duration, long / short+medium gilt market values
  - TPR Purple Book DB pension liabilities
  - PRA Solvency II insurance technical reserves
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
RAW.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

SOURCES = [
    {
        "name": "ons_ybha",
        "url": "https://www.ons.gov.uk/economy/grossdomesticproductgdp/timeseries/ybha/pn2/data",
        "out": RAW / "ons_ybha.json",
        "note": "Nominal GDP, current prices, annual (£m). ONS series YBHA.",
    },
    {
        "name": "obr_psf_databank",
        "url": "https://obr.uk/download/public-finances-databank-april-2026/",
        "out": RAW / "obr_psf_databank.xlsx",
        "note": "OBR Public Sector Finances aggregates databank.",
    },
    {
        "name": "boe_glcreal_zip",
        "url": "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcrealmonthedata.zip",
        "out": RAW / "boe_glcreal.zip",
        "note": "BoE GLC Real month-end yield curves, 1979-present (three xlsx).",
        "extract_to": RAW / "boe_glcreal",
    },
]


def fetch(src: dict) -> None:
    print(f"[fetch] {src['name']}: {src['url']}")
    r = requests.get(src["url"], headers=UA, timeout=120, allow_redirects=True)
    r.raise_for_status()
    src["out"].write_bytes(r.content)
    print(f"  saved {src['out'].name}  ({len(r.content):,} bytes)")
    extract_to = src.get("extract_to")
    if extract_to is not None:
        extract_to.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(extract_to)
            for n in z.namelist():
                print(f"  extracted -> {extract_to.name}/{n}")


def main() -> int:
    errors = 0
    for src in SOURCES:
        try:
            fetch(src)
        except Exception as e:
            errors += 1
            print(f"  !! FAILED: {e}")
    print()
    if errors:
        print(f"done with {errors} failure(s)")
        return 1
    print("done, all sources fetched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
