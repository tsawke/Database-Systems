#!/usr/bin/env python3
import argparse
import csv
import os
import time
from datetime import date, datetime
from typing import Dict, List, Optional

import requests

API_BASE = "https://api.themoviedb.org/3"

def tmdb_get(session: requests.Session, path: str, params: Optional[Dict] = None) -> Dict:
    r = session.get(f"{API_BASE}{path}", params=params or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def pick_country_iso2(prod_countries) -> str:
    if isinstance(prod_countries, list) and prod_countries:
        first = prod_countries[0]
        if isinstance(first, dict):
            iso = first.get("iso_3166_1")
            if isinstance(iso, str) and len(iso) >= 2:
                return iso[:2].lower()
    return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=os.environ.get("TMDB_BEARER_TOKEN", ""), help="TMDb API Read Access Token (Bearer). You can also set TMDB_BEARER_TOKEN env var.")
    ap.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD), typically last sync date from pipeline_state.tmdb_last_sync")
    ap.add_argument("--end-date", default=str(date.today()), help="End date (YYYY-MM-DD), default = today")
    ap.add_argument("--out", default="~/workspace/LargeFiles/tmdb_delta_normalized.csv", help="Output normalized delta CSV path")
    ap.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between detail requests to reduce rate limit risk")
    ap.add_argument("--max-pages", type=int, default=500, help="Safety cap for changes list pages")
    args = ap.parse_args()

    token = args.token.strip()
    if not token:
        raise SystemExit("TMDb token not provided. Set TMDB_BEARER_TOKEN or pass --token.")

    outp = os.path.expanduser(args.out)
    os.makedirs(os.path.dirname(outp), exist_ok=True)

    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})

    # 1) Fetch changed IDs (paginated with date chunking)
    from datetime import timedelta
    
    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    # Ensure start <= end
    if start_dt > end_dt:
        start_dt = end_dt
        
    changed_ids: List[int] = []
    
    current_start = start_dt
    while current_start <= end_dt:
        # TMDB allows max 14 days per request. We'll use 14 days chunk.
        current_end = current_start + timedelta(days=13)
        if current_end > end_dt:
            current_end = end_dt
            
        str_start = current_start.strftime("%Y-%m-%d")
        str_end = current_end.strftime("%Y-%m-%d")
        print(f"[INFO] Fetching changes from {str_start} to {str_end}...")
        
        page = 1
        while page <= args.max_pages:
            try:
                data = tmdb_get(session, "/movie/changes", params={"start_date": str_start, "end_date": str_end, "page": page})
                results = data.get("results", [])
                if not results:
                    break
                for item in results:
                    mid = item.get("id")
                    if isinstance(mid, int):
                        changed_ids.append(mid)
                total_pages = data.get("total_pages", page)
                if page >= total_pages:
                    break
                page += 1
            except Exception as e:
                print(f"[WARN] Failed to fetch page {page} for range {str_start}-{str_end}: {e}")
                break
        
        # Move to next chunk
        current_start = current_end + timedelta(days=1)


    changed_ids = sorted(set(changed_ids))
    print(f"[INFO] Changed movie IDs: {len(changed_ids)}")

    # 2) Fetch details per ID and write normalized CSV
    # Optimized: Use ThreadPoolExecutor for concurrent fetching
    out_fields = ["tmdb_id","imdb_id","title","original_title","original_language","release_date","runtime","country_iso2","popularity","vote_average","vote_count","budget","revenue"]
    
    # Write header first
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()

    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def fetch_and_write(mid):
        try:
            # Use append_to_response=external_ids for imdb_id in one call
            detail = tmdb_get(session, f"/movie/{mid}", params={"append_to_response": "external_ids"})
            if not detail: return None
            
            ext = detail.get("external_ids") or {}
            imdb_id = ext.get("imdb_id") or detail.get("imdb_id") or ""

            rec = {
                "tmdb_id": mid,
                "imdb_id": imdb_id or "",
                "title": (detail.get("title") or "").strip(),
                "original_title": (detail.get("original_title") or "").strip(),
                "original_language": (detail.get("original_language") or "").strip()[:2].lower(),
                "release_date": (detail.get("release_date") or "").strip(),
                "runtime": detail.get("runtime") or 0,
                "country_iso2": pick_country_iso2(detail.get("production_countries") or []),
                "popularity": detail.get("popularity") or 0,
                "vote_average": detail.get("vote_average") or 0,
                "vote_count": detail.get("vote_count") or 0,
                "budget": detail.get("budget") or 0,
                "revenue": detail.get("revenue") or 0
            }
            return rec
        except Exception as e:
            # print(f"[WARN] Error fetching {mid}: {e}")
            return None

    # Max workers: 10 is usually safe for TMDB; adjust if 429 Too Many Requests occurs
    max_workers = 8 
    print(f"[INFO] Fetching details concurrently with {max_workers} threads...")
    
    processed_count = 0
    with open(outp, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_mid = {executor.submit(fetch_and_write, mid): mid for mid in changed_ids}
            
            for future in as_completed(future_to_mid):
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"[INFO] Fetching details: {processed_count}/{len(changed_ids)}", end='\r', flush=True)
                
                result = future.result()
                if result:
                    # Write immediately to save memory and progress
                    w.writerow(result)

    print(f"\n[OK] Fetched and wrote {processed_count} delta records to {outp}")

if __name__ == "__main__":
    main()
