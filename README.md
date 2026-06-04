# Mise en Place — Weekly Meal Planner

A local-first web app for planning weekly meals, tracking calories and macros, and generating a grocery list. All data stays on your machine in a SQLite database.

## Quick start

```bash
pip install -r requirements.txt
python3 app.py
```

Open **http://localhost:5000**.

## Features

- **Recipe book** — Recipes with ingredients (grams per base serving), tags, and notes
- **Macros** — Calories, protein, carbs, and fat per serving pulled from USDA FoodData Central data
- **Weekly planner** — Assign recipes to days, adjust servings, navigate between weeks
- **Grocery list** — Ingredients summed across the whole week with macro totals
- **Automatic backups** — DB backed up on every server start and recipe save (last 10 kept in `backups/`)

## Importing USDA nutritional data

Get a free API key at https://fdc.nal.usda.gov/api-key-signup, then:

```bash
python3 import_usda.py --api-key YOUR_KEY

# For broader coverage (~8000 additional foods):
python3 import_usda.py --api-key YOUR_KEY --sr-legacy
```

---

## Architecture

### Request flow

```mermaid
sequenceDiagram
    participant B as Browser (JS)
    participant F as Flask (app.py)
    participant D as SQLite (mealplanner.db)

    B->>F: GET /api/recipes
    F->>D: SELECT recipes + ingredients
    D-->>F: rows
    F-->>B: JSON

    B->>F: POST /api/recipes
    F->>D: INSERT recipe + ingredients
    F->>D: Backup DB
    D-->>F: ok
    F-->>B: {id}

    B->>F: GET /api/grocery/:week
    F->>D: JOIN meal_plan + recipes + ingredients + ingredient_defs
    D-->>F: rows with macro data
    F-->>B: [{name, grams, calories, protein, carbs, fat}]
```

### Component overview

```mermaid
graph TD
    subgraph Browser
        UI[index.html / vanilla JS]
    end

    subgraph Flask["Flask app (app.py)"]
        R[Recipe endpoints]
        ID[Ingredient def endpoints]
        P[Plan endpoints]
        G[Grocery endpoint]
        M[Macros endpoint]
        BK[backup_db]
    end

    subgraph SQLite["SQLite (mealplanner.db)"]
        T1[recipes]
        T2[ingredients]
        T3[ingredient_defs]
        T4[meal_plan]
    end

    subgraph External
        USDA[USDA FoodData Central API]
        Script[import_usda.py]
    end

    UI -->|REST / JSON| R
    UI -->|REST / JSON| ID
    UI -->|REST / JSON| P
    UI -->|REST / JSON| G
    UI -->|REST / JSON| M

    R --> T1
    R --> T2
    ID --> T3
    P --> T4
    G --> T1
    G --> T2
    G --> T3
    G --> T4
    M --> T2
    M --> T3

    R -->|on save| BK
    BK -->|copies .db| backups[(backups/)]

    USDA -->|nutritional data| Script
    Script -->|INSERT ingredient_defs| T3
```

### Data model

```mermaid
erDiagram
    recipes {
        int id PK
        text name
        int base_servings
        text tags
        text notes
        timestamp created_at
    }
    ingredients {
        int id PK
        int recipe_id FK
        text name
        real grams_per_base_serving
        int ingredient_def_id FK
    }
    ingredient_defs {
        int id PK
        text name
        real calories_per_100g
        real protein_per_100g
        real carbs_per_100g
        real fat_per_100g
        int is_custom
    }
    meal_plan {
        int id PK
        text week_start
        int day_of_week
        text meal_slot
        int recipe_id FK
        int servings
    }

    recipes ||--o{ ingredients : has
    ingredient_defs ||--o{ ingredients : "nutritional data"
    recipes ||--o{ meal_plan : planned
```
