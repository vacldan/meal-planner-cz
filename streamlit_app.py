"""
Streamlit web aplikace pro Czech Meal Planner
"""

import streamlit as st
import json
from meal_planner import generate_meal_plan
from pdf_generator import generate_pdf
import os

# Kategorie receptů (seřazeno abecedně)
CATEGORIES = [
    "Jídla pro děti",
    "Polévky",
    "Rodinná klasika",
    "Rychlá jídla",
    "Tradiční česká",
    "Těstoviny",
    "Veganské",
    "Vegetariánské"
]

# Potraviny, které nechceš (seřazeno abecedně)
DISLIKES = [
    "Brokolice",
    "Cibule",
    "Česnek",
    "Čočka",
    "Fazole",
    "Hovězí",
    "Houby",
    "Koření (pikantní)",
    "Kuřecí",
    "Květák",
    "Mořské plody",
    "Paprika",
    "Rajčata",
    "Ryby",
    "Smetana",
    "Sýr",
    "Vepřové",
    "Vnitřnosti"
]

# Alergeny - kompletní seznam 14 hlavních alergenů EU (seřazeno abecedně)
ALLERGENS = [
    "Arašídy",
    "Celer",
    "Hořčice",
    "Korýši (krevety, humr, krab)",
    "Lepek (pšenice, žito, ječmen, oves)",
    "Měkkýši (slávky, chobotnice)",
    "Mléko a mléčné výrobky",
    "Ořechy (mandle, lískové, vlašské, kešu)",
    "Oxid siřičitý (konzervanty E220-E228)",
    "Ryby",
    "Sezam",
    "Sója",
    "Vejce",
    "Vlčí bob (lupina)"
]

# Vybavení kuchyně (seřazeno abecedně)
EQUIPMENT = [
    "Air fryer (fritéza na vzduch)",
    "Mikrovlnka",
    "Mixér/Tyčový mixér",
    "Slow cooker (pomalý hrnec)",
    "Trouba"
]

# Běžné ingredience, které lidé často mají doma (seřazeno abecedně)
COMMON_PANTRY_ITEMS = [
    "Bazalka",
    "Bobkový list",
    "Brambory",
    "Bujón/Vývar kostky",
    "Cibule",
    "Citron",
    "Cukr",
    "Cukr moučka",
    "Česnek",
    "Droždí",
    "Eidam",
    "Hořčice",
    "Instantní polévky",
    "Jogurt",
    "Kečup",
    "Kmín",
    "Kypřicí prášek",
    "Majoránka",
    "Máslo",
    "Med",
    "Mléko",
    "Mouka hladká",
    "Mouka hrubá",
    "Mouka polohrubá",
    "Mrkev",
    "Muškátový oříšek",
    "Nové koření",
    "Ocet",
    "Olej slunečnicový",
    "Olivový olej",
    "Oregano",
    "Paprika pálivá",
    "Paprika sladká",
    "Parmazán",
    "Pepř",
    "Petržel",
    "Rajčata",
    "Rýže",
    "Smetana ke šlehání",
    "Smetana na vaření",
    "Sojová omáčka",
    "Sůl",
    "Sýr",
    "Tvaroh",
    "Tymián",
    "Těstoviny",
    "Vanilkový cukr",
    "Vejce",
    "Zakysaná smetana",
    "Zázvor",
    "Škrob"
]

# Page config
st.set_page_config(
    page_title="🍽️ Týdenní Jídelníček",
    page_icon="🍽️",
    layout="wide"
)

# Title
st.title("🍽️ Tvůj Týdenní Jídelníček")
st.markdown("### Personalizovaný plán večeří s AI")
st.divider()

# Sidebar - Preferences
st.sidebar.header("📋 Tvoje Preference")

num_weeks = st.sidebar.selectbox(
    "📅 Kolik týdnů chceš naplánovat?",
    options=[1, 2, 3, 4],
    index=0,
    help="Recepty se nebudou opakovat - maximálně 1x za 3 týdny"
)

household_size = st.sidebar.number_input(
    "Velikost domácnosti (počet osob)",
    min_value=1,
    max_value=10,
    value=4
)

