import json
import math
import time
import requests

BASE_URL = "https://nyitottaktak.hu/api/search"
START_YEAR = 1850  # Min year per search.js
END_YEAR = 1990    # Max year per search.js

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Only basic ASCII letters needed due to accent/case insensitivity
ASCII_CHARS = [chr(i) for i in range(ord('a'), ord('z') + 1)]

def fetch_page(year: int, name_filter: str = "", page: int = 1, retries: int = 3) -> dict | None:
    """Fetch a single page following backend collation rules."""
    params = {
        "szul_tol": f"{year:04d}",
        "page": page,
        "sort": "nev",
        "dir": "asc"
    }

    # Minimum 2 characters required by API validation
    if name_filter and len(name_filter) >= 2:
        params["nev"] = name_filter.lower()

    for attempt in range(retries):
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error ({year}, nev='{name_filter}', page={page}) [Attempt {attempt + 1}/{retries}]: {e}")
            time.sleep(2 * (attempt + 1))

    return None

def save_json(data: dict, filename: str) -> None:
    """Save response payload to JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def process_search_query(year: int, prefix: str = "") -> None:
    """
    Recursively fetches all records for a year + substring filter.
    Expands the filter string dynamically when `too_many=True`.
    """
    first_page = fetch_page(year, name_filter=prefix, page=1)
    if not first_page:
        return

    # 1. If capped at 250 records, dynamically split using ASCII letters
    if first_page.get("too_many", False):
        if not prefix:
            print(f"Year {year} exceeds limit (`too_many=true`). Starting 2-letter ASCII splits...")
            for char1 in ASCII_CHARS:
                for char2 in ASCII_CHARS:
                    process_search_query(year, prefix=f"{char1}{char2}")
        else:
            print(f"Filter '{prefix}' for {year} still exceeds limit. Expanding to {len(prefix)+1} letters...")
            for char in ASCII_CHARS:
                process_search_query(year, prefix=f"{prefix}{char}")
        return

    total = first_page.get("total", 0)
    if total == 0:
        return  # Zero matches, exit immediately

    # 2. Save page 1 and paginate remaining records
    file_tag = f"{year}-{prefix}" if prefix else f"{year}"
    save_json(first_page, f"{file_tag}-1.json")

    page_size = first_page.get("page_size", 25)
    total_pages = math.ceil(total / page_size)
    print(f"[{file_tag}] Found {total} records. Downloading {total_pages} page(s)...")

    for page in range(2, total_pages + 1):
        time.sleep(0.2)
        page_data = fetch_page(year, name_filter=prefix, page=page)
        if page_data:
            save_json(page_data, f"{file_tag}-{page}.json")
        else:
            print(f"Failed to fetch {file_tag}-{page}.json")

def main():
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"\n==================== Processing Year: {year} ====================")
        process_search_query(year, prefix="")

if __name__ == "__main__":
    main()
