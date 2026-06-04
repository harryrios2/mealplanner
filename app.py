from flask import Flask, render_template, request, jsonify
import sqlite3, os, shutil, glob
from datetime import datetime

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), 'mealplanner.db')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')

def backup_db():
    if not os.path.exists(DB):
        return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'mealplanner_{timestamp}.db')
    shutil.copy2(DB, dest)
    old_backups = sorted(glob.glob(os.path.join(BACKUP_DIR, 'mealplanner_*.db')))
    for f in old_backups[:-10]:
        os.remove(f)

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

SEED_INGREDIENTS = [
    ("Chicken breast (raw)", 165, 31, 0, 3.6),
    ("Chicken thigh (raw)", 209, 26, 0, 11),
    ("Beef mince (5% fat)", 137, 21.8, 0, 5.5),
    ("Beef mince (20% fat)", 254, 17.2, 0, 20.3),
    ("Salmon fillet", 208, 20.4, 0, 13.4),
    ("Cod fillet", 82, 17.8, 0, 0.7),
    ("Tuna (tinned in water)", 116, 26, 0, 0.9),
    ("Eggs (whole)", 147, 12.6, 0.6, 10.3),
    ("Egg white", 52, 10.9, 0.7, 0.2),
    ("Milk (whole)", 61, 3.2, 4.8, 3.3),
    ("Milk (skimmed)", 35, 3.4, 5, 0.1),
    ("Greek yoghurt (0% fat)", 59, 10.3, 3.6, 0.4),
    ("Cheddar cheese", 402, 25, 0.1, 33.1),
    ("Mozzarella", 280, 17.1, 2.7, 22.4),
    ("Butter", 717, 0.9, 0.1, 81.1),
    ("Olive oil", 884, 0, 0, 100),
    ("Rapeseed oil", 884, 0, 0, 100),
    ("White rice (dry)", 360, 6.7, 79.9, 0.7),
    ("Brown rice (dry)", 362, 7.5, 76.2, 2.7),
    ("Pasta (dry)", 371, 13, 74, 1.5),
    ("Bread (wholemeal)", 247, 12.5, 41.3, 3),
    ("Oats (rolled)", 379, 13.2, 67.7, 7.1),
    ("Potatoes", 77, 2, 17.5, 0.1),
    ("Sweet potato", 86, 1.6, 20.1, 0.1),
    ("Lentils (dry)", 352, 25.1, 60, 1.1),
    ("Chickpeas (cooked)", 164, 8.9, 27.4, 2.6),
    ("Black beans (cooked)", 132, 8.9, 23.7, 0.5),
    ("Kidney beans (cooked)", 127, 8.7, 22.8, 0.5),
    ("Tofu (firm)", 76, 8, 1.9, 4.2),
    ("Broccoli", 34, 2.8, 7, 0.4),
    ("Spinach", 23, 2.9, 3.6, 0.4),
    ("Kale", 49, 4.3, 8.8, 0.9),
    ("Onion", 40, 1.1, 9.3, 0.1),
    ("Garlic", 149, 6.4, 33.1, 0.5),
    ("Tomatoes (fresh)", 18, 0.9, 3.9, 0.2),
    ("Tomatoes (tinned)", 24, 1.2, 4.6, 0.2),
    ("Bell pepper", 31, 1, 6, 0.3),
    ("Courgette", 17, 1.2, 3.1, 0.3),
    ("Carrot", 41, 0.9, 9.6, 0.2),
    ("Mushrooms", 22, 3.1, 3.3, 0.3),
    ("Cucumber", 15, 0.7, 3.6, 0.1),
    ("Avocado", 160, 2, 9, 14.7),
    ("Banana", 89, 1.1, 22.8, 0.3),
    ("Apple", 52, 0.3, 13.8, 0.2),
    ("Blueberries", 57, 0.7, 14.5, 0.3),
    ("Lemon juice", 22, 0.4, 6.9, 0.2),
    ("Flour (plain)", 364, 10, 76.3, 1),
    ("Flour (wholemeal)", 340, 13.2, 63.9, 2.2),
    ("Sugar (white)", 387, 0, 100, 0),
    ("Honey", 304, 0.3, 82.4, 0),
    ("Coconut milk (tinned)", 197, 2, 2.8, 21.3),
    ("Soy sauce", 53, 8.1, 4.9, 0.1),
    ("Tomato paste", 82, 4.3, 18.9, 0.5),
    ("Stock (chicken, liquid)", 10, 1.5, 0.5, 0.2),
    ("Stock (vegetable, liquid)", 7, 0.5, 1.2, 0.1),
    ("Cream (double)", 453, 1.7, 2.7, 48),
    ("Cream cheese", 342, 5.9, 4.1, 34),
    ("Breadcrumbs (dry)", 395, 13, 73, 3.4),
    ("Almonds", 579, 21.2, 21.7, 49.9),
    ("Walnuts", 654, 15.2, 13.7, 65.2),
    ("Sunflower seeds", 584, 20.8, 20, 51.5),
    ("Parmesan", 431, 38.5, 0, 29.7),
]

