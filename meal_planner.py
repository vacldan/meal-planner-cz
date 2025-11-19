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
        'sezónní jídla': 'seasonal',
        'vegetariánské': 'vegetarian',
        'veganské': 'vegan',
        # 'jídla pro děti' není kategorie - filtruje se přes kid_friendly flag
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

        # Check price budget
        if 'price_budget' in preferences:
            price_min, price_max = map(int, preferences['price_budget'].split('-'))
            if not (price_min <= recipe['price_per_portion_czk'] <= price_max):
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

        # Odfiltruj "jídla pro děti" - to se kontroluje přes kid_friendly flag, ne kategorii
        user_likes_cz_filtered = [l for l in user_likes_cz if l != 'jídla pro děti']
        user_likes_en = [category_mapping.get(l, l) for l in user_likes_cz_filtered]

        if user_likes_en:
            # Kontroluj jak category, tak tags (pro vegetarian/vegan)
            recipe_tags = recipe.get('tags', [])
            if recipe['category'] in user_likes_en or any(tag in user_likes_en for tag in recipe_tags):
                filtered.append(recipe)
        else:  # If no preference (nebo jen "Jídla pro děti"), include all
            filtered.append(recipe)

    return filtered

def get_main_protein(recipe: Dict) -> str:
    """Detekuje hlavní bílkovinu/typ jídla z receptu"""
    # Zkontroluj název a ingredience
    recipe_text = (recipe['name'] + ' ' + ' '.join([ing['name'] for ing in recipe['ingredients']])).lower()

    # Definuj priority - první match vyhrává
    protein_keywords = {
        'chicken': ['kuřec', 'kuře', 'kur', 'drůbež'],
        'pork': ['vepř', 'bůček', 'kýta', 'plec', 'krkovice', 'žebírk', 'slanina', 'uzené'],
        'beef': ['hovězí', 'hovädzí', 'svíčkov', 'roštěnec'],
        'fish': ['ryb', 'kapr', 'pstruh', 'losos', 'sleď', 'treska', 'makrela', 'tuňák'],
        'seafood': ['krevet', 'mořsk', 'kalamár', 'chobotnic'],
        'vegan': ['vegan', 'fazol', 'čočk', 'cizrn'],
        'vegetarian': ['vegetariánsk', 'sýr', 'smažený sýr', 'bramboráky', 'vaječn']
    }

    # Zkontroluj tags
    tags = recipe.get('tags', [])
    if 'vegan' in tags:
        return 'vegan'
    if 'vegetarian' in tags or 'vegetariánské' in tags:
        return 'vegetarian'

    # Hledej podle klíčových slov
    for protein, keywords in protein_keywords.items():
        if any(keyword in recipe_text for keyword in keywords):
            return protein

    return 'other'

