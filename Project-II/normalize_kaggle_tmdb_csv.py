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
    ap.add_argument("--country-map", dest="country_map", help="CSV path mapping country_name to country_code")
    args = ap.parse_args()

    inp = os.path.expanduser(args.inp)
    outp = os.path.expanduser(args.outp)
    
    # Load Country Map
    name_to_code = {}
    if args.country_map and os.path.exists(args.country_map):
        try:
            with open(args.country_map, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        name_to_code[row[0].strip().lower()] = row[1].strip().lower()
            print(f"[INFO] Loaded {len(name_to_code)} country mappings.")
        except Exception as e:
            print(f"[WARN] Failed to load country map: {e}")

    # Manual Aliases for common mismatches
    name_to_code["united states of america"] = "us"
    name_to_code["usa"] = "us"
    name_to_code["united kingdom"] = "gb"
    name_to_code["uk"] = "gb"
    name_to_code["south korea"] = "kr"
    name_to_code["russia"] = "ru"
    name_to_code["china"] = "cn"
    name_to_code["hong kong"] = "hk"
    name_to_code["macao"] = "mo"
    # Historical / Political Mappings (Best Effort for Data Retention)
    # Mapping to primary successor state or modern equivalent to ensure import
    name_to_code["soviet union"] = "ru"       # USSR -> Russia
    name_to_code["czechoslovakia"] = "cz"     # -> Czechia
    name_to_code["yugoslavia"] = "rs"         # -> Serbia (primary successor)
    name_to_code["east germany"] = "de"       # -> Germany
    name_to_code["west germany"] = "de"       # -> Germany
    name_to_code["palestinian territory"] = "ps"
    name_to_code["kyrgyz republic"] = "kg"
    name_to_code["syrian arab republic"] = "sy"
    name_to_code["congo"] = "cg"
    name_to_code["lao people's democratic republic"] = "la"
    name_to_code["brunei darussalam"] = "bn"
    name_to_code["vatican city"] = "va"
    name_to_code["cote d'ivoire"] = "ci"
    name_to_code["burma"] = "mm"
    name_to_code["north korea"] = "kp"

    # 1. Inspect header to map columns
    # ... (header inspection logic remains) ...
    sample = pd.read_csv(inp, nrows=5)
    cols_lc = [c.lower() for c in sample.columns]
    col_lc_to_real = {c.lower(): c for c in sample.columns}

    # ... (column mapping logic remains, assuming col_map is available) ...
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
    
    print(f"Processing {inp} -> {outp} (Vectorized)...")
    # ... (lines counting remains) ...
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

    print(f"[DEBUG] Headers parsed: {list(sample.columns)}")
    print(f"[DEBUG] Column map detected: {col_map}")
    
    processed_lines = 0
    
    first_chunk = True
    
    # 2. Process in chunks using csv.DictReader (More robust than pandas parser)
    # We read using standard csv lib, then convert batch to DataFrame for vectorized processing
    
    def chunk_generator(filepath, size):
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row)
                if len(batch) >= size:
                    yield pd.DataFrame(batch)
                    batch = []
            if batch:
                yield pd.DataFrame(batch)

    for chunk in chunk_generator(inp, args.chunksize):
        chunk_len = len(chunk)
        processed_lines += chunk_len
        
        # Ensure columns exist (csv.DictReader keys are headers)
        # We need to map our detected col_map to actual columns in DataFrame
        # DataFrame columns will be the CSV headers
        
        # Pandas auto-detection of column names from dict keys is automatic.
        # But we need to ensure col_map points to valid columns.
        
        # Create a new DataFrame for output with target columns
        out_df = pd.DataFrame()

        # ... (tmdb_id logic) ...
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

        # --- String Columns (Strip & Clean) ---
        for tgt, src in [("imdb_id", "imdb_id"), ("title", "title"), 
                         ("original_title", "original_title"), ("original_language", "original_language"),
                         ("release_date", "release_date")]:
            src_col = col_map[src]
            if src_col:
                # fillna, astype(str), strip, and replace internal newlines
                out_df[tgt] = chunk[src_col].fillna("").astype(str).str.strip().str.replace(r'[\r\n]+', ' ', regex=True)
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
        # --- Country ISO2 (Complex Logic) ---
        # Strategy: Coalesce(DirectColumn, ProductionCountriesJSON)
        # 1. Extract from Direct Column (if exists)
        s_direct = None
        src_col = col_map["country_iso2"]
        if src_col:
            s_direct = chunk[src_col].fillna("").astype(str).str.strip().str.slice(0, 2).str.lower().str.replace(r'[\r\n]+', '', regex=True)
            # Treat "nan" text as empty
            s_direct = s_direct.replace(r'(?i)^nan$', '', regex=True)

        # 2. Extract from Production Countries JSON
        s_json = None
        pc_col = col_map["production_countries"]
        if pc_col:
            def extract_iso(val):
                try:
                    if not val or pd.isna(val) or val == "[]": return ""
                    
                    val_str = str(val).strip()
                    # A. JSON List parsing
                    if val_str.startswith("["):
                        import ast
                        try:
                            data = ast.literal_eval(val_str)
                            if isinstance(data, list) and data:
                                first = data[0]
                                if isinstance(first, dict):
                                    iso = first.get("iso_3166_1") or first.get("iso") or first.get("code")
                                    if iso: return str(iso)[:2].lower()
                        except:
                            pass
                    
                    # B. Simple Name Lookup (Fallback)
                    first_name = val_str.split(',')[0].strip().lower()
                    if first_name in name_to_code:
                        return name_to_code[first_name]
                except:
                    pass
                return ""
            
            s_json = chunk[pc_col].astype(str).apply(extract_iso)

        # 3. Combine: Use Direct if present, else JSON
        if s_direct is not None and s_json is not None:
             out_df["country_iso2"] = np.where(s_direct.ne(""), s_direct, s_json)
        elif s_direct is not None:
             out_df["country_iso2"] = s_direct
        elif s_json is not None:
             out_df["country_iso2"] = s_json
        else:
             out_df["country_iso2"] = ""

        if "country_iso2" in out_df.columns:
            # Clean "nan", "NaN" (case insensitive) and strictly enforce 2 chars
            out_df["country_iso2"] = out_df["country_iso2"].astype(str).str.lower().replace("nan", "")
            out_df["country_iso2"] = out_df["country_iso2"].apply(lambda x: x if len(x) == 2 else "")
        else:
            out_df["country_iso2"] = ""

        # Enforce exact column order for COPY command alignment
        final_cols = ["tmdb_id", "imdb_id", "title", "original_title", "original_language", 
                      "release_date", "runtime", "country_iso2", "popularity", 
                      "vote_average", "vote_count", "budget", "revenue"]
        
        # Add missing columns as empty
        for col in final_cols:
            if col not in out_df.columns:
                out_df[col] = ""
        
        out_df = out_df[final_cols]

        # Write to CSV
        # QUOTE_MINIMAL is compatible with standard COPY
        out_df.to_csv(outp, mode='w' if first_chunk else 'a', index=False, header=first_chunk, encoding='utf-8', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        
        first_chunk = False

        if total_lines > 0:
            pct = (processed_lines / total_lines) * 100
            print(f"[INFO] Progress: {pct:.1f}% ({processed_lines}/{total_lines})", end='\r')
            
    print(f"\n[OK] Normalized Kaggle CSV written to: {outp}")

if __name__ == "__main__":
    main()
