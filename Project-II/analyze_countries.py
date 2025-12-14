
import csv
import ast
import collections

INPUT_CSV = "/root/workspace/LargeFiles/TMDB_all_movies.csv"
COUNTRY_MAP_CSV = "country_map.csv"

# Load current map
name_to_code = {}
try:
    with open(COUNTRY_MAP_CSV, 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                name_to_code[row[0].strip().lower()] = row[1].strip().lower()
except:
    pass

# Add my manual aliases to match the script
name_to_code["united states of america"] = "us"
name_to_code["usa"] = "us"
name_to_code["united kingdom"] = "gb"
name_to_code["uk"] = "gb"
name_to_code["south korea"] = "kr"
name_to_code["russia"] = "ru"
name_to_code["china"] = "cn"
name_to_code["hong kong"] = "hk"

def extract_iso(val):
    try:
        if not val or val == "[]": return None
        val_str = str(val).strip()
        
        # JSON
        if val_str.startswith("["):
            try:
                data = ast.literal_eval(val_str)
                if isinstance(data, list) and data:
                    first = data[0]
                    if isinstance(first, dict):
                        iso = first.get("iso_3166_1") or first.get("iso") or first.get("code")
                        if iso: return "FOUND_JSON"
            except:
                pass
        
        # Name Lookup
        first_name = val_str.split(',')[0].strip().lower()
        if first_name in name_to_code:
            return "FOUND_NAME"
        
        return None # Failed
    except:
        return None

print("Analyzing unmapped countries...")
unmapped_counter = collections.Counter()
total = 0
found = 0

with open(INPUT_CSV, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        raw_val = row.get("production_countries", "")
        
        # Simulate the fallback logic: if Direct 'country' is empty (which most are), checking this column
        res = extract_iso(raw_val)
        if res:
            found += 1
        else:
            # Clean up the raw val for reporting
            # If it looks like a list, take the name from it for better grouping
            display_val = raw_val
            if raw_val.startswith("["):
                 try:
                    data = ast.literal_eval(raw_val)
                    if data and isinstance(data[0], dict):
                         display_val = data[0].get('name', raw_val)
                 except: pass
            
            if len(display_val) > 50: display_val = display_val[:50] + "..."
            unmapped_counter[display_val] += 1
        
        if total % 100000 == 0:
            print(f"Scanned {total}...")

print(f"Total: {total}")
print(f"Mapped: {found} ({found/total*100:.1f}%)")
print(f"Unmapped: {total - found}")
print("\nTop 20 Unmapped Values:")
for val, count in unmapped_counter.most_common(20):
    print(f"{count}: {val}")
