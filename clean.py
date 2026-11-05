import glob
import json
import os
import re

# Directory containing your raw JSON files
RAW_DIR = "."
# Directory where cleaned yearly files will be saved
OUTPUT_DIR = "./cleaned"

def load_and_merge_year(year: int) -> list[dict]:
    """Finds all raw JSON files for a given year, extracts and deduplicates results by 'guid'."""
    # Matches filenames like '1920-1.json', '1920-sz-1.json', etc.
    pattern = os.path.join(RAW_DIR, f"{year}*.json")
    matching_files = glob.glob(pattern)

    # Filter out any files from previous clean runs if they happen to be in the same folder
    matching_files = [f for f in matching_files if not os.path.basename(f).startswith("clean_")]

    if not matching_files:
        return []

    unique_records: dict[str, dict] = {}

    for file_path in matching_files:
        # Validate that the file belongs to this year (e.g., 1920, not 1920s or 192)
        filename = os.path.basename(file_path)
        if not re.match(rf"^{year}(-\w+)*-\d+\.json$", filename):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            results = data.get("results", [])
            for item in results:
                guid = item.get("guid")
                if guid and guid not in unique_records:
                    unique_records[guid] = item
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading {file_path}: {e}")

    # Convert dict back to list and sort alphabetically by name ('nev')
    deduped_results = list(unique_records.values())
    deduped_results.sort(key=lambda x: x.get("nev", ""))

    return deduped_results

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Discover all years present in the raw directory filenames
    raw_files = glob.glob(os.path.join(RAW_DIR, "*.json"))
    detected_years = set()

    for file_path in raw_files:
        filename = os.path.basename(file_path)
        match = re.match(r"^(\d{4})(-\w+)*-\d+\.json$", filename)
        if match:
            detected_years.add(int(match.group(1)))

    sorted_years = sorted(detected_years)
    print(f"Found raw records spanning {len(sorted_years)} years.")

    for year in sorted_years:
        cleaned_records = load_and_merge_year(year)
        if not cleaned_records:
            continue

        output_filename = os.path.join(OUTPUT_DIR, f"clean_{year}.json")
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(cleaned_records, f, ensure_ascii=False, indent=2)

        print(f"Saved {output_filename} with {len(cleaned_records)} unique record(s).")

if __name__ == "__main__":
    main()
