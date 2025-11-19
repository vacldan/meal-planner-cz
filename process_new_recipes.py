#!/usr/bin/env python3
"""
Skript pro zpracování nových receptů:
1. Filtruje placeholdery
2. Kontroluje duplicity
3. Přidává jen validní nové recepty
"""

import json
from collections import defaultdict

# Načti nové recepty
new_recipes_json = """
{JSON_DATA_HERE}
"""

def is_valid_recipe(recipe):
    """Kontroluje, jestli recept není placeholder"""
    # Placeholder charakteristiky:
    # - Má "Tempeh recept" v názvu
    # - Má generické ingredience jako "Hlavní ingredience", "Ingredience 1"
    # - Má generické kroky jako "Krok 1: Příprava"

    name = recipe['name'].lower()

    # Tempeh recept XYZ
    if 'tempeh recept' in name and name.split()[-1].isdigit():
        return False

    # Kontrola placeholder ingrediencí
    for ing in recipe['ingredients']:
        ing_name = ing['name'].lower()
        if any(placeholder in ing_name for placeholder in ['ingredience 1', 'ingredience 2', 'hlavní ingredience', 'hlavní surovina', 'dresink ingredience', 'zelenina mix']):
            return False

    # Kontrola placeholder kroků
    if recipe['steps']:
        first_step = recipe['steps'][0].lower()
        if 'krok 1:' in first_step or 'připravte hlavní' in first_step:
            return False

    return True

def check_duplicate(recipe, existing_recipes):
    """Kontroluje, jestli recept už existuje"""
    name_lower = recipe['name'].lower().strip()

    for existing in existing_recipes:
        existing_name = existing['name'].lower().strip()

        # Přesná shoda názvu
        if name_lower == existing_name:
            return True

        # Velmi podobné názvy (editační vzdálenost)
        if abs(len(name_lower) - len(existing_name)) <= 3:
            # Jednoduché porovnání
            common = sum(1 for a, b in zip(name_lower, existing_name) if a == b)
            if common / max(len(name_lower), len(existing_name)) > 0.9:
                return True

    return False

# Načti současné recepty
with open('recipes.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    existing_recipes = data['recipes']

print(f"📊 Současný stav: {len(existing_recipes)} receptů (ID 1-{existing_recipes[-1]['id']})")
print("\n🔍 Analyzuji nové recepty...\n")

# Parsuj nové recepty z poskytnutého JSON
try:
    new_recipes = json.loads(new_recipes_json)
    if isinstance(new_recipes, dict) and 'recipes' in new_recipes:
        new_recipes = new_recipes['recipes']
except json.JSONDecodeError as e:
    print(f"❌ Chyba při parsování JSON: {e}")
    exit(1)

# Statistiky
stats = {
    'total': len(new_recipes),
    'valid': 0,
    'duplicates': 0,
    'placeholders': 0,
    'added': []
}

print("=" * 70)
print("ANALÝZA NOVÝCH RECEPTŮ")
print("=" * 70)
print(f"📥 Načteno receptů k analýze: {stats['total']}\n")

# Zpracuj každý nový recept
valid_new_recipes = []

for recipe in new_recipes:
    recipe_name = recipe['name']

    # 1. Kontrola, jestli není placeholder
    if not is_valid_recipe(recipe):
        print(f"❌ PLACEHOLDER: {recipe_name}")
        stats['placeholders'] += 1
        continue

    # 2. Kontrola duplicity
    if check_duplicate(recipe, existing_recipes):
        print(f"⚠️  DUPLICITA: {recipe_name}")
        stats['duplicates'] += 1
        continue

    # 3. Validní nový recept
    print(f"✅ VALIDNÍ: {recipe_name}")
    stats['valid'] += 1
    valid_new_recipes.append(recipe)

print("\n" + "=" * 70)
print("📊 VÝSLEDKY ANALÝZY")
print("=" * 70)
print(f"Celkem analyzováno: {stats['total']}")
print(f"✅ Validní nové recepty: {stats['valid']}")
print(f"⚠️  Duplicity: {stats['duplicates']}")
print(f"❌ Placeholder recepty: {stats['placeholders']}")

if stats['valid'] > 0:
    print(f"\n🎉 Přidávám {stats['valid']} nových receptů...\n")

    # Získej poslední ID
    last_id = existing_recipes[-1]['id'] if existing_recipes else 0

    # Přiřaď nová ID a přidej recepty
    for idx, recipe in enumerate(valid_new_recipes, start=1):
        recipe['id'] = last_id + idx
        existing_recipes.append(recipe)
        stats['added'].append(recipe['name'])
        print(f"   {idx}. {recipe['name']} (ID: {recipe['id']})")

    # Ulož aktualizovaný recipes.json
    with open('recipes.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Nový stav: {len(existing_recipes)} receptů (ID 1-{existing_recipes[-1]['id']})")
    print("💾 recipes.json úspěšně aktualizován!")
else:
    print("\n❌ Žádné validní nové recepty k přidání.")

print("=" * 70)