def select_weekly_recipes(filtered_recipes: List[Dict], daily_time_budgets: Dict[str, str] = None, num_weeks: int = 1) -> List[Dict[str, Dict]]:
    """Select recipes for multiple weeks with weighted ingredient overlap optimization, anti-repeat, and protein diversity (max 3x same protein per week)"""

    # Váhy pro weighted overlap optimization
    INGREDIENT_WEIGHTS = {
        'maso': 3.0,      # Nejdražší - nejvíce váhy
        'ryby': 3.0,
        'zelenina': 2.0,
        'vegetables': 2.0,
        'mléčné': 2.0,
        'dairy': 2.0,
        'trvanlivé': 1.0,
        'pantry': 1.0,
        'ostatní': 0.5
    }

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
        ingredient_pool = {}  # {ing_name: category} - pro vážený overlap
        categories_used = defaultdict(int)
        protein_counts = defaultdict(int)  # Sleduj hlavní ingredience v týdnu

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

                # Sleduj hlavní protein
                main_protein = get_main_protein(first)
                protein_counts[main_protein] += 1

                # Přidej ingredience do poolu s jejich kategoriemi
                for ing in first['ingredients']:
                    ing_name = ing['name'].lower().split()[0]
                    ing_category = ing.get('category', 'ostatní').lower()
                    ingredient_pool[ing_name] = ing_category
                continue

            # Další dny - preferuj recepty se sdílenými ingrediencemi (WEIGHTED OVERLAP)
            scored = []
            used_ids = [r['id'] for r in weekly_plan.values()]

            for recipe in day_recipes_available:
                if recipe['id'] in used_ids:
                    continue  # Neopakuj stejný recept v rámci týdne

                # Zkontroluj hlavní protein - HARD LIMIT: max 3x týdně
                recipe_protein = get_main_protein(recipe)
                if protein_counts[recipe_protein] >= 3:
                    continue  # Přeskoč, už je 3x tento protein

                # Spočítej VÁŽENÝ překryv ingrediencí
                weighted_overlap = 0.0
                recipe_ingredients = {}  # {name: category}

                for ing in recipe['ingredients']:
                    ing_name = ing['name'].lower().split()[0]
                    ing_category = ing.get('category', 'ostatní').lower()
                    recipe_ingredients[ing_name] = ing_category

                    # Pokud je ingredience už v poolu, přičti váhu
                    if ing_name in ingredient_pool:
                        weight = INGREDIENT_WEIGHTS.get(ing_category, 0.5)
                        weighted_overlap += weight

                # Penalizace za opakování kategorie
                category_penalty = categories_used[recipe['category']] * 2

                # Penalizace za opakování proteinu (soft penalty)
                protein_penalty = protein_counts[recipe_protein] * 5

                # Skóre: weighted overlap je pozitivní, penalty negativní
                score = weighted_overlap - category_penalty - protein_penalty

                scored.append((recipe, score))

            if not scored:
                # Pokud nejsou žádné nové recepty, použij co máme (bez protein limitu)
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

            # Sleduj hlavní protein
            main_protein = get_main_protein(next_recipe)
            protein_counts[main_protein] += 1

            # Přidej nové ingredience do poolu s jejich kategoriemi
            for ing in next_recipe['ingredients']:
                ing_name = ing['name'].lower().split()[0]
                ing_category = ing.get('category', 'ostatní').lower()
                ingredient_pool[ing_name] = ing_category

        # Přidej tento týden do seznamu
        weeks.append(weekly_plan)

    return weeks

def parse_amount(amount_str: str):
    """Extrahuje číslo a jednotku z textu množství"""
    import re

    # Podporuje formáty: "500g", "500 g", "1.5 kg", "2 ks"
    match = re.match(r'(\d+(?:[.,]\d+)?)\s*(\w+)', str(amount_str))
    if not match:
        return None, None

    amount = float(match.group(1).replace(',', '.'))
    unit = match.group(2).lower()

    return amount, unit