st.sidebar.divider()

# 1. Jaká jídla máš rád
st.sidebar.subheader("🍽️ Jaká jídla máš rád?")
st.sidebar.markdown("*Vyber jeden nebo více typů:*")
likes = st.sidebar.multiselect(
    "Kategorie jídel",
    CATEGORIES,
    default=["Rychlá jídla", "Tradiční česká", "Těstoviny"],
    help="""
    • Jídla pro děti - jednoduchá, neexotická jídla vhodná pro děti\n
    • Polévky - zeleninové, vývarové, krémové\n
    • Rodinná klasika - pizza, burgery, palačinky\n
    • Rychlá jídla - do 30 minut\n
    • Tradiční česká - guláš, svíčková, řízek\n
    • Těstoviny - špagety, lasagne, penne\n
    • Veganské - bez živočišných produktů\n
    • Vegetariánské - bez masa a ryb
    """
)

st.sidebar.divider()

# 2. Co nechceš v jídle
st.sidebar.subheader("❌ Co nechceš v jídle")
st.sidebar.markdown("*Vyber potraviny, které nechceš:*")
dislikes = st.sidebar.multiselect(
    "Nechci jíst...",
    DISLIKES,
    default=[],
    help="Vyloučíme recepty obsahující tyto ingredience"
)

st.sidebar.divider()

# 3. Alergie
st.sidebar.subheader("⚠️ Alergie")
allergies = st.sidebar.multiselect(
    "Máš alergii na...",
    ALLERGENS,
    default=[],
    help="Vyfiltrujeme recepty s těmito alergeny"
)

st.sidebar.divider()

# 4. Kolik máš času
st.sidebar.subheader("⏱️ Kolik máš času?")

# Možnost: Stejný čas každý den NEBO individuální
time_mode = st.sidebar.radio(
    "Jak chceš nastavit čas?",
    ["Stejný každý den", "Jiný čas pro každý den"],
    help="Vyber si jestli máš stejný čas každý den, nebo se ti to liší"
)

if time_mode == "Stejný každý den":
    time_budget = st.sidebar.select_slider(
        "Kolik minut na přípravu?",
        options=["15-25", "20-45", "30-60", "30-120"],
        value="20-45"
    )
    daily_time_budgets = None
else:
    st.sidebar.caption("💡 Nastav čas pro každý den:")
    days_cz = {
        'monday': 'Pondělí',
        'tuesday': 'Úterý',
        'wednesday': 'Středa',
        'thursday': 'Čtvrtek',
        'friday': 'Pátek',
        'saturday': 'Sobota',
        'sunday': 'Neděle'
    }

    daily_time_budgets = {}
    for day_en, day_cz in days_cz.items():
        emoji = "⚡" if day_en in ['monday', 'tuesday', 'wednesday', 'thursday'] else "🕐"
        daily_time_budgets[day_en] = st.sidebar.selectbox(
            f"{emoji} {day_cz}",
            ["15-25", "20-45", "30-60", "30-120"],
            index=1,  # default 20-45
            key=f"time_{day_en}"
        )
    time_budget = "20-45"  # fallback

st.sidebar.caption("💡 Rychlá jídla = do 30 minut")

st.sidebar.divider()

# 5. Jaké máš vybavení
st.sidebar.subheader("🔧 Jaké máš vybavení?")
st.sidebar.markdown("*Recepty použijí jen to, co máš:*")
equipment = st.sidebar.multiselect(
    "Dostupné vybavení",
    EQUIPMENT,
    default=["Trouba"],
    help="Vybereme jen recepty, které můžeš s tímto vybavením připravit"
)

st.sidebar.divider()

# 6. Co už máš doma
st.sidebar.subheader("🏠 Co už máš doma?")
st.sidebar.markdown("*Odečteme z nákupního seznamu:*")
have_at_home = st.sidebar.multiselect(
    "Odškrtni co máš",
    COMMON_PANTRY_ITEMS,
    default=[],
    help="Vyber ingredience, které už máš doma - nebudou v nákupním seznamu. Ušetříš peníze!"
)

