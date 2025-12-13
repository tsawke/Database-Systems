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

    # 1) Fetch changed IDs (paginated)
    changed_ids: List[int] = []
    page = 1
    while page <= args.max_pages:
        data = tmdb_get(session, "/movie/changes", params={"start_date": args.start_date, "end_date": args.end_date, "page": page})
        results = data.get("results", [])
        if not results:
            break
        for item in results:
            mid = item.get("id")
            if isinstance(mid, int):
                changed_ids.append(mid)
        total_pages = data.get("total_pages", page)
        page += 1
        if page > total_pages:
            break

    changed_ids = sorted(set(changed_ids))
    print(f"[INFO] Changed movie IDs: {len(changed_ids)}")

    # 2) Fetch details per ID and write normalized CSV
    out_fields = ["tmdb_id","imdb_id","title","original_title","original_language","release_date","runtime","country_iso2","popularity","vote_average","vote_count","budget","revenue"]
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()

        for i, mid in enumerate(changed_ids, 1):
            try:
                # Use append_to_response=external_ids for imdb_id in one call (if supported by your TMDb plan)
                detail = tmdb_get(session, f"/movie/{mid}", params={"append_to_response": "external_ids"})
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
                    "country_iso2": pick_country_iso2(detail.get("production_countries")),
                    "popularity": detail.get("popularity"),
                    "vote_average": detail.get("vote_average"),
                    "vote_count": detail.get("vote_count") or 0,
                    "budget": detail.get("budget") or 0,
                    "revenue": detail.get("revenue") or 0,
                }
                w.writerow(rec)
            except Exception as e:
                # Best-effort: skip failed IDs but keep pipeline running; in a real system you would log this
                continue

            if args.sleep > 0:
                time.sleep(args.sleep)

    print(f"[OK] TMDb delta normalized CSV written to: {outp}")

if __name__ == "__main__":
    main()
