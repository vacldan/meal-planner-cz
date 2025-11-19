#!/usr/bin/env python3
"""
Audit skript pro recipes.json
- Přidá tag "seasonal" receptům se sezónními ingrediencemi
- Zkontroluje a doplní chybějící alergeny
- Vytvoří backup a report
"""

import json
import shutil
from datetime import datetime
from collections import defaultdict

# Sezónní ingredience podle ročního období
SEASONAL_INGREDIENTS = {
    'jaro': ['chřest', 'špenát', 'ředkvičk', 'ředkev', 'jahod', 'hrách', 'mladá mrkev', 'salát', 'pažitka', 'medvědí česnek'],
    'léto': ['rajčat', 'paprik', 'cuket', 'okurk', 'baklažán', 'brokolice', 'kukuřic', 'třešn', 'meruňk', 'broskv', 'maliny', 'borůvky'],
    'podzim': ['dýň', 'bramb', 'zelí', 'houb', 'jablk', 'hruš', 'švestk', 'hroznů', 'květák', 'kapusta', 'řepa', 'pórek'],
    'zima': ['mrkev', 'celer', 'petržel', 'zelí', 'kedlubna', 'květák', 'kapusta', 'pór', 'brukev']
}

# Mapování ingrediencí na alergeny (český formát s EU čísly)
ALLERGEN_MAPPING = {
    '1. Lepek (pšenice, žito, ječmen, oves)': ['mouka', 'těstoviny', 'chléb', 'špaget', 'penne', 'nudle', 'krupice', 'strouhanka', 'bulka', 'houska', 'sójová omáčka', 'soy sauce'],
    '7. Mléko a mléčné výrobky': ['mléko', 'smetana', 'sýr', 'máslo', 'jogurt', 'tvaroh', 'zakysaná', 'parmazán', 'mozzarella', 'eidam', 'čedar', 'mascarpone', 'ricotta', 'cream'],
    '3. Vejce': ['vejce', 'vaječn', 'egg'],
    '4. Ryby': ['losos', 'treska', 'tuňák', 'kapr', 'pstruh', 'sleď', 'makrela', 'fish'],
    '2. Korýši': ['krevet', 'garnát', 'humr', 'krab', 'shrimp', 'prawn'],
    '14. Měkkýši': ['slávk', 'mušl', 'chobotnic', 'sépie'],
    '8. Ořechy (skořápkové plody)': ['oříšk', 'mandle', 'lískové', 'vlašské', 'kešu', 'pistácie', 'pekan', 'nut', 'almond', 'walnut', 'cashew'],
    '5. Arašídy (podzemnice olejná)': ['arašíd', 'peanut'],
    '6. Sója': ['sójov', 'tofu', 'soy', 'tempeh'],
    '11. Sezam (sezamová semena)': ['sezam', 'sesame'],
    '9. Celer': ['celer', 'celery'],
    '10. Hořčice': ['hořčic', 'mustard'],
    '12. Oxid siřičitý a siřičitany': ['víno', 'sušené'],
    '13. Vlčí bob (lupina)': ['vlčí bob', 'lupina', 'lupin']
}

def detect_seasonal_ingredients(recipe):
    """Detekuje, zda recept obsahuje sezónní ingredience"""
    recipe_text = recipe['name'].lower()

    # Přidej ingredience do textu
    for ing in recipe['ingredients']:
        recipe_text += ' ' + ing['name'].lower()

    # Kontroluj všechna roční období
    seasonal_matches = []
    for season, keywords in SEASONAL_INGREDIENTS.items():
        for keyword in keywords:
            if keyword in recipe_text:
                seasonal_matches.append((season, keyword))
                break  # Stačí jeden match ze sezóny

    return len(seasonal_matches) > 0, seasonal_matches

def detect_missing_allergens(recipe):
    """Detekuje chybějící alergeny v receptu"""
    current_allergens = recipe.get('allergens', [])
    recipe_text = recipe['name'].lower()

    # Přidej ingredience do textu
    for ing in recipe['ingredients']:
        recipe_text += ' ' + ing['name'].lower()

    missing_allergens = []

    for allergen, keywords in ALLERGEN_MAPPING.items():
        # Pokud už alergen máme, přeskoč (kontroluj přesnou shodu)
        if allergen in current_allergens:
            continue

        # Kontroluj, zda recept obsahuje klíčová slova
        for keyword in keywords:
            if keyword in recipe_text:
                missing_allergens.append((allergen, keyword))
                break

    return missing_allergens