st.sidebar.divider()

# Generate button
if st.sidebar.button("🚀 Generuj Jídelníček", type="primary", use_container_width=True):

    # Prepare preferences - vše česky
    # "Mám doma" už je list z multiselect
    have_at_home_list = [item.lower() for item in have_at_home]

    preferences = {
        "household_size": household_size,
        "allergies": [a.lower() for a in allergies],
        "likes": [l.lower() for l in likes],
        "time_budget": time_budget,
        "daily_time_budgets": daily_time_budgets,  # None pokud stejný čas, jinak dict
        "price_budget": "30-70",
        "dislikes": [d.lower() for d in dislikes],
        "kid_friendly_required": "jídla pro děti" in [l.lower() for l in likes],
        "equipment": [e.lower() for e in equipment],
        "num_weeks": num_weeks,
        "have_at_home": have_at_home_list
    }

    # Show loading spinner
    with st.spinner("🤖 Generuji tvůj personalizovaný jídelníček..."):
        try:
            # Generate meal plan
            meal_plan = generate_meal_plan(preferences)

            # Save to session state
            st.session_state.meal_plan = meal_plan
            st.session_state.preferences = preferences

            # Load all filtered recipes for swap functionality
            from meal_planner import load_recipes, filter_recipes, load_desserts
            all_recipes = load_recipes()
            filtered = filter_recipes(all_recipes, preferences)
            st.session_state.filtered_recipes = filtered
            st.session_state.all_desserts = load_desserts()

            # Generate PDF
            try:
                pdf_path = generate_pdf(meal_plan, "generated_meal_plan.pdf")
                st.session_state.pdf_path = pdf_path
            except Exception as pdf_error:
                st.warning(f"⚠️ PDF se nepodařilo vygenerovat: {str(pdf_error)}")
                st.info("💡 Recepty a nákupní seznam jsou k dispozici níže na stránce")

            st.success("✅ Jídelníček vygenerován!")

        except json.JSONDecodeError as je:
            st.error(f"❌ Chyba při načítání dat: {str(je)}")
            st.error(f"📍 Pozice chyby: řádek {je.lineno}, sloupec {je.colno}")
            st.info("💡 Zkus aplikaci restartovat (F5) nebo kontaktuj podporu")

        except ValueError as ve:
            st.error(f"❌ {str(ve)}")
            st.info("💡 Tip: Zkus upravit své preference (např. rozšířit časový budget nebo odstranit některá omezení)")

        except Exception as e:
            st.error(f"❌ Neočekávaná chyba: {str(e)}")
            import traceback
            with st.expander("🔍 Detaily chyby (pro ladění)"):
                st.code(traceback.format_exc())
            st.info("💡 Zkus aplikaci restartovat (F5) nebo změnit preference")

