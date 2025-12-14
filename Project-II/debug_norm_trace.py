
import pandas as pd
import csv
import ast
import numpy as np

INPUT_CSV = "/root/workspace/LargeFiles/TMDB_all_movies.csv"
COUNTRY_MAP_CSV = "country_map.csv"

# 1. Load Country Map
name_to_code = {}
with open(COUNTRY_MAP_CSV, 'r', encoding='utf-8') as f:
    for row in csv.reader(f):
        if len(row) >= 2:
            name_to_code[row[0].strip().lower()] = row[1].strip().lower()

# Add aliases
name_to_code["united states of america"] = "us"

# 2. Inspect Header
with open(INPUT_CSV, 'r', encoding='utf-8', errors='replace') as f:
    header_line = f.readline().strip()
    headers = [h.strip('"') for h in header_line.split(',')]
    print(f"Headers: {headers}")
    
    col_map = {}
    for i, h in enumerate(headers):
        clean_h = h.lower().strip()
        if clean_h == "id": col_map["tmdb_id"] = i  # Should be 0 based on previous head
        if clean_h == "production_countries": col_map["production_countries"] = i
    
    print(f"Column Map: {col_map}")

# 3. Process Chunk
chunk = pd.read_csv(INPUT_CSV, nrows=50)

# Apply Logic
# Direct
s_direct = None
# JSON
def extract_iso(val):
    try:
        if not val or pd.isna(val) or val == "[]": return ""
        val_str = str(val).strip()
        
        # Name Lookup Trace
        first_name = val_str.split(',')[0].strip().lower()
        if "united states" in first_name:
            print(f"DEBUG: Found '{first_name}', In Map? {first_name in name_to_code}")
            
        if first_name in name_to_code:
            return name_to_code[first_name]
    except:
        pass
    return ""

# Apply to 'production_countries' column by NAME (pandas reads by header)
# Wait, my script used column INDEX or Name?
# The script uses `col_map` which stores NAMES likely?
# Let's check the script.
# Script uses `col_map = { target_col_name: source_col_name/index }`?

# Replicating script logic exactly:
# chunk is a DataFrame.
# pc_col = col_map["production_countries"]
# The real script determines `col_map["production_countries"] = "production_countries"` string if by header.

# In the real script, `col_map` values are COLUMN NAMES if pandas read with header=0.
# Let's assume correct mapping.

if "production_countries" in chunk.columns:
    print("Found 'production_countries' column in DataFrame.")
    res = chunk["production_countries"].astype(str).apply(extract_iso)
    print("\nResults:")
    for idx, val in enumerate(res):
        raw = chunk.iloc[idx]["production_countries"]
        print(f"Row {idx}: Raw='{raw}' -> Extracted='{val}'")
else:
    print("Column 'production_countries' NOT FOUND in DataFrame!")
