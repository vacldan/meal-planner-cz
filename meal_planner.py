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

    for recipe in recipes:
        # Check time budget
        time_min, time_max = map(int, preferences['time_budget'].split('-'))
        if not (time_min <= recipe['time_minutes'] <= time_max):
            continue

        # Check kid-friendly requirement
        if preferences.get('kid_friendly_required') and not recipe['kid_friendly']:
            continue

        # Check dislikes (ingredients)
        dislikes = [d.lower() for d in preferences.get('dislikes', [])]
        if any(dislike in recipe['name'].lower() for dislike in dislikes):
            continue

        # Check if any ingredient contains disliked items
        recipe_ingredients = ' '.join([ing['name'].lower() for ing in recipe['ingredients']])
        if any(dislike in recipe_ingredients for dislike in dislikes):
            continue

        # Check allergens
        user_allergens = [a.lower() for a in preferences.get('allergies', [])]
        recipe_allergens = [a.lower() for a in recipe['allergens']]
        if any(allergen in recipe_allergens for allergen in user_allergens):
            continue

        # Check category preference
        if recipe['category'] in preferences.get('likes', []):
            filtered.append(recipe)
        elif not preferences.get('likes'):  # If no preference, include all
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
