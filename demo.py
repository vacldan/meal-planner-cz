"""
Demo script - generates sample meal plan
"""

import json
from meal_planner import generate_meal_plan
from pdf_generator import generate_pdf

def run_demo():
    """Run complete demo"""

    print("🚀 MEAL PLANNER DEMO")
    print("=" * 50)

    # Sample user preferences
    preferences = {
        "household_size": 4,
        "allergies": [],  # Options: "gluten", "dairy", "eggs", "nuts"
        "likes": ["pasta", "czech_traditional", "quick"],
        "time_budget": "20-45",  # minutes
        "price_budget": "40-70",  # Kč per portion
        "dislikes": ["fish"],  # Will avoid recipes with fish
        "kid_friendly_required": True
    }

    print("\n📋 Tvoje preference:")
    print(json.dumps(preferences, indent=2, ensure_ascii=False))

    # Generate meal plan
    print("\n🤖 Generuji jídelníček...")
    meal_plan = generate_meal_plan(preferences)

    # Save to JSON
    with open('meal_plan_output.json', 'w', encoding='utf-8') as f:
        json.dump(meal_plan, f, indent=2, ensure_ascii=False)
    print("✅ Meal plan uložen: meal_plan_output.json")

    # Print summary
    print("\n" + "=" * 50)
    print("📅 TÝDENNÍ MENU:")
    print("=" * 50)

    days_czech = {
        'monday': 'Pondělí',
        'tuesday': 'Úterý',
        'wednesday': 'Středa',
        'thursday': 'Čtvrtek',
        'friday': 'Pátek',
        'saturday': 'Sobota',
        'sunday': 'Neděle'
    }

    for day, recipe in meal_plan['meals'].items():
        print(f"{days_czech[day]}: {recipe['name']}")
        print(f"  ⏱️  {recipe['time_minutes']} min  |  💰 {recipe['price_per_portion_czk']} Kč/porce")
        print()

    print("=" * 50)
    print(f"💰 Celková cena: {meal_plan['total_cost_czk']} Kč")
    print(f"📊 Cena na porci: {meal_plan['cost_per_portion_czk']} Kč")
    print("=" * 50)

    # Generate PDF
    print("\n📄 Generuji PDF...")
    pdf_path = generate_pdf(meal_plan, "muj_jidelnicek.pdf")

    print("\n✨ HOTOVO!")
    print(f"📱 Otevři: {pdf_path}")
    print("\n💡 TIP: Vytiskni si PDF nebo ulož do mobilu pro snadný nákup!")

if __name__ == "__main__":
    run_demo()
