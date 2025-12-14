
import pandas as pd
import ast

inp = "/root/workspace/LargeFiles/TMDB_all_movies.csv"
df = pd.read_csv(inp, nrows=5)
print("Columns:", df.columns.tolist())
if "production_countries" in df.columns:
    print("Sample production_countries:")
    for val in df["production_countries"]:
        print(f"Original: {val}")
        try:
             parsed = ast.literal_eval(val)
             print(f"Parsed: {parsed}")
        except Exception as e:
             print(f"Parse Error: {e}")
else:
    print("production_countries column NOT found!")
