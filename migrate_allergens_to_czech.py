#!/usr/bin/env python3
"""
Migrace alergenů z anglické verze na českou s čísly dle EU směrnice 2000/89 ES
"""

import json
import shutil
from datetime import datetime

# Mapování anglických alergenů na české s EU čísly
ALLERGEN_MIGRATION_MAP = {
    'gluten': '1. Lepek (pšenice, žito, ječmen, oves)',
    'shellfish': '2. Korýši',
    'crustaceans': '2. Korýši',
    'eggs': '3. Vejce',
    'fish': '4. Ryby',
    'peanuts': '5. Arašídy (podzemnice olejná)',
    'soy': '6. Sója',
    'soja': '6. Sója',
    'dairy': '7. Mléko a mléčné výrobky',
    'milk': '7. Mléko a mléčné výrobky',
    'nuts': '8. Ořechy (skořápkové plody)',
    'celery': '9. Celer',
    'mustard': '10. Hořčice',
    'sesame': '11. Sezam (sezamová semena)',
    'sulfites': '12. Oxid siřičitý a siřičitany',
    'lupin': '13. Vlčí bob (lupina)',
    'molluscs': '14. Měkkýši',
    'mollusks': '14. Měkkýši'
}

# Mapování číselných alergenů (starý formát) na české s EU názvy
NUMBER_ALLERGEN_MAP = {
    1: '1. Lepek (pšenice, žito, ječmen, oves)',
    2: '2. Korýši',
    3: '3. Vejce',
    4: '4. Ryby',
    5: '5. Arašídy (podzemnice olejná)',
    6: '6. Sója',
    7: '7. Mléko a mléčné výrobky',
    8: '8. Ořechy (skořápkové plody)',
    9: '9. Celer',
    10: '10. Hořčice',
    11: '11. Sezam (sezamová semena)',
    12: '12. Oxid siřičitý a siřičitany',
    13: '13. Vlčí bob (lupina)',
    14: '14. Měkkýši'
}

def migrate_allergens(input_file='recipes.json', output_file='recipes.json', create_backup=True):
    """Migruje alergeny ze současné anglické verze na českou s EU čísly"""

    print("🔄 Začínám migraci alergenů na český formát...")
    print("=" * 70)

    # Načti recipes.json
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    recipes = data['recipes']
    total_recipes = len(recipes)

    print(f"📊 Celkem receptů k migraci: {total_recipes}\n")

    # Statistiky
    stats = {
        'migrated': 0,
        'no_allergens': 0,
        'unknown_allergens': [],
        'allergen_counts': {}
    }

    # Projdi všechny recepty
    for recipe in recipes:
        if 'allergens' not in recipe or not recipe['allergens']:
            stats['no_allergens'] += 1
            continue

        # Migruj alergeny
        old_allergens = recipe['allergens']
        new_allergens = []

        for allergen in old_allergens:
            # Handle integer allergens (old dessert format)
            if isinstance(allergen, int):
                if allergen in NUMBER_ALLERGEN_MAP:
                    czech_allergen = NUMBER_ALLERGEN_MAP[allergen]
                    if czech_allergen not in new_allergens:
                        new_allergens.append(czech_allergen)

                        # Počítej statistiky
                        if czech_allergen not in stats['allergen_counts']:
                            stats['allergen_counts'][czech_allergen] = 0
                        stats['allergen_counts'][czech_allergen] += 1
                else:
                    print(f"⚠️  Neznámé číslo alergenu '{allergen}' v receptu: {recipe['name']}")
                continue

            allergen_lower = allergen.lower().strip()

            # Pokud už je v novém formátu (začíná číslem), nech ho být
            if allergen.strip() and allergen.strip()[0].isdigit():
                new_allergens.append(allergen)
                continue

            # Převeď z anglického na český
            if allergen_lower in ALLERGEN_MIGRATION_MAP:
                czech_allergen = ALLERGEN_MIGRATION_MAP[allergen_lower]
                if czech_allergen not in new_allergens:
                    new_allergens.append(czech_allergen)

                    # Počítej statistiky
                    if czech_allergen not in stats['allergen_counts']:
                        stats['allergen_counts'][czech_allergen] = 0
                    stats['allergen_counts'][czech_allergen] += 1
            else:
                # Neznámý alergen
                if allergen_lower not in stats['unknown_allergens']:
                    stats['unknown_allergens'].append(allergen_lower)
                print(f"⚠️  Neznámý alergen '{allergen}' v receptu: {recipe['name']}")

        # Aktualizuj recept
        if new_allergens:
            recipe['allergens'] = sorted(new_allergens)  # Seřaď podle čísla
            stats['migrated'] += 1

    # Vytvoř backup před uložením
    if create_backup:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"recipes_backup_allergen_migration_{timestamp}.json"
        shutil.copy(input_file, backup_file)
        print(f"💾 Vytvořen backup: {backup_file}\n")

    # Ulož aktualizovaný soubor
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Vytvoř report
    print("=" * 70)
    print("📋 REPORT MIGRACE")
    print("=" * 70)

    print(f"\n✅ Migrováno receptů: {stats['migrated']}")
    print(f"📝 Receptů bez alergenů: {stats['no_allergens']}")

    if stats['unknown_allergens']:
        print(f"\n⚠️  Neznámé alergeny ({len(stats['unknown_allergens'])}): {', '.join(stats['unknown_allergens'])}")

    print(f"\n📊 ROZDĚLENÍ ALERGENŮ (top 10):")
    sorted_allergens = sorted(stats['allergen_counts'].items(), key=lambda x: x[1], reverse=True)
    for allergen, count in sorted_allergens[:10]:
        print(f"   • {allergen}: {count} receptů")

    print("\n✅ Migrace dokončena!")
    print("=" * 70)

    return stats

if __name__ == '__main__':
    stats = migrate_allergens()
