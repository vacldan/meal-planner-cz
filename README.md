# 🍽️ Czech Meal Planner Demo

Personalizovaný týdenní jídelníček s AI - Demo verze

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run demo:**
   ```bash
   python demo.py
   ```

3. **Output:**
   - `meal_plan_output.json` - Data meal plánu
   - `muj_jidelnicek.pdf` - Krásné PDF s recepty a nákupním seznamem

## 📝 Customize Preferences

Edit preferences in `demo.py`:

```python
preferences = {
    "household_size": 4,
    "allergies": [],  # ["gluten", "dairy", "eggs"]
    "likes": ["pasta", "czech_traditional"],
    "time_budget": "20-45",
    "dislikes": ["fish", "mushrooms"],
    "kid_friendly_required": True
}
```

## 🎨 Features

- ✅ 10 autentických českých receptů
- ✅ Personalizace dle preferencí
- ✅ Automatický nákupní seznam
- ✅ Kalkulace ceny
- ✅ Profesionální PDF output

## 📦 Project Structure

```
meal-planner-demo/
├── demo.py              # Main script
├── meal_planner.py      # Core logic
├── pdf_generator.py     # PDF creation
├── recipes.json         # Recipe database
└── templates/
    └── meal_plan_template.html
```
