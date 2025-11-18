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

def load_desserts(filepath: str = "recipes-dezerty.json") -> List[Dict]:
    """Load dessert recipes from JSON file"""
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
                raise ValueError(f"Chyba při načítání dezertů z {path}: {str(e)}")

    # Pokud soubor neexistuje, vrať prázdný seznam (dezerty jsou volitelné)
    return []

def filter_recipes(recipes: List[Dict], preferences: Dict) -> List[Dict]:
    """Filter recipes based on user preferences"""
    filtered = []

    # Mapování českých kategorií na anglické v recipes.json
    category_mapping = {
        'těstoviny': 'pasta',
        'tradiční česká': 'czech_traditional',
        'rychlá jídla': 'quick',
        'rodinná klasika': 'comfort',
        'polévky': 'soup',
        'vegetariánské': 'vegetarian',
        'veganské': 'vegan'
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

    # Mapování českého vybavení na anglické v recipes.json
    equipment_mapping = {
        'trouba': 'oven',
        'slow cooker (pomalý hrnec)': 'slow_cooker',
        'air fryer (fritéza na vzduch)': 'air_fryer',
        'mikrovlnka': 'microwave',
        'mixér/tyčový mixér': 'blender'
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

        # Check equipment - pokud recept vyžaduje speciální vybavení
        if 'equipment' in recipe and recipe['equipment']:
            user_equipment_cz = [e.lower() for e in preferences.get('equipment', [])]
            user_equipment_en = [equipment_mapping.get(eq, eq) for eq in user_equipment_cz]

            # Pokud recept potřebuje něco, co uživatel nemá, přeskoč ho
            recipe_equipment = [e.lower() for e in recipe['equipment']]
            if not all(req_eq in user_equipment_en or req_eq == 'stovetop' for req_eq in recipe_equipment):
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
            # Kontroluj jak category, tak tags (pro vegetarian/vegan)
            recipe_tags = recipe.get('tags', [])
            if recipe['category'] in user_likes_en or any(tag in user_likes_en for tag in recipe_tags):
                filtered.append(recipe)
        else:  # If no preference, include all
            filtered.append(recipe)

    return filtered

def select_weekly_recipes(filtered_recipes: List[Dict], daily_time_budgets: Dict[str, str] = None, num_weeks: int = 1) -> List[Dict[str, Dict]]:
    """Select recipes for multiple weeks with ingredient overlap optimization and anti-repeat (max 1x per 3 weeks)"""

    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    total_days = num_weeks * 7

    if len(filtered_recipes) < 7:
        # If not enough recipes, allow repeats
        selected = random.sample(filtered_recipes * 2, min(total_days, len(filtered_recipes) * 2))
        weeks = []
        for week_num in range(num_weeks):
            week_meals = {}
            for i, day in enumerate(days):
                idx = week_num * 7 + i
                if idx < len(selected):
                    week_meals[day] = selected[idx]
            weeks.append(week_meals)
        return weeks

    # OPTIMALIZACE: Vyber recepty pro všechny týdny
    # Anti-repeat: stejný recept max 1x za 3 týdny (21 dní)
    all_selected_recipes = []
    weeks = []

    for week_num in range(num_weeks):
        weekly_plan = {}
        ingredient_pool = set()  # Reset pro každý týden
        categories_used = defaultdict(int)

        for day in days:
            # Pokud máme individuální časy, filtruj podle dne
            if daily_time_budgets:
                time_range = daily_time_budgets.get(day, "20-45")
                time_min, time_max = map(int, time_range.split('-'))

                # Filtruj recepty pro tento den
                day_recipes = [r for r in filtered_recipes
                              if time_min <= r['time_minutes'] <= time_max]

                if not day_recipes:
                    day_recipes = filtered_recipes  # fallback
            else:
                day_recipes = filtered_recipes

            # Anti-repeat: vyfiltruj recepty použité v posledních 21 dnech
            recent_recipe_ids = [r['id'] for r in all_selected_recipes[-21:]]
            day_recipes_available = [r for r in day_recipes if r['id'] not in recent_recipe_ids]

            if not day_recipes_available:
                day_recipes_available = day_recipes  # fallback pokud nemáme dost receptů

            # První den týdne - vyber náhodně
            if not weekly_plan:
                first = random.choice(day_recipes_available)
                weekly_plan[day] = first
                all_selected_recipes.append(first)
                categories_used[first['category']] += 1

                # Přidej ingredience do poolu
                for ing in first['ingredients']:
                    ingredient_pool.add(ing['name'].lower().split()[0])
                continue

            # Další dny - preferuj recepty se sdílenými ingrediencemi
            scored = []
            used_ids = [r['id'] for r in weekly_plan.values()]

            for recipe in day_recipes_available:
                if recipe['id'] in used_ids:
                    continue  # Neopakuj stejný recept v rámci týdne

                # Spočítej překryv ingrediencí
                recipe_ingredients = set()
                for ing in recipe['ingredients']:
                    recipe_ingredients.add(ing['name'].lower().split()[0])

                overlap = len(recipe_ingredients & ingredient_pool)

                # Penalizace za opakování kategorie
                category_penalty = categories_used[recipe['category']] * 2

                # Skóre: overlap je pozitivní, category_penalty negativní
                score = overlap - category_penalty

                scored.append((recipe, score))

            if not scored:
                # Pokud nejsou žádné nové recepty, použij co máme
                available = [r for r in day_recipes_available if r['id'] not in used_ids]
                if available:
                    next_recipe = random.choice(available)
                else:
                    next_recipe = random.choice(day_recipes_available)
            else:
                # Seřaď podle skóre (vyšší = lepší)
                scored.sort(key=lambda x: x[1], reverse=True)

                # Vyber z top 3 kandidátů (trochu randomizace)
                top_candidates = scored[:min(3, len(scored))]
                next_recipe, _ = random.choice(top_candidates)

            weekly_plan[day] = next_recipe
            all_selected_recipes.append(next_recipe)
            categories_used[next_recipe['category']] += 1

            # Přidej nové ingredience do poolu
            for ing in next_recipe['ingredients']:
                ingredient_pool.add(ing['name'].lower().split()[0])

        # Přidej tento týden do seznamu
        weeks.append(weekly_plan)

    return weeks

def round_to_package_size(ingredient_name: str, amount_str: str) -> str:
    """Zaokrouhlit množství na reálné velikosti balení v obchodech"""
    import re

    # Extrahuj číslo a jednotku
    match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', amount_str)
    if not match:
        return amount_str  # Pokud nejde parsovat, vrať původní

    amount = float(match.group(1))
    unit = match.group(2).lower()

    # Mapování běžných velikostí balení
    package_sizes = {
        # Maso a uzeniny (g)
        'kuřecí': (400, 'g'), 'hovězí': (500, 'g'), 'vepřové': (400, 'g'),
        'šunka': (100, 'g'), 'slanina': (150, 'g'),

        # Mléčné výrobky
        'máslo': (250, 'g'), 'smetana': (200, 'ml'),
        'mléko': (1000, 'ml'), 'jogurt': (150, 'g'),
        'sýr': (200, 'g'), 'parmazán': (100, 'g'),

        # Zelenina a ovoce (přibližné)
        'brambory': (1000, 'g'), 'mrkev': (500, 'g'),
        'cibule': (500, 'g'), 'rajčata': (500, 'g'),

        # Trvanlivé
        'mouka': (1000, 'g'), 'rýže': (500, 'g'),
        'těstoviny': (500, 'g'), 'cukr': (1000, 'g'),
    }

    # Zkus najít ingredienci v mapování
    ingredient_lower = ingredient_name.lower()
    package_size = None
    package_unit = unit

    for key, (size, pkg_unit) in package_sizes.items():
        if key in ingredient_lower:
            # Konvertuj jednotky pokud nutné
            if unit == pkg_unit or (unit == 'g' and pkg_unit == 'g') or (unit == 'ml' and pkg_unit == 'ml'):
                package_size = size
                package_unit = pkg_unit
                break

    # Pokud našli package_size, zaokrouhli nahoru
    if package_size:
        packages_needed = int((amount + package_size - 1) // package_size)  # Ceiling division
        rounded = packages_needed * package_size

        if rounded > amount:
            return f"{int(amount)}{unit} → {int(rounded)}{package_unit} (balení)"
        else:
            return f"{int(rounded)}{package_unit}"

    # Pokud není v mapování, vrať původní
    if amount == int(amount):
        return f"{int(amount)}{unit}"
    else:
        return amount_str


def generate_shopping_list(weeks: List[Dict[str, Dict]], have_at_home: List[str] = None) -> Dict[str, List[str]]:
    """Aggregate ingredients from all weeks into shopping list with smart rounding and 'have at home' deduction"""
    shopping_dict = defaultdict(lambda: defaultdict(float))

    # Aggregate across all weeks
    for week in weeks:
        for day, recipe in week.items():
            for ingredient in recipe['ingredients']:
                name = ingredient['name']
                amount = ingredient['amount']
                category = ingredient['category']

                # Simple aggregation (for demo - in production, parse units properly)
                shopping_dict[category][name] = amount  # Just store, not summing for demo

    # Convert to list format grouped by category with smart quantities
    shopping_list = {}
    have_at_home_lower = [item.lower() for item in (have_at_home or [])]

    for category, items in shopping_dict.items():
        smart_items = []
        for name, amount in items.items():
            # Pokud už máme doma, přeskoč
            if any(have_item in name.lower() for have_item in have_at_home_lower):
                continue  # Není v nákupním seznamu

            rounded_amount = round_to_package_size(name, amount)
            smart_items.append(f"{name} - {rounded_amount}")

        if smart_items:  # Přidej jen pokud má items
            shopping_list[category] = smart_items

    return shopping_list

def calculate_total_cost(weeks: List[Dict[str, Dict]]) -> int:
    """Calculate total cost across all weeks"""
    total = 0
    for week in weeks:
        for recipe in week.values():
            total += recipe['price_per_portion_czk'] * recipe['servings']
    return total

def select_weekly_desserts(num_weeks: int) -> List[Dict]:
    """Select 1 random dessert for each week"""
    all_desserts = load_desserts()

    if not all_desserts:
        return []  # Pokud nejsou dezerty, vrať prázdný seznam

    # Vyber náhodně 1 dezert pro každý týden
    selected_desserts = []
    available_desserts = all_desserts.copy()

    for _ in range(num_weeks):
        if not available_desserts:
            # Pokud dojdou dezerty, obnov seznam
            available_desserts = all_desserts.copy()

        dessert = random.choice(available_desserts)
        selected_desserts.append(dessert)
        # Odstraň vybraný dezert, aby se neopakoval
        available_desserts = [d for d in available_desserts if d['id'] != dessert['id']]

    return selected_desserts

def generate_meal_plan(preferences: Dict) -> Dict:
    """Main function to generate complete meal plan for multiple weeks"""
    # Load and filter recipes
    all_recipes = load_recipes()
    filtered = filter_recipes(all_recipes, preferences)

    if not filtered:
        raise ValueError("No recipes match your preferences. Please adjust your criteria.")

    # Select recipes for multiple weeks
    num_weeks = preferences.get('num_weeks', 1)
    daily_time_budgets = preferences.get('daily_time_budgets')
    have_at_home = preferences.get('have_at_home', [])

    weeks = select_weekly_recipes(filtered, daily_time_budgets, num_weeks)

    # Select 1 dessert for each week
    weekly_desserts = select_weekly_desserts(num_weeks)

    # Add desserts to shopping list by creating temporary weeks structure
    # Přidáme dezerty do nákupního seznamu
    weeks_with_desserts = []
    for i, week in enumerate(weeks):
        week_copy = week.copy()
        if i < len(weekly_desserts) and weekly_desserts[i]:
            # Přidáme dezert jako "sunday_dessert" do týdne
            week_copy['sunday_dessert'] = weekly_desserts[i]
        weeks_with_desserts.append(week_copy)

    # Generate shopping list (for all weeks including desserts, minus "mám doma")
    shopping_list = generate_shopping_list(weeks_with_desserts, have_at_home)

    # Calculate costs (včetně dezertů)
    total_cost = calculate_total_cost(weeks_with_desserts)
    total_portions = sum(sum(r['servings'] for r in week.values()) for week in weeks_with_desserts)

    # Spočítej překryv ingrediencí (pro statistiku úspor) - across all weeks including desserts
    all_ingredients = set()
    unique_count = 0
    for week in weeks_with_desserts:
        for recipe in week.values():
            for ing in recipe['ingredients']:
                ing_base = ing['name'].lower().split()[0]
                if ing_base not in all_ingredients:
                    unique_count += 1
                    all_ingredients.add(ing_base)

    total_ingredient_uses = sum(sum(len(r['ingredients']) for r in week.values()) for week in weeks_with_desserts)
    reuse_count = total_ingredient_uses - unique_count
    reuse_percentage = round((reuse_count / total_ingredient_uses) * 100) if total_ingredient_uses > 0 else 0

    return {
        "week_of": "2024-11-18",
        "preferences": preferences,
        "weeks": weeks_with_desserts,  # List[Dict[str, Dict]] - včetně dezertů
        "meals": weeks_with_desserts[0] if weeks_with_desserts else {},  # První týden pro zpětnou kompatibilitu
        "num_weeks": num_weeks,
        "weekly_desserts": weekly_desserts,  # Samostatný seznam dezertů pro zobrazení
        "shopping_list": shopping_list,
        "total_cost_czk": total_cost,
        "cost_per_portion_czk": round(total_cost / total_portions, 1) if total_portions > 0 else 0,
        "ingredient_stats": {
            "total_uses": total_ingredient_uses,
            "unique_ingredients": unique_count,
            "reused_count": reuse_count,
            "reuse_percentage": reuse_percentage
        }
    }
