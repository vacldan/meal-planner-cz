"""
Streamlit web aplikace pro Czech Meal Planner
"""

import streamlit as st
import json
from meal_planner import generate_meal_plan
from pdf_generator import generate_pdf
import os

# Page config
st.set_page_config(
    page_title="🍽️ Czech Meal Planner",
    page_icon="🍽️",
    layout="wide"
)

# Title
st.title("🍽️ Czech Meal Planner")
st.markdown("### Personalizovaný týdenní jídelníček s AI")
st.divider()

# Sidebar - Preferences
st.sidebar.header("📋 Tvoje Preference")

household_size = st.sidebar.number_input(
    "Velikost domácnosti (počet osob)",
    min_value=1,
    max_value=10,
    value=4
)

st.sidebar.subheader("Kategorie, které máš rád")
likes = st.sidebar.multiselect(
    "Vyber kategorie",
    ["pasta", "czech_traditional", "quick", "comfort"],
    default=["pasta", "czech_traditional", "quick"]
)

st.sidebar.subheader("Časový budget")
time_budget = st.sidebar.select_slider(
    "Kolik minut na přípravu večeře?",
    options=["15-25", "20-45", "30-60", "30-120"],
    value="20-45"
)

st.sidebar.subheader("Alergeny a omezení")
allergies = st.sidebar.multiselect(
    "Alergie",
    ["gluten", "dairy", "eggs", "soy", "nuts"],
    default=[]
)

dislikes = st.sidebar.multiselect(
    "Co nechceš v jídle",
    ["fish", "mushrooms", "seafood", "liver", "pork"],
    default=["fish"]
)

kid_friendly = st.sidebar.checkbox("Jen jídla vhodná pro děti", value=True)

# Generate button
if st.sidebar.button("🚀 Generuj Meal Plan", type="primary"):

    # Prepare preferences
    preferences = {
        "household_size": household_size,
        "allergies": allergies,
        "likes": likes,
        "time_budget": time_budget,
        "price_budget": "30-70",
        "dislikes": dislikes,
        "kid_friendly_required": kid_friendly
    }

    # Show loading spinner
    with st.spinner("🤖 Generuji tvůj personalizovaný meal plan..."):
        try:
            # Generate meal plan
            meal_plan = generate_meal_plan(preferences)

            # Save to session state
            st.session_state.meal_plan = meal_plan
            st.session_state.preferences = preferences

            # Generate PDF
            pdf_path = generate_pdf(meal_plan, "generated_meal_plan.pdf")
            st.session_state.pdf_path = pdf_path

            st.success("✅ Meal plan vygenerován!")

        except Exception as e:
            st.error(f"❌ Chyba při generování: {str(e)}")
            st.info("💡 Tip: Zkus upravit své preference (např. rozšířit časový budget nebo odstranit některá omezení)")

# Display results
if "meal_plan" in st.session_state:
    meal_plan = st.session_state.meal_plan

    # Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Celková cena týdne", f"{meal_plan['total_cost_czk']} Kč")
    with col2:
        st.metric("📊 Cena na porci", f"{meal_plan['cost_per_portion_czk']} Kč")
    with col3:
        total_portions = sum(r['servings'] for r in meal_plan['meals'].values())
        st.metric("🍽️ Celkem porcí", f"{total_portions}")

    st.divider()

    # Download PDF button
    if os.path.exists("generated_meal_plan.pdf"):
        with open("generated_meal_plan.pdf", "rb") as pdf_file:
            st.download_button(
                label="📥 Stáhnout PDF s recepty a nákupním seznamem",
                data=pdf_file.read(),
                file_name="muj_jidelnicek.pdf",
                mime="application/pdf",
                type="primary"
            )

    st.divider()

    # Weekly menu
    st.header("📅 Týdenní Menu")

    days_czech = {
        'monday': 'Pondělí',
        'tuesday': 'Úterý',
        'wednesday': 'Středa',
        'thursday': 'Čtvrtek',
        'friday': 'Pátek',
        'saturday': 'Sobota',
        'sunday': 'Neděle'
    }

    # Display recipes
    for day_en, day_cz in days_czech.items():
        recipe = meal_plan['meals'][day_en]

        with st.expander(f"**{day_cz}**: {recipe['name']} ({recipe['time_minutes']} min, {recipe['price_per_portion_czk']} Kč/porce)"):

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📝 Ingredience")
                for ingredient in recipe['ingredients']:
                    st.markdown(f"- {ingredient['name']} - {ingredient['amount']}")

                st.subheader("👨‍🍳 Postup")
                for i, step in enumerate(recipe['steps'], 1):
                    st.markdown(f"{i}. {step}")

            with col2:
                st.metric("⏱️ Čas", f"{recipe['time_minutes']} min")
                st.metric("📊 Obtížnost", recipe['difficulty'])
                st.metric("👥 Porce", recipe['servings'])
                st.metric("💰 Cena/porce", f"{recipe['price_per_portion_czk']} Kč")

                if recipe.get('allergens'):
                    st.warning(f"⚠️ Alergeny: {', '.join(recipe['allergens'])}")

    st.divider()

    # Shopping list
    st.header("🛒 Nákupní Seznam")

    category_names = {
        'meat': '🥩 Maso & Ryby',
        'vegetables': '🥬 Zelenina & Ovoce',
        'dairy': '🥛 Mléčné Výrobky',
        'pantry': '🥫 Trvanlivé'
    }

    cols = st.columns(2)

    for i, (category, items) in enumerate(meal_plan['shopping_list'].items()):
        with cols[i % 2]:
            st.subheader(category_names.get(category, category))
            for item in items:
                st.checkbox(item, key=f"{category}_{item}")

    st.divider()
    st.success(f"💰 Odhadovaná cena nákupu: **{meal_plan['total_cost_czk']} Kč**")

else:
    # Welcome message
    st.info("👈 Nastav své preference v postranním menu a klikni na **'Generuj Meal Plan'**")

    st.markdown("""
    ### ✨ Jak to funguje?

    1. **Nastav preference** v levém menu:
       - Velikost domácnosti
       - Kategorie jídel, které máš rád
       - Časový budget
       - Alergie a omezení

    2. **Klikni na tlačítko** "Generuj Meal Plan"

    3. **Získej:**
       - 7 receptů na celý týden
       - Automatický nákupní seznam
       - Krásné PDF ke stažení
       - Kalkulaci ceny

    ### 📊 Dostupné kategorie receptů:

    - **Pasta** - Italská klasika i české adaptace
    - **Czech Traditional** - Guláš, řízek, bramboráky...
    - **Quick** - Rychlé večeře do 30 minut
    - **Comfort** - Pizza, lasagne, comfort food

    ### 🎯 Demo features:

    ✅ 10 autentických českých receptů
    ✅ Personalizace dle preferencí
    ✅ Filtrování alergií
    ✅ Automatický nákupní seznam
    ✅ PDF download
    ✅ Kalkulace ceny
    """)
