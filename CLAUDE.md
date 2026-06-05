# Claude Chef Guide

How to add recipes to Mise en Place via the backend API.

## Running the app

```bash
cd /home/harry/projects/mealplanner
python3 app.py                                      # runs on http://localhost:5000

# Claude Chef tab requires an Anthropic API key:
ANTHROPIC_API_KEY=your-key python3 app.py
```

---

## Recipe creation workflow

### 1. Check what ingredients exist

```python
import urllib.request, json

res = urllib.request.urlopen('http://localhost:5000/api/ingredient-defs')
defs = json.loads(res.read())

# Search by keyword
term = 'salmon'
matches = [d for d in defs if term.lower() in d['name'].lower()]
for d in matches:
    print(f"[{d['id']}] {d['name']}: {d['calories_per_100g']} kcal/100g")
```

### 2. Create any missing ingredients

Only needed when the ingredient is not in the USDA dataset. All values are **per 100 g**.

```python
def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        'http://localhost:5000' + path, data=body,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

oyster_sauce = post('/api/ingredient-defs', {
    'name': 'Oyster sauce',
    'calories': 92,    # kcal per 100g
    'protein': 3.7,
    'carbs': 10.5,
    'fat': 0.5,
})
# returns {'id': <new_id>}
```

Common custom ingredients worth creating: oyster sauce, sesame oil, fish sauce, miso paste,
rice vinegar, coconut aminos, harissa, tahini, gochujang.

### 3. Create the recipe

All ingredient quantities are **grams per single serving** (base_servings is always 1).
The planner's servings picker scales everything up when meal planning.

```python
recipe = post('/api/recipes', {
    'name': 'Tomato-Egg with Rice',
    'tags': 'Chinese, quick',           # comma-separated; used for filtering
    'notes': 'Optional cooking notes.',
    'ingredients': [
        {'name': 'Egg, whole, raw, frozen, pasteurized', 'grams': 100, 'ingredient_def_id': 608},
        {'name': 'Tomato, roma',                         'grams': 150, 'ingredient_def_id': 818},
        {'name': 'White rice (dry)',                     'grams':  80, 'ingredient_def_id': 853},
        {'name': 'Oyster sauce',                         'grams':  18, 'ingredient_def_id': oyster_sauce['id']},
        {'name': 'Rapeseed oil',                         'grams':  10, 'ingredient_def_id': 852},
    ]
})
print('Recipe id:', recipe['id'])
```

`ingredient_def_id` links the ingredient to nutritional data for the macro pills.
If an ingredient has no matching def, omit `ingredient_def_id` — it still appears in the
grocery list but won't contribute to calorie counts.

### 4. Verify macros

```python
res = urllib.request.urlopen(f'http://localhost:5000/api/recipes/{recipe["id"]}/macros')
print(json.loads(res.read())['per_serving'])
# {'calories': 576.0, 'protein': 19.4, 'carbs': 72.5, 'fat': 21.6}
```

---

## Key ingredient IDs (frequently used)

| ID  | Name                                    | kcal/100g |
|-----|-----------------------------------------|-----------|
| 608 | Egg, whole, raw, frozen, pasteurized    | 150       |
| 623 | Fish, salmon, Atlantic, farm raised     | 197       |
| 534 | Beef, top sirloin steak, raw            | 140       |
| 818 | Tomato, roma                            | 22        |
| 727 | Onions, red, raw                        | 44        |
| 868 | Onion                                   | 40        |
| 552 | Cabbage, bok choy, raw                  | 20        |
| 658 | Garlic, raw                             | 143       |
| 665 | Green onion (scallion)                  | 3         |
| 764 | Potatoes, gold, without skin, raw       | 74        |
| 853 | White rice (dry)                        | 360       |
| 854 | Brown rice (dry)                        | 362       |
| 851 | Olive oil                               | 884       |
| 852 | Rapeseed oil                            | 884       |
| 887 | Soy sauce                               | 53        |
| 888 | Tomato paste                            | 82        |
| 898 | Oyster sauce (custom)                   | 92        |
| 900 | Vinegar, red wine (custom)              | 19        |
| 901 | Sesame oil (custom)                     | 884       |
| 902 | Ginger, fresh (custom)                  | 80        |

> Custom ingredient IDs (898+) were created manually and will vary between databases.
> Always search first with step 1 to confirm IDs before using them.

---

## Typical gram quantities per serving

| Ingredient type         | Typical range |
|-------------------------|---------------|
| Protein (meat/fish)     | 150–250g      |
| Dry rice or pasta       | 70–90g        |
| Vegetables              | 80–200g       |
| Cooking oil             | 8–15g         |
| Soy / oyster sauce      | 10–20g        |
| Aromatics (garlic etc.) | 5–10g         |
| 1 tablespoon (liquid)   | ~15g          |
| 1 tablespoon (paste)    | ~18g          |
| 1 teaspoon              | ~5g           |

---

## Sanity-check calorie targets

| Meal type                  | Expected kcal / serving |
|----------------------------|-------------------------|
| Light bowl (salad/veg)     | 300–450                 |
| Standard meal (rice+protein) | 500–700               |
| High-protein / bulking     | 700–900                 |
| Snack or side              | 150–300                 |

If the calculated value looks way off, check that:
- Grams are reasonable (rice 80g, not 800g)
- Oil/fat quantity isn't too large (10–15g typical)
- The `ingredient_def_id` is actually linked (run step 4 to verify)

---

## Updating the USDA ingredient database

The app ships with USDA Foundation Foods data. To refresh from the full CSV export:

```bash
python3 import_usda_csv.py /path/to/usda/folder
# default path: ../usda relative to this file
python3 import_usda_csv.py
```

Download the latest CSV from https://fdc.nal.usda.gov/download-datasets (Foundation Foods).