def audit_recipes(input_file='recipes.json', output_file='recipes.json', create_backup=True):
    """Hlavní audit funkce"""

    print("🔍 Začínám audit receptů...")
    print("=" * 60)

    # Načti recipes.json
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    recipes = data['recipes']
    total_recipes = len(recipes)

    print(f"📊 Celkem receptů: {total_recipes}\n")

    # Statistiky
    stats = {
        'seasonal_added': 0,
        'allergens_added': 0,
        'recipes_with_seasonal': [],
        'recipes_with_new_allergens': defaultdict(list),
        'seasonal_matches': defaultdict(list)
    }

    # Projdi všechny recepty
    for recipe in recipes:
        modified = False

        # 1. Kontrola sezónních ingrediencí
        is_seasonal, seasonal_matches = detect_seasonal_ingredients(recipe)

        if is_seasonal:
            # Přidej tag 'seasonal' pokud tam ještě není
            if 'tags' not in recipe:
                recipe['tags'] = []

            if 'seasonal' not in recipe['tags']:
                recipe['tags'].append('seasonal')
                stats['seasonal_added'] += 1
                stats['recipes_with_seasonal'].append(recipe['name'])
                modified = True

                # Zaznamenej, které sezónní ingredience byly nalezeny
                for season, ing in seasonal_matches:
                    stats['seasonal_matches'][recipe['name']].append(f"{ing} ({season})")

        # 2. Kontrola chybějících alergenů
        missing_allergens = detect_missing_allergens(recipe)

        if missing_allergens:
            if 'allergens' not in recipe:
                recipe['allergens'] = []

            for allergen, keyword in missing_allergens:
                if allergen not in recipe['allergens']:
                    recipe['allergens'].append(allergen)
                    stats['allergens_added'] += 1
                    stats['recipes_with_new_allergens'][recipe['name']].append(f"{allergen} (kvůli: {keyword})")
                    modified = True

    # Vytvoř backup před uložením
    if create_backup and modified:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"recipes_backup_{timestamp}.json"
        shutil.copy(input_file, backup_file)
        print(f"💾 Vytvořen backup: {backup_file}\n")

    # Ulož aktualizovaný soubor
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Vytvoř report
    print("=" * 60)
    print("📋 REPORT ZMĚN")
    print("=" * 60)

    print(f"\n✅ SEZÓNNÍ JÍDLA:")
    print(f"   Přidán tag 'seasonal' do {stats['seasonal_added']} receptů")

    if stats['seasonal_added'] > 0:
        print(f"\n   📝 Recepty označené jako sezónní (ukázka prvních 10):")
        for recipe_name in stats['recipes_with_seasonal'][:10]:
            ingredients = ', '.join(stats['seasonal_matches'][recipe_name])
            print(f"      • {recipe_name}")
            print(f"        └─ Sezónní ingredience: {ingredients}")

        if stats['seasonal_added'] > 10:
            print(f"      ... a {stats['seasonal_added'] - 10} dalších")

    print(f"\n✅ ALERGENY:")
    print(f"   Přidáno celkem {stats['allergens_added']} nových alergenů")

    if stats['allergens_added'] > 0:
        print(f"\n   📝 Recepty s doplněnými alergeny (ukázka prvních 10):")
        count = 0
        for recipe_name, allergens in list(stats['recipes_with_new_allergens'].items())[:10]:
            print(f"      • {recipe_name}")
            for allergen in allergens:
                print(f"        └─ +{allergen}")
            count += 1

        if len(stats['recipes_with_new_allergens']) > 10:
            print(f"      ... a {len(stats['recipes_with_new_allergens']) - 10} dalších receptů")

    # Finální statistiky
    print("\n" + "=" * 60)
    print("📊 FINÁLNÍ STATISTIKY")
    print("=" * 60)

    # Znovu načti a spočítej
    with open(output_file, 'r', encoding='utf-8') as f:
        updated_data = json.load(f)

    updated_recipes = updated_data['recipes']

    # Kategorie
    from collections import Counter
    categories = Counter(r['category'] for r in updated_recipes)

    # Tagy
    all_tags = []
    for r in updated_recipes:
        all_tags.extend(r.get('tags', []))
    tags = Counter(all_tags)

    # Seasonal
    seasonal_count = tags.get('seasonal', 0)
    print(f"\n🌱 SEZÓNNÍ JÍDLA: {seasonal_count} receptů má tag 'seasonal'")

    # Alergeny
    all_allergens = []
    for r in updated_recipes:
        all_allergens.extend(r.get('allergens', []))
    allergens = Counter(all_allergens)

    print(f"\n⚠️  ALERGENY (top 5):")
    for allergen, count in allergens.most_common(5):
        print(f"   • {allergen}: {count} receptů")

    print("\n✅ Audit dokončen!")
    print("=" * 60)

    return stats

if __name__ == '__main__':
    stats = audit_recipes()