# Display results
if "meal_plan" in st.session_state:
    meal_plan = st.session_state.meal_plan

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Celková cena týdne", f"{meal_plan['total_cost_czk']} Kč")
    with col2:
        st.metric("📊 Cena na porci", f"{meal_plan['cost_per_portion_czk']} Kč")
    with col3:
        total_portions = sum(r['servings'] for r in meal_plan['meals'].values())
        st.metric("🍽️ Celkem porcí", f"{total_portions}")
    with col4:
        if 'ingredient_stats' in meal_plan:
            reuse_pct = meal_plan['ingredient_stats']['reuse_percentage']
            st.metric(
                "♻️ Opakované ingredience",
                f"{reuse_pct}%",
                help="Kolik ingrediencí používáš vícekrát = menší nákup!"
            )

    # Zobraz úspory z opakování ingrediencí (weighted optimization)
    if 'ingredient_stats' in meal_plan and meal_plan['ingredient_stats']['reuse_percentage'] > 0:
        stats = meal_plan['ingredient_stats']

        # Základní info
        success_msg = (
            f"✨ **Smart optimalizace:** Tvůj jídelníček využívá {stats['reused_count']} "
            f"sdílených ingrediencí! "
        )

        # Přidej weighted score a savings pokud jsou k dispozici
        if 'weighted_reuse_score' in stats and 'estimated_savings_czk' in stats:
            success_msg += (
                f"\n\n💰 **Weighted overlap skóre:** {stats['weighted_reuse_score']} bodů "
                f"(dražší ingredience jako maso mají vyšší váhu)\n\n"
                f"💸 **Odhadované úspory:** ~{stats['estimated_savings_czk']} Kč díky sdílení ingrediencí"
            )
        else:
            success_msg += "Koupíš méně, ušetříš čas i peníze."

        st.success(success_msg)

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

    # Weekly menu (multiple weeks support)
    st.header("📅 Menu")
    st.info("💡 **Tip:** Nelíbí se ti nějaký recept? Klikni na tlačítko **🔄 Vyměň** vedle názvu dne a vygeneruje se ti jiný recept!")

    days_czech = {
        'monday': 'Pondělí',
        'tuesday': 'Úterý',
        'wednesday': 'Středa',
        'thursday': 'Čtvrtek',
        'friday': 'Pátek',
        'saturday': 'Sobota',
        'sunday': 'Neděle'
    }

    # Display recipes for all weeks
    num_weeks = meal_plan.get('num_weeks', 1)
    weeks = meal_plan.get('weeks', [meal_plan.get('meals', {})])

    for week_idx, week_meals in enumerate(weeks, 1):
        if num_weeks > 1:
            st.subheader(f"🗓️ Týden {week_idx}")

        for day_en, day_cz in days_czech.items():
            if day_en not in week_meals:
                continue

            recipe = week_meals[day_en]

            # Create columns for recipe title and swap button
            col_title, col_swap = st.columns([4, 1])

            with col_title:
                expander_title = f"**{day_cz}**: {recipe['name']} ({recipe['time_minutes']} min, {recipe['price_per_portion_czk']} Kč/porce)"

            with col_swap:
                swap_key = f"swap_{week_idx}_{day_en}"
                if st.button("🔄 Vyměň", key=swap_key, help="Vyměnit za jiný recept"):
                    # Get current week and day preferences
                    from meal_planner import get_main_protein, generate_shopping_list, calculate_total_cost
                    from collections import defaultdict

                    # Get alternatives
                    if 'filtered_recipes' in st.session_state:
                        filtered = st.session_state.filtered_recipes

                        # Get used recipe IDs in this week
                        used_ids = [r['id'] for r in week_meals.values() if isinstance(r, dict) and 'id' in r]

                        # Count proteins in this week (excluding current day)
                        protein_counts = defaultdict(int)
                        for d, r in week_meals.items():
                            if d != day_en and d != 'sunday_dessert' and isinstance(r, dict):
                                protein = get_main_protein(r)
                                protein_counts[protein] += 1

                        # Filter alternatives: not used, respects protein diversity
                        alternatives = []
                        for r in filtered:
                            if r['id'] in used_ids:
                                continue

                            # Check time budget for this day
                            prefs = st.session_state.preferences
                            daily_budgets = prefs.get('daily_time_budgets')
                            if daily_budgets and day_en in daily_budgets:
                                time_range = daily_budgets[day_en]
                            else:
                                time_range = prefs['time_budget']

                            time_min, time_max = map(int, time_range.split('-'))
                            if not (time_min <= r['time_minutes'] <= time_max):
                                continue

                            # Check protein diversity (max 3x)
                            r_protein = get_main_protein(r)
                            if protein_counts[r_protein] >= 3:
                                continue

                            alternatives.append(r)

                        if alternatives:
                            import random
                            new_recipe = random.choice(alternatives)

                            # Update meal plan
                            st.session_state.meal_plan['weeks'][week_idx - 1][day_en] = new_recipe

                            # Re-generate shopping list and costs
                            weeks_with_desserts = st.session_state.meal_plan['weeks']
                            have_at_home = st.session_state.preferences.get('have_at_home', [])

                            shopping_result = generate_shopping_list(weeks_with_desserts, have_at_home)
                            total_cost = calculate_total_cost(weeks_with_desserts)
                            total_portions = sum(sum(r['servings'] for r in w.values() if isinstance(r, dict)) for w in weeks_with_desserts)

                            st.session_state.meal_plan['shopping_list'] = shopping_result['shopping_list']
                            st.session_state.meal_plan['shopping_details'] = shopping_result
                            st.session_state.meal_plan['total_cost_czk'] = total_cost
                            st.session_state.meal_plan['cost_per_portion_czk'] = round(total_cost / total_portions, 1) if total_portions > 0 else 0

                            st.rerun()
                        else:
                            st.warning("⚠️ Nenalezeny žádné alternativní recepty s těmito preferencemi")

            with st.expander(expander_title):

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📝 Ingredience")
                    for ingredient in recipe['ingredients']:
                        st.markdown(f"- {ingredient['name']} - {ingredient['amount']}")

                    st.subheader("👨‍🍳 Postup")
                    for i, step in enumerate(recipe['steps'], 1):
                        st.markdown(f"{i}. {step}")

                with col2:
                    # Zobraz celkový čas nebo rozdělení prep/cook
                    if 'prep_time_minutes' in recipe and 'cook_time_minutes' in recipe:
                        st.metric("⏱️ Celkový čas", f"{recipe['time_minutes']} min")
                        st.caption(f"🔪 Příprava: {recipe['prep_time_minutes']} min | 🍳 Vaření: {recipe['cook_time_minutes']} min")
                    else:
                        st.metric("⏱️ Čas", f"{recipe['time_minutes']} min")

                    st.metric("📊 Obtížnost", recipe['difficulty'])
                    st.metric("👥 Porce", recipe['servings'])
                    st.metric("💰 Cena/porce", f"{recipe['price_per_portion_czk']} Kč")

                    if recipe.get('allergens'):
                        # Translate allergens to Czech for display
                        allergens_cz = []
                        allergen_display_map = {
                            "gluten": "lepek",
                            "shellfish": "korýši",
                            "eggs": "vejce",
                            "fish": "ryby",
                            "peanuts": "arašídy",
                            "soy": "sója",
                            "dairy": "mléko",
                            "nuts": "ořechy",
                            "celery": "celer",
                            "hořčice": "mustard",
                            "sesame": "sezam",
                            "sulfites": "oxid siřičitý",
                            "lupin": "vlčí bob",
                            "molluscs": "měkkýši"
                        }
                        for allergen in recipe['allergens']:
                            allergens_cz.append(allergen_display_map.get(allergen.lower(), allergen))
                        st.warning(f"⚠️ Alergeny: {', '.join(allergens_cz)}")

        # Po všech dnech týdne zobraz dezert (pokud existuje)
        if 'sunday_dessert' in week_meals:
            dessert = week_meals['sunday_dessert']

            # Create columns for dessert title and swap button
            col_title_d, col_swap_d = st.columns([4, 1])

            with col_title_d:
                dessert_title = f"🍰 **Dezert k neděli**: {dessert['name']} ({dessert['time_minutes']} min, {dessert['price_per_portion_czk']} Kč/porce)"

            with col_swap_d:
                swap_dessert_key = f"swap_dessert_{week_idx}"
                if st.button("🔄 Vyměň", key=swap_dessert_key, help="Vyměnit za jiný dezert"):
                    if 'all_desserts' in st.session_state:
                        all_desserts = st.session_state.all_desserts

                        # Get used dessert IDs across all weeks
                        used_dessert_ids = []
                        for w in st.session_state.meal_plan['weeks']:
                            if 'sunday_dessert' in w:
                                used_dessert_ids.append(w['sunday_dessert']['id'])

                        # Filter alternatives (not used this week)
                        current_dessert_id = dessert['id']
                        used_dessert_ids_except_current = [d_id for d_id in used_dessert_ids if d_id != current_dessert_id]

                        alternatives = [d for d in all_desserts if d['id'] not in used_dessert_ids_except_current]

                        if alternatives:
                            import random
                            new_dessert = random.choice(alternatives)

                            # Update meal plan
                            from meal_planner import generate_shopping_list, calculate_total_cost
                            st.session_state.meal_plan['weeks'][week_idx - 1]['sunday_dessert'] = new_dessert

                            # Re-generate shopping list and costs
                            weeks_with_desserts = st.session_state.meal_plan['weeks']
                            have_at_home = st.session_state.preferences.get('have_at_home', [])

                            shopping_result = generate_shopping_list(weeks_with_desserts, have_at_home)
                            total_cost = calculate_total_cost(weeks_with_desserts)
                            total_portions = sum(sum(r['servings'] for r in w.values() if isinstance(r, dict)) for w in weeks_with_desserts)

                            st.session_state.meal_plan['shopping_list'] = shopping_result['shopping_list']
                            st.session_state.meal_plan['shopping_details'] = shopping_result
                            st.session_state.meal_plan['total_cost_czk'] = total_cost
                            st.session_state.meal_plan['cost_per_portion_czk'] = round(total_cost / total_portions, 1) if total_portions > 0 else 0

                            st.rerun()
                        else:
                            st.warning("⚠️ Nenalezeny žádné alternativní dezerty")

            with st.expander(dessert_title):

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📝 Ingredience")
                    for ingredient in dessert['ingredients']:
                        st.markdown(f"- {ingredient['name']} - {ingredient['amount']}")

                    st.subheader("👨‍🍳 Postup")
                    for i, step in enumerate(dessert['steps'], 1):
                        st.markdown(f"{i}. {step}")

                with col2:
                    st.metric("⏱️ Čas", f"{dessert['time_minutes']} min")
                    st.metric("📊 Obtížnost", dessert['difficulty'])
                    st.metric("👥 Porce", dessert['servings'])
                    st.metric("💰 Cena/porce", f"{dessert['price_per_portion_czk']} Kč")

                    if dessert.get('kid_friendly'):
                        st.success("👶 Vhodné pro děti")

                    # Zobraz alergeny pokud existují
                    if dessert.get('allergens'):
                        # Alergeny v dezertech jsou jako čísla, převedeme je
                        allergen_number_map = {
                            1: "lepek",
                            3: "vejce",
                            7: "mléko",
                            8: "ořechy"
                        }
                        allergens_cz = []
                        for allergen in dessert['allergens']:
                            if isinstance(allergen, int):
                                allergens_cz.append(allergen_number_map.get(allergen, str(allergen)))
                            else:
                                allergens_cz.append(str(allergen))
                        st.warning(f"⚠️ Alergeny: {', '.join(allergens_cz)}")

    st.divider()

    # Shopping list
    st.header("🛒 Nákupní Seznam")

    category_names = {
        'maso': '🥩 Maso',
        'ryby': '🐟 Ryby',
        'zelenina': '🥬 Zelenina & Ovoce',
        'vegetables': '🥬 Zelenina & Ovoce',
        'mléčné': '🥛 Mléčné Výrobky',
        'dairy': '🥛 Mléčné Výrobky',
        'trvanlivé': '🥫 Trvanlivé',
        'pantry': '🥫 Trvanlivé',
        'ostatní': '📦 Ostatní'
    }

    # Zobraz "Mám doma" sekci pokud existuje
    if 'shopping_details' in meal_plan and meal_plan['shopping_details'].get('have_at_home_items'):
        with st.expander("✅ Mám doma (nepotřebuješ koupit)", expanded=False):
            for item in meal_plan['shopping_details']['have_at_home_items']:
                st.write(f"- {item}")

    cols = st.columns(2)

    for i, (category, items) in enumerate(meal_plan['shopping_list'].items()):
        with cols[i % 2]:
            st.subheader(category_names.get(category, category))
            for item in items:
                st.checkbox(item, key=f"{category}_{item}")

    st.divider()

    # Zobraz info o balení a celkovém počtu
    if 'shopping_details' in meal_plan:
        total_packages = meal_plan['shopping_details'].get('total_packages', 0)
        st.info(f"📦 Celkem balení k nákupu: **{total_packages}**")

    st.success(f"💰 Odhadovaná cena nákupu: **{meal_plan['total_cost_czk']} Kč**")

    # Zobraz zbytky a tipy pokud existují
    if 'shopping_details' in meal_plan and meal_plan['shopping_details'].get('leftovers'):
        with st.expander("💡 Tipy na využití zbytků", expanded=False):
            st.markdown("Při nákupu v balíčcích ti zbydou tyto ingredience:")

            for leftover in meal_plan['shopping_details']['leftovers']:
                tip_text = f"**{leftover['ingredient']}**: zbytek ~{leftover['leftover']}"
                if 'tip' in leftover:
                    tip_text += f"\n- 💡 {leftover['tip']}"
                st.markdown(tip_text)