def round_to_package_size(ingredient_name: str, amount_str: str) -> dict:
    """
    Zaokrouhlit množství na reálné velikosti balení v českých obchodech.

    Returns:
        dict: {
            'original_amount': str,
            'rounded_amount': str,
            'leftover': str (optional),
            'packages_needed': int,
            'tip': str (optional)
        }
    """

    # Rozšířené PACKAGE_SIZES - reálné velikosti z Kaufland, Tesco, Albert, Billa
    PACKAGE_SIZES = {
        # Maso a drůbež
        'kuřecí prsa': (400, 'g'),
        'kuřecí stehna': (600, 'g'),
        'kuřecí': (500, 'g'),
        'hovězí maso': (500, 'g'),
        'hovězí': (500, 'g'),
        'vepřové': (400, 'g'),
        'vepřová': (400, 'g'),
        'krkovice': (500, 'g'),
        'uzené': (300, 'g'),
        'slanina': (150, 'g'),
        'klobása': (250, 'g'),
        'párky': (300, 'g'),

        # Ryby
        'losos': (250, 'g'),
        'treska': (400, 'g'),
        'kapr': (1000, 'g'),

        # Mléčné výrobky
        'máslo': (250, 'g'),
        'smetana': (200, 'ml'),
        'zakysaná smetana': (200, 'ml'),
        'mléko': (1000, 'ml'),
        'jogurt': (150, 'g'),
        'sýr': (200, 'g'),
        'eidam': (250, 'g'),
        'parmazán': (100, 'g'),
        'mozzarella': (125, 'g'),
        'tvaroh': (250, 'g'),
        'čedar': (200, 'g'),

        # Zelenina (typické váhy/balení)
        'brambory': (1000, 'g'),
        'mrkev': (500, 'g'),
        'cibule': (500, 'g'),
        'rajčata': (500, 'g'),
        'paprika': (500, 'g'),
        'česnek': (50, 'g'),
        'cuketa': (500, 'g'),
        'brokolice': (400, 'g'),
        'květák': (600, 'g'),
        'zelí': (1000, 'g'),
        'pórek': (300, 'g'),
        'houby': (250, 'g'),
        'žampiony': (250, 'g'),

        # Trvanlivé
        'mouka': (1000, 'g'),
        'rýže': (500, 'g'),
        'těstoviny': (500, 'g'),
        'špagety': (500, 'g'),
        'cukr': (1000, 'g'),
        'sůl': (500, 'g'),
        'olej': (1000, 'ml'),
        'ocet': (500, 'ml'),
        'rajčatový protlak': (500, 'g'),
        'rajčata konzervovaná': (400, 'g'),
        'fazole': (400, 'g'),
        'čočka': (500, 'g'),
        'hladká mouka': (1000, 'g'),
        'polohrubá mouka': (1000, 'g'),

        # Koření a dochucovadla (častá balení)
        'pepř': (50, 'g'),
        'paprika': (50, 'g'),
        'kmín': (30, 'g'),
        'muškátový oříšek': (20, 'g'),
    }

    amount, unit = parse_amount(amount_str)
    if not amount or not unit:
        return {
            'original_amount': amount_str,
            'rounded_amount': amount_str,
            'packages_needed': 1
        }

    # Zkus najít ingredienci v mapování
    ingredient_lower = ingredient_name.lower()
    package_size = None
    package_unit = unit

    for key, (size, pkg_unit) in PACKAGE_SIZES.items():
        if key in ingredient_lower:
            # Konvertuj jednotky pokud nutné (g/kg, ml/l)
            if unit == pkg_unit:
                package_size = size
                package_unit = pkg_unit
                break
            elif unit == 'kg' and pkg_unit == 'g':
                amount = amount * 1000
                unit = 'g'
                package_size = size
                package_unit = pkg_unit
                break
            elif unit == 'l' and pkg_unit == 'ml':
                amount = amount * 1000
                unit = 'ml'
                package_size = size
                package_unit = pkg_unit
                break

    # Pokud není v mapování, vrať původní
    if not package_size:
        return {
            'original_amount': amount_str,
            'rounded_amount': f"{int(amount) if amount == int(amount) else amount}{unit}",
            'packages_needed': 1
        }

    # Zaokrouhli nahoru na celé balení
    packages_needed = int((amount + package_size - 1) // package_size)
    rounded = packages_needed * package_size
    leftover = rounded - amount

    result = {
        'original_amount': f"{int(amount) if amount == int(amount) else amount}{unit}",
        'rounded_amount': f"{int(rounded)}{package_unit}",
        'packages_needed': packages_needed
    }

    # Přidej info o zbytku, pokud je > 20% balení
    if leftover > 0 and leftover / package_size > 0.2:
        result['leftover'] = f"{int(leftover)}{package_unit}"

        # Tipy na využití zbytků
        tips = {
            'máslo': 'Zbytek využij na pečení nebo vaření.',
            'smetana': 'Použij do kávy nebo na přípravu omáček.',
            'sýr': 'Nastrouhaný sýr vydrží v lednici 2 týdny.',
            'těstoviny': 'Suché těstoviny vydrží rok v suchém prostředí.',
            'rýže': 'Rýže vydrží neomezeně v uzavřené nádobě.'
        }

        for key, tip in tips.items():
            if key in ingredient_lower:
                result['tip'] = tip
                break

    return result


def generate_shopping_list(weeks: List[Dict[str, Dict]], have_at_home: List[str] = None) -> Dict:
    """
    Aggregate ingredients from all weeks into shopping list with smart rounding and 'have at home' deduction.

    Returns:
        dict: {
            'shopping_list': {category: [items]},
            'have_at_home_items': [items],
            'leftovers': [{ingredient, leftover, tip}],
            'total_packages': int
        }
    """
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
    have_at_home_items = []
    leftovers = []
    total_packages = 0

    have_at_home_lower = [item.lower() for item in (have_at_home or [])]

    for category, items in shopping_dict.items():
        smart_items = []
        for name, amount in items.items():
            # Pokud už máme doma, přidej do "mám doma" seznamu
            if any(have_item in name.lower() for have_item in have_at_home_lower):
                have_at_home_items.append(f"{name} - {amount}")
                continue  # Není v nákupním seznamu

            # Smart rounding
            rounded_info = round_to_package_size(name, amount)
            total_packages += rounded_info['packages_needed']

            # Formátuj do textu
            display_text = f"{name} - {rounded_info['rounded_amount']}"

            # Přidej info o původním množství pokud se liší
            if rounded_info['original_amount'] != rounded_info['rounded_amount']:
                display_text += f" (potřebuješ {rounded_info['original_amount']})"

            smart_items.append(display_text)

            # Shromáždi info o zbytcích
            if 'leftover' in rounded_info:
                leftover_entry = {
                    'ingredient': name,
                    'leftover': rounded_info['leftover']
                }
                if 'tip' in rounded_info:
                    leftover_entry['tip'] = rounded_info['tip']
                leftovers.append(leftover_entry)

        if smart_items:  # Přidej jen pokud má items
            shopping_list[category] = smart_items

    return {
        'shopping_list': shopping_list,
        'have_at_home_items': have_at_home_items,
        'leftovers': leftovers,
        'total_packages': total_packages
    }

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

    # Generate smart shopping list (for all weeks including desserts, minus "mám doma")
    shopping_result = generate_shopping_list(weeks_with_desserts, have_at_home)

    # Calculate costs (včetně dezertů)
    total_cost = calculate_total_cost(weeks_with_desserts)
    total_portions = sum(sum(r['servings'] for r in week.values()) for week in weeks_with_desserts)

    # Váhy pro weighted overlap statistics
    INGREDIENT_WEIGHTS = {
        'maso': 3.0, 'ryby': 3.0,
        'zelenina': 2.0, 'vegetables': 2.0,
        'mléčné': 2.0, 'dairy': 2.0,
        'trvanlivé': 1.0, 'pantry': 1.0,
        'ostatní': 0.5
    }

    # Spočítej vážený překryv ingrediencí (pro statistiku úspor)
    all_ingredients = {}  # {name: category}
    unique_count = 0
    weighted_reuse = 0.0

    for week in weeks_with_desserts:
        for recipe in week.values():
            for ing in recipe['ingredients']:
                ing_base = ing['name'].lower().split()[0]
                ing_category = ing.get('category', 'ostatní').lower()

                if ing_base not in all_ingredients:
                    unique_count += 1
                    all_ingredients[ing_base] = ing_category
                else:
                    # Přičti váhu za opakované použití
                    weight = INGREDIENT_WEIGHTS.get(ing_category, 0.5)
                    weighted_reuse += weight

    total_ingredient_uses = sum(sum(len(r['ingredients']) for r in week.values()) for week in weeks_with_desserts)
    reuse_count = total_ingredient_uses - unique_count
    reuse_percentage = round((reuse_count / total_ingredient_uses) * 100) if total_ingredient_uses > 0 else 0

    # Odhadni úspory z překryvu (weighted)
    avg_ingredient_cost = 30  # Kč průměr
    estimated_savings = round(weighted_reuse * avg_ingredient_cost)

    return {
        "week_of": "2024-11-18",
        "preferences": preferences,
        "weeks": weeks_with_desserts,  # List[Dict[str, Dict]] - včetně dezertů
        "meals": weeks_with_desserts[0] if weeks_with_desserts else {},  # První týden pro zpětnou kompatibilitu
        "num_weeks": num_weeks,
        "weekly_desserts": weekly_desserts,  # Samostatný seznam dezertů pro zobrazení
        "shopping_list": shopping_result['shopping_list'],  # Zpětná kompatibilita
        "shopping_details": shopping_result,  # Nová detailní struktura
        "total_cost_czk": total_cost,
        "cost_per_portion_czk": round(total_cost / total_portions, 1) if total_portions > 0 else 0,
        "ingredient_stats": {
            "total_uses": total_ingredient_uses,
            "unique_ingredients": unique_count,
            "reused_count": reuse_count,
            "reuse_percentage": reuse_percentage,
            "weighted_reuse_score": round(weighted_reuse, 1),
            "estimated_savings_czk": estimated_savings
        }
    }
