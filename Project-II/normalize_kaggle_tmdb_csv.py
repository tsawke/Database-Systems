#!/usr/bin/env python3
import argparse
import csv
import json
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

def pick_col(cols_lc: List[str], candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in cols_lc:
            return c
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="Input Kaggle CSV path")
    ap.add_argument("--out", dest="outp", required=True, help="Output normalized CSV path")
    ap.add_argument("--chunksize", type=int, default=500000, help="Chunk size for streaming")
    args = ap.parse_args()

    inp = os.path.expanduser(args.inp)
    outp = os.path.expanduser(args.outp)

    # 1. Inspect header to map columns
    sample = pd.read_csv(inp, nrows=5)
    cols_lc = [c.lower() for c in sample.columns]
    col_lc_to_real = {c.lower(): c for c in sample.columns}

    # Identify TMDB ID column
    tmdb_id_col = pick_col(cols_lc, ["tmdb_id", "id", "movie_id"])
    if not tmdb_id_col:
        raise SystemExit("Cannot find a TMDb id column.")
    real_tmdb_id_col = col_lc_to_real[tmdb_id_col]

    # Map other columns
    def get_real(candidates):
        c = pick_col(cols_lc, candidates)
        return col_lc_to_real[c] if c else None

    # Mapping: { TargetName: SourceName or None }
    col_map = {
        "tmdb_id": real_tmdb_id_col,
        "imdb_id": get_real(["imdb_id", "imdbid"]),
        "title": get_real(["title", "movie_title", "name"]) or real_tmdb_id_col,
        "original_title": get_real(["original_title"]),
        "original_language": get_real(["original_language", "language"]),
        "release_date": get_real(["release_date", "released", "release"]),
        "runtime": get_real(["runtime", "duration", "run_time"]),
        "country_iso2": get_real(["country_iso2", "country", "country_code", "iso_3166_1"]),
        "popularity": get_real(["popularity"]),
        "vote_average": get_real(["vote_average", "rating", "voteavg"]),
        "vote_count": get_real(["vote_count", "votecount"]),
        "budget": get_real(["budget"]),
        "revenue": get_real(["revenue"]),
        "production_countries": get_real(["production_countries", "production_country", "countries"]) # For fallback
    }

    out_fields = ["tmdb_id","imdb_id","title","original_title","original_language",
                  "release_date","runtime","country_iso2","popularity","vote_average",
                  "vote_count","budget","revenue"]

    os.makedirs(os.path.dirname(outp), exist_ok=True)
    
    # Write header first
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()

    print(f"Processing {inp} -> {outp} (Vectorized)...")

    # 1.5 Calculate total lines for progress bar
    # Using subprocess wc -l for speed on Linux
    try:
        import subprocess
        print("[INFO] Counting total lines for progress calculation...")
        # wc -l output might be "1234 filename" or just "1234"
        wc_out = subprocess.check_output(["wc", "-l", inp]).strip().split()[0]
        total_lines = int(wc_out)
        print(f"[INFO] Total lines: {total_lines}")
    except Exception as e:
        print(f"[WARN] Could not count lines ({e}), progress bar will not show percentage.")
        total_lines = 0

    processed_lines = 0
    
    # 2. Process in chunks using Vectorization
    for chunk in pd.read_csv(inp, chunksize=args.chunksize, dtype=str, on_bad_lines='skip'):
        chunk_len = len(chunk)
        processed_lines += chunk_len
        
        # Create a new DataFrame for output with target columns
        out_df = pd.DataFrame()

        # --- TMDB ID (Required, Int) ---
        # Coerce to numeric, drop NaNs or 0
        s_tmdb = pd.to_numeric(chunk[col_map["tmdb_id"]], errors='coerce').fillna(0).astype(np.int64)
        out_df["tmdb_id"] = s_tmdb
        
        # Filter invalid IDs immediately to reduce size
        valid_mask = (out_df["tmdb_id"] > 0)
        
        # If all filtered, still update progress and continue
        if not valid_mask.any():
            if total_lines > 0:
                pct = (processed_lines / total_lines) * 100
                print(f"[INFO] Progress: {pct:.1f}% ({processed_lines}/{total_lines})", end='\r')
            continue
        
        out_df = out_df[valid_mask].copy()
        chunk = chunk[valid_mask].reset_index(drop=True) # Align source chunk

        # --- String Columns (Strip) ---
        for tgt, src in [("imdb_id", "imdb_id"), ("title", "title"), 
                         ("original_title", "original_title"), ("original_language", "original_language"),
                         ("release_date", "release_date")]:
            src_col = col_map[src]
            if src_col:
                # fillna, astype(str), strip
                out_df[tgt] = chunk[src_col].fillna("").astype(str).str.strip()
            else:
                out_df[tgt] = ""

        # Truncate language to 2 chars
        out_df["original_language"] = out_df["original_language"].str.slice(0, 2).str.lower()
        
        # --- Numeric Columns (Float/Int) ---
        # Runtime (Int)
        if col_map["runtime"]:
            out_df["runtime"] = pd.to_numeric(chunk[col_map["runtime"]], errors='coerce').fillna(0).astype(int)
        else:
            out_df["runtime"] = 0
            
        # Float columns
        for tgt in ["popularity", "vote_average"]:
            src_col = col_map[tgt]
            if src_col:
                out_df[tgt] = pd.to_numeric(chunk[src_col], errors='coerce') # Keep as float, NaNs allowed (will trigger empty string in to_csv?) 
            else:
                out_df[tgt] = np.nan

        # Int columns
        for tgt in ["vote_count", "budget", "revenue"]:
            src_col = col_map[tgt]
            if src_col:
                out_df[tgt] = pd.to_numeric(chunk[src_col], errors='coerce').fillna(0).astype(np.int64)
            else:
                out_df[tgt] = 0

        # --- Country ISO2 (Complex Logic) ---
        src_col = col_map["country_iso2"]
        if src_col:
            # Direct column exists
            out_df["country_iso2"] = chunk[src_col].fillna("").astype(str).str.strip().str.slice(0, 2).str.lower()
        else:
            # Fallback to JSON parsing from production_countries
            pc_col = col_map["production_countries"]
            if pc_col:
                def extract_iso(val):
                    try:
                        if not val or pd.isna(val): return ""
                        if "iso_3166_1" not in val and "iso" not in val: return "" # optimization
                        data = json.loads(val.replace("'", '"')) # Common issue in CSVs: Python dict string repr
                        if isinstance(data, list) and data:
                            first = data[0]
                            if isinstance(first, dict):
                                iso = first.get("iso_3166_1") or first.get("iso") or first.get("code")
                                if iso: return str(iso)[:2].lower()
                    except:
                        pass
                    return ""
                
                # Apply only to this series
                out_df["country_iso2"] = chunk[pc_col].astype(str).apply(extract_iso)
            else:
                out_df["country_iso2"] = ""

        # --- Write Chunk ---
        # mode='a', header=False
        out_df.to_csv(outp, mode='a', index=False, header=False, encoding='utf-8')

        if total_lines > 0:
            pct = (processed_lines / total_lines) * 100
            print(f"[INFO] Progress: {pct:.1f}% ({processed_lines}/{total_lines})", end='\r')
            
    print(f"\n[OK] Normalized Kaggle CSV written to: {outp}")

if __name__ == "__main__":
    main()