else:
    # Welcome message - user friendly pro české matky
    st.success("👋 Vítej! Pomohu ti naplánovat večeře na celý týden.")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ### ✨ Jak to funguje?

        **Je to jednoduché:**

        1. **👈 V levém menu vyber** co máš rád a co nechceš
           - Kolik máš času na vaření?
           - Jaká jídla máš rád? (těstoviny, tradiční česká...)
           - Co nechceš jíst? (ryby, vepřové, houby...)
           - Máš nějaké alergie?

        2. **🚀 Klikni "Generuj Jídelníček"**

        3. **📥 Dostaneš:**
           - 7 receptů na celý týden (pondělí-neděle)
           - Nákupní seznam (co koupit)
           - PDF ke stažení (pro mobil nebo vytisknutí)
           - Celkovou cenu

        ### 💡 Proč je to skvělé?

        - ✅ **Ušetříš čas** - Žádné plánování "co dnes uvařím?"
        - ✅ **Ušetříš peníze** - Přesný nákupní seznam, nic se neplýtvá
        - ✅ **Zdravější jídlo** - Vyvážené menu podle tvých preferencí
        - ✅ **Méně stresu** - Víš předem, co budeš vařit

        ---

        ### 📊 Jaká jídla nabízíme?

        | Kategorie | Příklady |
        |-----------|----------|
        | 🍝 **Těstoviny** | Špagety carbonara, lasagne, penne s kuřetem |
        | 🇨🇿 **Tradiční česká** | Guláš, svíčková, řízek s bramborovým salátem |
        | ⚡ **Rychlá jídla** | Smažený sýr, kuřecí stir-fry (do 30 min) |
        | 🍕 **Rodinná klasika** | Pizza, palačinky, bramboráky |
        | 🍲 **Polévky** | Rajčatová, česnečka, kuřecí vývar, hráškový krém |
        | 🥗 **Vegetariánské** | Smažený sýr, bramboráky, zapečené těstoviny |
        | 🌱 **Veganské** | Zeleninové kari, fazolový guláš, vegan lasagne |

        ---

        **💰 Ceny:** Průměrně 30-60 Kč na porci
        **⏱️ Čas:** Od 15 do 120 minut (ty si vybereš)
        **👶 Pro děti:** Všechna jídla kid-friendly (pokud zaškrtneš)
        """)

    with col2:
        st.info("""
        ### 🎯 Začni tady:

        1. Otevři levé menu 👈
        2. Vyplň preference
        3. Klikni na zelené tlačítko
        4. Hotovo! ✨
        """)

        st.markdown("---")

        st.markdown("""
        ### 💬 Tip pro maminky:

        **Nemáš čas?**
        Vyber "Rychlá jídla" a časový budget "15-25 min"

        **Děti jsou vybíravé?**
        Zaškrtni "Jen jídla vhodná pro děti" a vyluč co nejedí

        **Chceš ušetřit?**
        Zkus "Tradiční česká" - levné a chutné!
        """)

    st.divider()

    # Statistiky pro důvěryhodnost
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🍽️ Receptů v databázi", "40+", help="Stále přidáváme nové")
    with col2:
        st.metric("⏱️ Průměrný čas úspory", "3 hodiny/týden", help="Díky plánování")
    with col3:
        st.metric("💰 Průměrná cena", "45 Kč/porce", help="Včetně všech ingrediencí")
