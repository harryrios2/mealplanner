# Mise en Place — Weekly Meal Planner

A local web app for planning weekly meals and generating a grocery list.
All data is stored in a SQLite database (`mealplanner.db`) on your machine.

## Setup

```bash
cd mealplanner
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser.

## How it works

1. **Recipe book** — Create recipes with a name, base serving count, and a list of ingredients (all in grams per base serving). Add tags to organise by cuisine or diet.

2. **This week** — Pick any recipes from your library for each day. Adjust servings up or down per meal. Navigate between weeks with the arrows.

3. **Grocery list** — Generated automatically from your week's plan. Ingredients used across multiple recipes are summed together. Check off items as you shop. Copy the list as plain text to share or paste elsewhere.

## Data

The SQLite database is created automatically as `mealplanner.db` in the app folder on first run.

## Adding macros / nutrition later

The schema is ready for this. You can add `calories_per_g`, `protein_per_g`, `carbs_per_g`, `fat_per_g` columns to the `ingredients` table and display totals per meal or per week.
