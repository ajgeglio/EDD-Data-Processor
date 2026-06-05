#!/usr/bin/env python3
"""
Simple version: For each ZIP in a folder, create an Excel with the same base name (<zip>.xlsx)
containing only the three data sheets—no Key tab, no formatting.

Sheets (written only if data exists), fixed order:
  1) LabSample_v1
  2) TestResultQC_v1
  3) TestBatch_v1

File matching inside each ZIP is by suffix preceded by '_' or '-':
  *_LabSample_v1(.txt|.csv)
  *_TestResultQC_v1(.txt|.csv)
  *_TestBatch_v1(.txt|.csv)

Data handling:
  - All columns are read as TEXT to preserve significant figures and leading zeros.
  - 'NA' remains the literal string "NA" (not converted to NaN), and blanks remain blanks.

Usage examples:
  python EDD-zipdataProcessor_simple.py --input-dir ./zips --output-dir ./out --strict
  python EDD-zipdataProcessor_simple.py --input-dir ./zips --strict
"""

import argparse
import io
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Dict, Optional, Iterable

import pandas as pd

EXPECTED_SUFFIXES = ["LabSample_v1", "TestResultQC_v1", "TestBatch_v1"]
SHEET_ORDER = ["LabSample_v1", "TestResultQC_v1", "TestBatch_v1"]  # write order


def argument_parser():
    p = argparse.ArgumentParser(
        description="Create one Excel per ZIP (same base name), with three ordered data sheets. No Key sheet. No formatting. Reads all fields as text."
    )
    p.add_argument("input_dir", type=Path, default=Path("."), help="Folder with ZIP files (default: current directory).")
    p.add_argument("--glob", type=str, default="*.zip", help="Glob for ZIPs (default: *.zip).")
    p.add_argument("--output-dir", type=Path, default=None, help="Optional output folder; if omitted, saves next to each ZIP.")
    p.add_argument("--sep", type=str, default=",", help="Field delimiter for the text files (default: ',').")
    p.add_argument("--encoding", type=str, default="utf-8", help="Text encoding to try first (fallback to latin-1). Tip: use 'utf-8-sig' if a BOM is present.")
    p.add_argument("--no-header", action="store_true", help="Treat files as having no header row.")
    p.add_argument("--add-source", action="store_true", help="Add a 'source_zip' column with the ZIP filename.")
    p.add_argument("--strict", action="store_true", help="Fail if any ZIP is missing one or more expected files.")
    return p.parse_args()


def read_csv_from_zip(
    zf: zipfile.ZipFile,
    member: str,
    sep: str = ",",
    encoding: str = "utf-8",
    **read_csv_kwargs,
) -> pd.DataFrame:
    """
    Read CSV/TXT from a zip member, preserving text exactly:
      - dtype=str (all columns text)
      - keep_default_na=False (don't auto-convert NA-like strings)
      - na_filter=False (faster; keep blanks as blanks)
    """
    # Always enforce text-preserving settings:
    read_csv_kwargs = {
        "dtype": str,
        "keep_default_na": False,
        "na_filter": False,
        # Avoid date parsing/munging
        # "infer_datetime_format": False,
        "parse_dates": False,
        **read_csv_kwargs,
    }

    with zf.open(member, "r") as raw:
        try:
            return pd.read_csv(
                io.TextIOWrapper(raw, encoding=encoding, newline=""),
                sep=sep,
                **read_csv_kwargs,
            )
        except UnicodeDecodeError:
            raw.seek(0)
            return pd.read_csv(
                io.TextIOWrapper(raw, encoding="latin-1", newline=""),
                sep=sep,
                **read_csv_kwargs,
            )


def detect_expected_suffix(base_stem: str, suffixes: Iterable[str]) -> Optional[str]:
    """
    Determine which expected suffix a base filename (no extension) belongs to.
    Accepts '_' or '-' before the suffix, or matches exactly; case-insensitive.
    """
    lower = base_stem.lower()
    for suf in suffixes:
        s = suf.lower()
        if lower.endswith("_" + s) or lower.endswith("-" + s) or lower == s:
            return suf
    return None