def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                base_servings INTEGER NOT NULL DEFAULT 4,
                tags TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ingredient_defs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                calories_per_100g REAL NOT NULL DEFAULT 0,
                protein_per_100g REAL NOT NULL DEFAULT 0,
                carbs_per_100g REAL NOT NULL DEFAULT 0,
                fat_per_100g REAL NOT NULL DEFAULT 0,
                is_custom INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                grams_per_base_serving REAL NOT NULL,
                ingredient_def_id INTEGER REFERENCES ingredient_defs(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS meal_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL,
                day_of_week INTEGER NOT NULL,
                meal_slot TEXT NOT NULL DEFAULT 'dinner',
                recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
                servings INTEGER NOT NULL DEFAULT 4
            );
        ''')
        existing = {r[0] for r in db.execute('SELECT name FROM ingredient_defs').fetchall()}
        for name, cal, pro, carb, fat in SEED_INGREDIENTS:
            if name not in existing:
                db.execute(
                    'INSERT INTO ingredient_defs (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g) VALUES (?,?,?,?,?)',
                    (name, cal, pro, carb, fat)
                )
        db.commit()

def migrate_db():
    with get_db() as db:
        cols = {r[1] for r in db.execute('PRAGMA table_info(ingredients)').fetchall()}
        if 'ingredient_def_id' not in cols:
            db.execute('ALTER TABLE ingredients ADD COLUMN ingredient_def_id INTEGER REFERENCES ingredient_defs(id) ON DELETE SET NULL')
            db.commit()

init_db()
migrate_db()
backup_db()

# ── Recipes ──────────────────────────────────────────────────────────────────

@app.get('/api/recipes')
def list_recipes():
    db = get_db()
    recipes = db.execute('SELECT * FROM recipes ORDER BY name').fetchall()
    result = []
    for r in recipes:
        ingredients = db.execute(
            'SELECT * FROM ingredients WHERE recipe_id = ?', (r['id'],)
        ).fetchall()
        result.append({**dict(r), 'ingredients': [dict(i) for i in ingredients]})
    return jsonify(result)

@app.post('/api/recipes')
def create_recipe():
    data = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO recipes (name, base_servings, tags, notes) VALUES (?,?,?,?)',
        (data['name'], data.get('base_servings', 4), data.get('tags', ''), data.get('notes', ''))
    )
    recipe_id = cur.lastrowid
    for ing in data.get('ingredients', []):
        db.execute(
            'INSERT INTO ingredients (recipe_id, name, grams_per_base_serving, ingredient_def_id) VALUES (?,?,?,?)',
            (recipe_id, ing['name'], ing['grams'], ing.get('ingredient_def_id'))
        )
    db.commit()
    backup_db()
    return jsonify({'id': recipe_id}), 201

@app.put('/api/recipes/<int:rid>')
def update_recipe(rid):
    data = request.json
    db = get_db()
    db.execute(
        'UPDATE recipes SET name=?, base_servings=?, tags=?, notes=? WHERE id=?',
        (data['name'], data.get('base_servings', 4), data.get('tags', ''), data.get('notes', ''), rid)
    )
    db.execute('DELETE FROM ingredients WHERE recipe_id = ?', (rid,))
    for ing in data.get('ingredients', []):
        db.execute(
            'INSERT INTO ingredients (recipe_id, name, grams_per_base_serving, ingredient_def_id) VALUES (?,?,?,?)',
            (rid, ing['name'], ing['grams'], ing.get('ingredient_def_id'))
        )
    db.commit()
    backup_db()
    return jsonify({'ok': True})

@app.delete('/api/recipes/<int:rid>')
def delete_recipe(rid):
    db = get_db()
    db.execute('DELETE FROM recipes WHERE id = ?', (rid,))
    db.commit()
    return jsonify({'ok': True})

# ── Ingredient Definitions ────────────────────────────────────────────────────

@app.get('/api/ingredient-defs')
def list_ingredient_defs():
    db = get_db()
    rows = db.execute('SELECT * FROM ingredient_defs ORDER BY name').fetchall()
    return jsonify([dict(r) for r in rows])

@app.post('/api/ingredient-defs')
def create_ingredient_def():
    data = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO ingredient_defs (name, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, is_custom) VALUES (?,?,?,?,?,1)',
        (data['name'], data.get('calories', 0), data.get('protein', 0), data.get('carbs', 0), data.get('fat', 0))
    )
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201

@app.put('/api/ingredient-defs/<int:did>')
def update_ingredient_def(did):
    data = request.json
    db = get_db()
    db.execute(
        'UPDATE ingredient_defs SET name=?, calories_per_100g=?, protein_per_100g=?, carbs_per_100g=?, fat_per_100g=? WHERE id=?',
        (data['name'], data.get('calories', 0), data.get('protein', 0), data.get('carbs', 0), data.get('fat', 0), did)
    )
    db.commit()
    return jsonify({'ok': True})

@app.delete('/api/ingredient-defs/<int:did>')
def delete_ingredient_def(did):
    db = get_db()
    db.execute('DELETE FROM ingredient_defs WHERE id = ?', (did,))
    db.commit()
    return jsonify({'ok': True})

# ── Meal Plan ─────────────────────────────────────────────────────────────────

@app.get('/api/plan/<week_start>')
def get_plan(week_start):
    db = get_db()
    rows = db.execute(
        '''SELECT mp.*, r.name as recipe_name, r.base_servings
           FROM meal_plan mp
           JOIN recipes r ON r.id = mp.recipe_id
           WHERE mp.week_start = ?
           ORDER BY mp.day_of_week, mp.meal_slot''',
        (week_start,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])

@app.post('/api/plan')
def add_to_plan():
    data = request.json
    db = get_db()
    cur = db.execute(
        'INSERT INTO meal_plan (week_start, day_of_week, meal_slot, recipe_id, servings) VALUES (?,?,?,?,?)',
        (data['week_start'], data['day_of_week'], data.get('meal_slot', 'dinner'), data['recipe_id'], data['servings'])
    )
    db.commit()
    return jsonify({'id': cur.lastrowid}), 201

@app.put('/api/plan/<int:pid>')
def update_plan_entry(pid):
    data = request.json
    db = get_db()
    db.execute('UPDATE meal_plan SET servings=?, recipe_id=?, meal_slot=? WHERE id=?',
               (data['servings'], data['recipe_id'], data.get('meal_slot', 'dinner'), pid))
    db.commit()
    return jsonify({'ok': True})

@app.delete('/api/plan/<int:pid>')
def delete_plan_entry(pid):
    db = get_db()
    db.execute('DELETE FROM meal_plan WHERE id = ?', (pid,))
    db.commit()
    return jsonify({'ok': True})

# ── Grocery List ──────────────────────────────────────────────────────────────

@app.get('/api/grocery/<week_start>')
def get_grocery(week_start):
    db = get_db()
    rows = db.execute(
        '''SELECT i.name, i.grams_per_base_serving, mp.servings, r.base_servings,
                  d.calories_per_100g, d.protein_per_100g, d.carbs_per_100g, d.fat_per_100g
           FROM meal_plan mp
           JOIN recipes r ON r.id = mp.recipe_id
           JOIN ingredients i ON i.recipe_id = r.id
           LEFT JOIN ingredient_defs d ON d.id = i.ingredient_def_id
           WHERE mp.week_start = ?''',
        (week_start,)
    ).fetchall()

    totals = {}
    for row in rows:
        scale = row['servings'] / row['base_servings']
        grams = row['grams_per_base_serving'] * scale
        key = row['name'].strip().lower()
        if key not in totals:
            totals[key] = {'grams': 0, 'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'has_macros': False}
        totals[key]['grams'] += grams
        if row['calories_per_100g'] is not None:
            factor = grams / 100
            totals[key]['calories'] += row['calories_per_100g'] * factor
            totals[key]['protein'] += row['protein_per_100g'] * factor
            totals[key]['carbs'] += row['carbs_per_100g'] * factor
            totals[key]['fat'] += row['fat_per_100g'] * factor
            totals[key]['has_macros'] = True

    result = []
    for k, v in sorted(totals.items()):
        item = {'name': k, 'grams': round(v['grams'], 1), 'has_macros': v['has_macros']}
        if v['has_macros']:
            item['calories'] = round(v['calories'])
            item['protein'] = round(v['protein'], 1)
            item['carbs'] = round(v['carbs'], 1)
            item['fat'] = round(v['fat'], 1)
        result.append(item)
    return jsonify(result)

# ── Recipe macros ─────────────────────────────────────────────────────────────

@app.get('/api/recipes/<int:rid>/macros')
def recipe_macros(rid):
    db = get_db()
    recipe = db.execute('SELECT base_servings FROM recipes WHERE id=?', (rid,)).fetchone()
    if not recipe:
        return jsonify({}), 404
    rows = db.execute(
        '''SELECT i.grams_per_base_serving, d.calories_per_100g, d.protein_per_100g,
                  d.carbs_per_100g, d.fat_per_100g
           FROM ingredients i
           LEFT JOIN ingredient_defs d ON d.id = i.ingredient_def_id
           WHERE i.recipe_id = ? AND d.id IS NOT NULL''',
        (rid,)
    ).fetchall()
    totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
    for row in rows:
        f = row['grams_per_base_serving'] / 100
        totals['calories'] += row['calories_per_100g'] * f
        totals['protein'] += row['protein_per_100g'] * f
        totals['carbs'] += row['carbs_per_100g'] * f
        totals['fat'] += row['fat_per_100g'] * f
    per_serving = {k: round(v / recipe['base_servings'], 1) for k, v in totals.items()}
    return jsonify({'per_serving': per_serving, 'total': {k: round(v, 1) for k, v in totals.items()}})

# ── Frontend ──────────────────────────────────────────────────────────────────

@app.get('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
