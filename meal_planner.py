"""
Core meal planning logic
"""

import json
import random
from typing import Dict, List
from collections import defaultdict

def load_recipes(filepath: str = "recipes.json") -> List[Dict]:
    """Load recipes from JSON file"""
    import os

    # Try multiple possible paths
    possible_paths = [
        filepath,
        os.path.join(os.path.dirname(__file__), filepath),
        os.path.abspath(filepath)
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data['recipes']
            except json.JSONDecodeError as e:
                raise ValueError(f"Chyba při načítání receptů z {path}: {str(e)}")

    raise FileNotFoundError(f"Soubor recipes.json nebyl nalezen. Zkontroluj cestu: {possible_paths}")

def filter_recipes(recipes: List[Dict], preferences: Dict) -> List[Dict]:
    """Filter recipes based on user preferences"""
    filtered = []

    # Mapování českých kategorií na anglické v recipes.json
    category_mapping = {
        'těstoviny': 'pasta',
        'tradiční česká': 'czech_traditional',
        'rychlá jídla': 'quick',
        'rodinná klasika': 'comfort'
    }

    # Mapování českých alergenů na anglické v recipes.json
    # Podporuje i varianty s popisem v závorkách
    allergen_mapping = {
        'lepek': 'gluten',
        'korýši': 'shellfish',
        'vejce': 'eggs',
        'ryby': 'fish',
        'arašídy': 'peanuts',
        'sója': 'soy',
        'mléko': 'dairy',
        'mléko a mléčné výrobky': 'dairy',
        'ořechy': 'nuts',
        'celer': 'celery',
        'hořčice': 'mustard',
        'sezam': 'sesame',
        'oxid siřičitý': 'sulfites',
        'vlčí bob': 'lupin',
        'měkkýši': 'molluscs'
    }

    # Mapování českých omezení na varianty v receptech - rozšířené
    dislike_mapping = {
        'vepřové': ['vepř', 'bůček', 'kýta', 'plec', 'krkovice', 'žebírk', 'slanina'],
        'hovězí': ['hovězí', 'hovädzí', 'svíčkov', 'roštěnec', 'guláš'],
        'kuřecí': ['kuřec', 'kuře', 'kur', 'drůbež'],
        'ryby': ['ryb', 'kapr', 'pstruh', 'losos', 'sleď', 'treska', 'makrela'],
        'mořské plody': ['krevet', 'mořsk', 'kalamár', 'chobotnic', 'slávk', 'humr'],
        'vnitřnosti': ['játr', 'vnitřnos', 'dršť', 'ledvin', 'srdce', 'jazyk'],
        'houby': ['houb', 'žampion', 'hřib', 'bedl', 'liška', 'hlív'],
        'cibule': ['cibul', 'cibulk'],
        'česnek': ['česnek', 'česnekový'],
        'paprika': ['paprik'],
        'rajčata': ['rajč', 'paradajk', 'pomidor'],
        'brokolice': ['brokolic'],
        'květák': ['květák'],
        'fazole': ['fazol'],
        'čočka': ['čočk', 'čočkový'],
        'sýr': ['sýr', 'syr', 'parmazán', 'eidam', 'mozzarella'],
        'smetana': ['smetan', 'smetanový'],
        'koření (pikantní)': ['peprn', 'pálivý', 'pikant', 'chilli', 'jalapeño']
    }

    for recipe in recipes:
        # Check time budget
        time_min, time_max = map(int, preferences['time_budget'].split('-'))
        if not (time_min <= recipe['time_minutes'] <= time_max):
            continue

        # Check kid-friendly requirement
        if preferences.get('kid_friendly_required') and not recipe['kid_friendly']:
            continue

        # Check dislikes (ingredients) - vše česky
        dislikes = [d.lower() for d in preferences.get('dislikes', [])]

        # Rozšíř české dislikes na všechny varianty
        dislikes_expanded = []
        for dislike in dislikes:
            if dislike in dislike_mapping:
                dislikes_expanded.extend(dislike_mapping[dislike])
            else:
                dislikes_expanded.append(dislike)

        # Check v názvu receptu
        recipe_name_lower = recipe['name'].lower()
        if any(dislike in recipe_name_lower for dislike in dislikes_expanded):
            continue

        # Check v ingrediencích
        recipe_ingredients = ' '.join([ing['name'].lower() for ing in recipe['ingredients']])
        if any(dislike in recipe_ingredients for dislike in dislikes_expanded):
            continue

        # Check allergens - převeď české na anglické
        user_allergens_cz = [a.lower() for a in preferences.get('allergies', [])]

        # Extrahuj klíčové slovo před závorkou (např. "Lepek (pšenice)" → "lepek")
        user_allergens_keys = []
        for allergen in user_allergens_cz:
            # Pokud obsahuje závorku, vezmi část před závorkou
            if '(' in allergen:
                key = allergen.split('(')[0].strip()
            else:
                key = allergen.strip()
            user_allergens_keys.append(key)

        # Převeď na anglické varianty
        user_allergens_en = [allergen_mapping.get(key, key) for key in user_allergens_keys]
        recipe_allergens = [a.lower() for a in recipe['allergens']]
        if any(allergen in recipe_allergens for allergen in user_allergens_en):
            continue

        # Check category preference - převeď české na anglické
        user_likes_cz = [l.lower() for l in preferences.get('likes', [])]
        user_likes_en = [category_mapping.get(l, l) for l in user_likes_cz]

        if user_likes_en:
            if recipe['category'] in user_likes_en:
                filtered.append(recipe)
        else:  # If no preference, include all
            filtered.append(recipe)

    return filtered

def select_weekly_recipes(filtered_recipes: List[Dict]) -> Dict[str, Dict]:
    """Select 7 recipes for the week with variety"""
    if len(filtered_recipes) < 7:
        # If not enough recipes, allow repeats
        selected = random.sample(filtered_recipes * 2, 7)
    else:
        # Ensure variety - try to avoid same category multiple times
        selected = []
        remaining = filtered_recipes.copy()
        categories_used = defaultdict(int)

        for _ in range(7):
            # Sort by how many times category was used (prefer less used)
            remaining.sort(key=lambda r: categories_used[r['category']])

            # Pick from top candidates
            recipe = random.choice(remaining[:min(3, len(remaining))])
            selected.append(recipe)
            categories_used[recipe['category']] += 1
            remaining.remove(recipe)

            if not remaining:
                remaining = filtered_recipes.copy()

    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return {day: recipe for day, recipe in zip(days, selected)}

def generate_shopping_list(weekly_recipes: Dict[str, Dict]) -> Dict[str, List[str]]:
    """Aggregate ingredients from all recipes into shopping list"""
    shopping_dict = defaultdict(lambda: defaultdict(float))

    for day, recipe in weekly_recipes.items():
        for ingredient in recipe['ingredients']:
            name = ingredient['name']
            amount = ingredient['amount']
            category = ingredient['category']

            # Simple aggregation (for demo - in production, parse units properly)
            shopping_dict[category][name] = amount  # Just store, not summing for demo

    # Convert to list format grouped by category
    shopping_list = {}
    for category, items in shopping_dict.items():
        shopping_list[category] = [f"{name} - {amount}" for name, amount in items.items()]

    return shopping_list

def calculate_total_cost(weekly_recipes: Dict[str, Dict]) -> int:
    """Calculate total weekly cost"""
    total = sum(recipe['price_per_portion_czk'] * recipe['servings']
                for recipe in weekly_recipes.values())
    return total

def generate_meal_plan(preferences: Dict) -> Dict:
    """Main function to generate complete meal plan"""
    # Load and filter recipes
    all_recipes = load_recipes()
    filtered = filter_recipes(all_recipes, preferences)

    if not filtered:
        raise ValueError("No recipes match your preferences. Please adjust your criteria.")

    # Select 7 recipes
    weekly_recipes = select_weekly_recipes(filtered)

    # Generate shopping list
    shopping_list = generate_shopping_list(weekly_recipes)

    # Calculate costs
    total_cost = calculate_total_cost(weekly_recipes)
    total_portions = sum(r['servings'] for r in weekly_recipes.values())

    return {
        "week_of": "2024-11-18",
        "preferences": preferences,
        "meals": weekly_recipes,
        "shopping_list": shopping_list,
        "total_cost_czk": total_cost,
        "cost_per_portion_czk": round(total_cost / total_portions, 1)
    }
