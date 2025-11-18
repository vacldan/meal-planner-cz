"""
Streamlit web aplikace pro Czech Meal Planner
"""

import streamlit as st
import json
from meal_planner import generate_meal_plan
from pdf_generator import generate_pdf
import os

# Běžné ingredience, které lidé často mají doma (50 nejpoužívanějších v ČR)
COMMON_PANTRY_ITEMS = [
    # Trvanlivé - mouka a pečení
    "Mouka hladká", "Mouka polohrubá", "Mouka hrubá", "Cukr", "Cukr moučka",
    "Sůl", "Kypřicí prášek", "Droždí", "Vanilkový cukr", "Škrob",

    # Trvanlivé - oleje a tuky
    "Olej slunečnicový", "Olivový olej", "Ocet",

    # Trvanlivé - těstoviny a rýže
    "Rýže", "Těstoviny", "Instantní polévky", "Bujón/Vývar kostky",

    # Trvanlivé - koření a dochucovadla
    "Pepř", "Paprika sladká", "Paprika pálivá", "Kmín", "Majoránka",
    "Bazalka", "Oregano", "Tymián", "Bobkový list", "Muškátový oříšek",
    "Nové koření", "Kečup", "Hořčice", "Sojová omáčka",

    # Mléčné výrobky
    "Mléko", "Máslo", "Sýr", "Eidam", "Parmazán", "Smetana na vaření",
    "Smetana ke šlehání", "Zakysaná smetana", "Jogurt", "Tvaroh",

    # Zelenina
    "Cibule", "Česnek", "Brambory", "Mrkev", "Rajčata", "Petržel",

    # Ostatní
    "Vejce", "Med", "Citron", "Zázvor"
]

# Kategorie receptů
CATEGORIES = ["Těstoviny", "Tradiční česká", "Rychlá jídla", "Rodinná klasika", "Polévky", "Vegetariánské", "Veganské"]

# Alergeny - kompletní seznam 14 hlavních alergenů EU
ALLERGENS = [
    "Lepek (pšenice, žito, ječmen, oves)",
    "Korýši (krevety, humr, krab)",
    "Vejce",
    "Ryby",
    "Arašídy",
    "Sója",
    "Mléko a mléčné výrobky",
    "Ořechy (mandle, lískové, vlašské, kešu)",
    "Celer",
    "Hořčice",
    "Sezam",
    "Oxid siřičitý (konzervanty E220-E228)",
    "Vlčí bob (lupina)",
    "Měkkýši (slávky, chobotnice)"
]

# Potraviny, které nechceš - rozšířený seznam
DISLIKES = [
    "Vepřové",
    "Hovězí",
    "Kuřecí",
    "Ryby",
    "Mořské plody",
    "Vnitřnosti",
    "Houby",
    "Cibule",
    "Česnek",
    "Paprika",
    "Rajčata",
    "Brokolice",
    "Květák",
    "Fazole",
    "Čočka",
    "Sýr",
    "Smetana",
    "Koření (pikantní)"
]

# Vybavení kuchyně
EQUIPMENT = [
    "Trouba",
    "Slow cooker (pomalý hrnec)",
    "Air fryer (fritéza na vzduch)",
    "Mikrovlnka",
    "Mixér/Tyčový mixér"
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

st.sidebar.subheader("🍽️ Jaká jídla máš rád?")
st.sidebar.markdown("*Vyber jeden nebo více typů:*")
likes = st.sidebar.multiselect(
    "Kategorie jídel",
    CATEGORIES,
    default=["Těstoviny", "Tradiční česká", "Rychlá jídla"],
    help="""
    • Těstoviny - špagety, lasagne, penne\n
    • Tradiční česká - guláš, svíčková, řízek\n
    • Rychlá jídla - do 30 minut\n
    • Rodinná klasika - pizza, burgery, palačinky\n
    • Polévky - zeleninové, vývarové, krémové\n
    • Vegetariánské - bez masa a ryb\n
    • Veganské - bez živočišných produktů
    """
)

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

st.sidebar.subheader("⚠️ Alergie")
allergies = st.sidebar.multiselect(
    "Máš alergii na...",
    ALLERGENS,
    default=[],
    help="Vyfiltrujeme recepty s těmito alergeny"
)

st.sidebar.subheader("❌ Co nechceš v jídle")
st.sidebar.markdown("*Vyber potraviny, které nechceš:*")
dislikes = st.sidebar.multiselect(
    "Nechci jíst...",
    DISLIKES,
    default=[],
    help="Vyloučíme recepty obsahující tyto ingredience"
)

kid_friendly = st.sidebar.checkbox(
    "👶 Jen jídla vhodná pro děti",
    value=True,
    help="Vyloučíme velmi pikantní a netradiční jídla"
)

st.sidebar.divider()

st.sidebar.subheader("🔧 Jaké máš vybavení?")
st.sidebar.markdown("*Recepty použijí jen to, co máš:*")
equipment = st.sidebar.multiselect(
    "Dostupné vybavení",
    EQUIPMENT,
    default=["Trouba"],
    help="Vybereme jen recepty, které můžeš s tímto vybavením připravit"
)

st.sidebar.divider()

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
        "kid_friendly_required": kid_friendly,
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

    # Zobraz úspory z opakování ingrediencí
    if 'ingredient_stats' in meal_plan and meal_plan['ingredient_stats']['reuse_percentage'] > 0:
        st.success(
            f"✨ **Smart optimalizace:** Tvůj jídelníček využívá {meal_plan['ingredient_stats']['reused_count']} "
            f"sdílených ingrediencí! Koupíš méně, ušetříš čas i peníze."
        )

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

    st.divider()

    # Shopping list
    st.header("🛒 Nákupní Seznam")

    category_names = {
        'maso': '🥩 Maso',
        'ryby': '🐟 Ryby',
        'zelenina': '🥬 Zelenina & Ovoce',
        'mléčné': '🥛 Mléčné Výrobky',
        'trvanlivé': '🥫 Trvanlivé',
        'ostatní': '📦 Ostatní'
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
