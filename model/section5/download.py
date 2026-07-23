"""Fetch raw data for Section 5."""

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
        "name": "millennium",
        "url": "https://www.bankofengland.co.uk/-/media/boe/files/statistics/research-datasets/a-millennium-of-macroeconomic-data-for-the-uk.xlsx",
        "out": RAW / "millennium_data.xlsx",
        "note": "BoE 'A Millennium of Macroeconomic Data' (Hills, Thomas & Dimsdale; latest version). "
                "Covers UK macro 1086-present, including government debt/GDP, gilt yields, prices.",
    },
    {
        "name": "glcnom",
        "url": "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcnominalmonthedata.zip",
        "out": RAW / "glcnom_monthly.zip",
        "extract_to": RAW / "glcnom",
        "note": "BoE GLC Nominal month-end yield curves, 1970s-present.",
    },
    {
        "name": "ois",
        "url": "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/oismonthedata.zip",
        "out": RAW / "ois_monthly.zip",
        "extract_to": RAW / "ois",
        "note": "BoE OIS (Overnight Index Swap) month-end yield curves.",
    },
]


def fetch(src):
    print(f"[fetch] {src['name']} <- {src['url']}")
    r = requests.get(src["url"], headers=UA, timeout=300, allow_redirects=True)
    r.raise_for_status()
    src["out"].write_bytes(r.content)
    print(f"  saved {src['out'].name}  ({len(r.content):,} bytes)")
    ex = src.get("extract_to")
    if ex is not None:
        ex.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(ex)
            for n in z.namelist():
                print(f"  extracted -> {ex.name}/{n}")


def main():
    errors = 0
    for s in SOURCES:
        try:
            fetch(s)
        except Exception as e:
            print(f"  !! FAILED: {e}")
            errors += 1
    print(f"\ndone; {len(SOURCES) - errors}/{len(SOURCES)} sources fetched")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
