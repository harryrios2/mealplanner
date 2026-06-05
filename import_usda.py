#!/usr/bin/env python3
"""
Import ingredient nutritional data from USDA FoodData Central.

Get a free API key at: https://fdc.nal.usda.gov/api-key-signup

Usage:
    python3 import_usda.py --api-key YOUR_KEY
    python3 import_usda.py --api-key YOUR_KEY --sr-legacy   # also import SR Legacy (~8000 more foods)

Or set the FDC_API_KEY environment variable instead of passing --api-key.
"""

import argparse, os, sqlite3, time, sys, json
import urllib.request, urllib.parse

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
DB = os.path.join(os.path.dirname(__file__), 'mealplanner.db')

# USDA nutrient numbers
# Foundation Foods often report energy as 957/958 (Atwater factors) instead of 208
N_ENERGY  = {208, 957, 958}
N_PROTEIN = {203}
N_FAT     = {204}
N_CARBS   = {205}


def fetch_page(api_key, data_type, page, page_size=200):
    params = urllib.parse.urlencode({
        'api_key': api_key,
        'dataType': data_type,
        'pageSize': page_size,
        'pageNumber': page,
    })
    url = f"{BASE_URL}/foods/list?{params}"
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\n  HTTP {e.code}: {body[:200]}")
        raise


def fetch_all(api_key, data_type):
    foods = []
    page = 1
    while True:
        print(f"  {data_type} — page {page} ...", end=' ', flush=True)
        batch = fetch_page(api_key, data_type, page)
        if not batch:
            print("empty, done.")
            break
        print(f"{len(batch)} foods")
        foods.extend(batch)
        if len(batch) < 200:
            break
        page += 1
        time.sleep(0.25)
    return foods


def parse_macros(food):
    m = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0, 'carbs': 0.0}
    for n in food.get('foodNutrients', []):
        try:
            num = int(n.get('number', 0))
        except (TypeError, ValueError):
            continue
        val = float(n.get('amount') or 0)
        if num in N_ENERGY:
            if m['calories'] == 0:   # take first match; prefer lower number (208 < 957 < 958)
                m['calories'] = val
        elif num in N_PROTEIN:
            m['protein'] = val
        elif num in N_FAT:
            m['fat'] = val
        elif num in N_CARBS:
            m['carbs'] = val
    return m


def main():
    parser = argparse.ArgumentParser(description='Import USDA FoodData Central data into mealplanner')
    parser.add_argument('--api-key', default=os.environ.get('FDC_API_KEY'),
                        help='FDC API key (or set FDC_API_KEY env var)')
    parser.add_argument('--sr-legacy', action='store_true',
                        help='Also import SR Legacy foods (~8000 additional items, takes longer)')
    args = parser.parse_args()

    if not args.api_key:
        print("Error: API key required.")
        print("Get one free at https://fdc.nal.usda.gov/api-key-signup")
        print("Then run: python3 import_usda.py --api-key YOUR_KEY")
        sys.exit(1)

    if not os.path.exists(DB):
        print(f"Error: database not found at {DB}")
        print("Start the app at least once first so the database is created.")
        sys.exit(1)

    # Fetch
    print("Fetching Foundation Foods from USDA FoodData Central...")
    foods = fetch_all(args.api_key, 'Foundation')

    if args.sr_legacy:
        print("Fetching SR Legacy foods (this may take a minute)...")
        foods += fetch_all(args.api_key, 'SR Legacy')

    print(f"\nTotal fetched: {len(foods)}")

    # Parse — keep only foods that have at least some calorie data
    parsed = []
    for food in foods:
        name = food.get('description', '').strip()
        if not name:
            continue
        m = parse_macros(food)
        if m['calories'] == 0 and m['protein'] == 0:
            continue
        parsed.append((name, round(m['calories'], 1), round(m['protein'], 1),
                        round(m['carbs'], 1), round(m['fat'], 1)))

    print(f"Foods with usable nutritional data: {len(parsed)}")

    # Import — replace built-in seeds, keep anything the user created manually
    conn = sqlite3.connect(DB)
    deleted = conn.execute("DELETE FROM ingredient_defs WHERE is_custom = 0").rowcount
    print(f"Removed {deleted} previous built-in entries.")

    inserted = 0
    for row in parsed:
        try:
            conn.execute(
                '''INSERT OR IGNORE INTO ingredient_defs
                   (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, is_custom)
                   VALUES (?,?,?,?,?,0)''',
                row
            )
            inserted += 1
        except Exception:
            pass

    conn.commit()
    conn.close()

    print(f"Imported {inserted} USDA ingredients.")
    print("Restart the server for the changes to appear in the app.")


if __name__ == '__main__':
    main()
