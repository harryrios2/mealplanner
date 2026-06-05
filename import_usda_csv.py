#!/usr/bin/env python3
"""
Import ingredient nutritional data from USDA FoodData Central CSV export.

Download the full dataset from https://fdc.nal.usda.gov/download-datasets
(select "Foundation Foods") and point this script at the extracted folder.

Usage:
    python3 import_usda_csv.py /path/to/usda/folder
    python3 import_usda_csv.py           # defaults to ../usda relative to this file
"""

import csv, os, sqlite3, sys

DB = os.path.join(os.path.dirname(__file__), 'mealplanner.db')

# Nutrient IDs in the USDA FoodData Central dataset
ENERGY_IDS  = {'1008', '2047', '2048'}   # 208, 957 (Atwater general), 958 (Atwater specific)
PROTEIN_ID  = '1003'
FAT_ID      = '1004'
CARBS_ID    = '1005'
WANT_IDS    = ENERGY_IDS | {PROTEIN_ID, FAT_ID, CARBS_ID}


def load_foundation_foods(usda_dir):
    food_csv    = os.path.join(usda_dir, 'food.csv')
    nutrient_csv = os.path.join(usda_dir, 'food_nutrient.csv')

    for path in (food_csv, nutrient_csv):
        if not os.path.exists(path):
            print(f"Error: {path} not found.")
            sys.exit(1)

    print("Reading food.csv …")
    foods = {}
    with open(food_csv, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['data_type'] == 'foundation_food':
                foods[row['fdc_id']] = row['description'].strip()
    print(f"  {len(foods)} Foundation Foods found.")

    print("Reading food_nutrient.csv …")
    nut_data = {}
    with open(nutrient_csv, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['fdc_id'] in foods and row['nutrient_id'] in WANT_IDS:
                try:
                    val = float(row['amount'] or 0)
                except ValueError:
                    val = 0.0
                nut_data.setdefault(row['fdc_id'], {})[row['nutrient_id']] = val

    # Parse each food
    parsed = {}   # name -> (calories, protein, carbs, fat)
    for fdc_id, name in foods.items():
        d = nut_data.get(fdc_id, {})
        protein = round(d.get(PROTEIN_ID, 0), 2)
        fat     = round(d.get(FAT_ID, 0), 2)
        carbs   = round(d.get(CARBS_ID, 0), 2)

        # Prefer measured energy; fall back to Atwater approximation
        cals = 0.0
        for eid in ('1008', '2047', '2048'):
            if d.get(eid, 0) > 0:
                cals = d[eid]
                break
        if cals == 0 and (protein > 0 or fat > 0 or carbs > 0):
            cals = protein * 4 + carbs * 4 + fat * 9

        cals = round(cals, 1)

        # Skip if truly no nutritional data at all
        if cals == 0 and protein == 0 and fat == 0 and carbs == 0:
            continue

        # Deduplicate: keep highest-calorie entry when same name appears
        if name not in parsed or cals > parsed[name][0]:
            parsed[name] = (cals, protein, carbs, fat)

    print(f"  {len(parsed)} foods with usable nutritional data.")
    return parsed


def main():
    if len(sys.argv) > 1:
        usda_dir = sys.argv[1]
    else:
        usda_dir = os.path.join(os.path.dirname(__file__), '..', 'usda')

    usda_dir = os.path.realpath(usda_dir)
    if not os.path.isdir(usda_dir):
        print(f"Error: directory not found: {usda_dir}")
        sys.exit(1)

    if not os.path.exists(DB):
        print(f"Error: database not found at {DB}")
        print("Start the app at least once first so the database is created.")
        sys.exit(1)

    parsed = load_foundation_foods(usda_dir)

    conn = sqlite3.connect(DB)
    deleted = conn.execute("DELETE FROM ingredient_defs WHERE is_custom = 0").rowcount
    print(f"Removed {deleted} previous built-in entries.")

    inserted = 0
    for name, (cals, protein, carbs, fat) in sorted(parsed.items()):
        try:
            conn.execute(
                '''INSERT OR IGNORE INTO ingredient_defs
                   (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, is_custom)
                   VALUES (?,?,?,?,?,0)''',
                (name, cals, protein, carbs, fat)
            )
            inserted += 1
        except Exception as e:
            print(f"  Warning: could not insert '{name}': {e}")

    conn.commit()
    conn.close()

    print(f"Imported {inserted} USDA ingredients.")
    print("Restart the app for changes to appear.")


if __name__ == '__main__':
    main()