def extract_three_frames_from_zip(
    zip_path: Path,
    sep: str = ",",
    encoding: str = "utf-8",
    no_header: bool = False,
    add_source: bool = False,
    strict: bool = False,
) -> Dict[str, Optional[pd.DataFrame]]:
    """
    From a single ZIP, return a dict mapping each expected suffix to its DataFrame (or None if missing).
    If strict=True and any expected file is missing, raise a RuntimeError.
    """
    frames: Dict[str, Optional[pd.DataFrame]] = {k: None for k in EXPECTED_SUFFIXES}
    read_csv_kwargs = {}
    if no_header:
        read_csv_kwargs["header"] = None

    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [m for m in zf.namelist() if m.lower().endswith((".txt", ".csv"))]
        for m in sorted(members):
            base = Path(PurePosixPath(m).name).stem
            suf = detect_expected_suffix(base, EXPECTED_SUFFIXES)
            if not suf:
                continue
            try:
                df = read_csv_from_zip(zf, m, sep=sep, encoding=encoding, **read_csv_kwargs)
            except Exception as e:
                print(f"Error reading {m} in {zip_path.name}: {e}", file=sys.stderr)
                continue

            if add_source:
                df.insert(0, "source_zip", zip_path.name)

            if frames[suf] is None:
                frames[suf] = df
            else:
                frames[suf] = pd.concat([frames[suf], df], ignore_index=True, sort=False)

    missing = [s for s in EXPECTED_SUFFIXES if frames[s] is None]
    if strict and missing:
        raise RuntimeError(f"{zip_path.name} is missing expected files for: {', '.join(missing)}")

    return frames


def write_simple_workbook(
    out_path: Path,
    frames_by_sheet: Dict[str, Optional[pd.DataFrame]],
):
    """
    Create a workbook with only the three data sheets, in fixed order.
    No Key sheet. No formatting. Writes only sheets that have data.
    """
    with pd.ExcelWriter(out_path, engine="openpyxl", mode="w") as writer:
        for sheet in SHEET_ORDER:
            df = frames_by_sheet.get(sheet)
            if df is None:
                continue
            if len(df) > 1_048_576:
                print(
                    f"Warning: sheet '{sheet}' has {len(df):,} rows; Excel may truncate beyond 1,048,576.",
                    file=sys.stderr,
                )
            df.to_excel(writer, sheet_name=sheet, index=False)


def main():
    args = argument_parser()

    input_dir = args.input_dir
    ext = args.glob

    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    if args.output_dir is not None:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    zip_paths = sorted(input_dir.glob(ext))
    print(f"### Found {len(zip_paths)} ZIP files at: {input_dir / ext}")
    if not zip_paths:
        raise FileNotFoundError(f"No ZIPs found at: {input_dir / ext}")

    for zp in zip_paths:
        if zp.is_dir() or zp.suffix.lower() != ".zip":
            continue

        frames = extract_three_frames_from_zip(
            zip_path=zp,
            sep=args.sep,
            encoding=args.encoding,
            no_header=args.no_header,
            add_source=args.add_source,
            strict=args.strict,
        )
        print(f"### Processed {zp.name}: found sheets: {[k for k, v in frames.items() if v is not None]}")
        # If nothing matched (non-strict), skip writing a workbook.
        if all(frames[k] is None for k in EXPECTED_SUFFIXES):
            print(f"!!! Skipping {zp.name}: no expected files found.")
            continue

        # Same base name as the ZIP, .xlsx extension
        out_name = zp.stem + ".xlsx"
        out_path = (args.output_dir / out_name) if args.output_dir else (zp.with_suffix(".xlsx"))

        write_simple_workbook(out_path, frames)
        print(f"### Wrote: {out_path.resolve()}")


if __name__ == "__main__":
    main()