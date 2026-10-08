import streamlit as st
import pandas as pd
import json
import os

# Page configuration
st.set_page_config(page_title="Slevomat Dashboard", page_icon="🕯️", layout="wide")

# Soubory pro trvalé ukládání dat
GOALS_FILE = "goals.json"
PAYMENTS_FILE = "payments.csv"

# --- POMOCNÉ FUNKCE PRO UKLÁDÁNÍ A NAČÍTÁNÍ ---
def load_data():
    # Načtení cílů
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            goals = json.load(f)
    else:
        goals = {
            "Jen tak (celoroční)": 15436.0,
            "Podzim": 17643.0,
            "Vánoce": 25000.0
        }

    # Načtení plateb
    if os.path.exists(PAYMENTS_FILE):
        payments = pd.read_csv(PAYMENTS_FILE)
    else:
        payments = pd.DataFrame([
            {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "FVSP-131966/2026 (21.8.)", "Částka (Kč)": 536.35},
            {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "FVSP-137120/2026 (2.9.)", "Částka (Kč)": 265.00},
            {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "FVSP-142249/2026 (11.9.)", "Částka (Kč)": 352.42},
            {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "FVSP-147112/2026 (21.9.)", "Částka (Kč)": 90.45},
            {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "FVSP-152319/2026 (2.10.)", "Částka (Kč)": 768.06},
            {"Akce": "Podzim", "Datum / Doklad": "FVSP-152318/2026 (2.10.)", "Částka (Kč)": 973.72},
        ])
    return goals, payments

def save_goals():
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.goals, f, ensure_ascii=False, indent=4)

def save_payments():
    st.session_state.payments.to_csv(PAYMENTS_FILE, index=False)

def fmt_czk(amount):
    """Formátování částky na český tvar (1 234,56 Kč)"""
    return f"{amount:,.2f} Kč".replace(",", " ").replace(".", ",")

# --- INICIALIZACE STAVU ---
if "goals" not in st.session_state or "payments" not in st.session_state:
    goals, payments = load_data()
    st.session_state.goals = goals
    st.session_state.payments = payments

# --- HLAVIČKA ---
st.title("🕯️ Slevomat Účtování & Sledování Cílů")
st.markdown("Přehledná aplikace pro evidenci vyúčtování ze Slevomatu a plnění prodejních cílů.")

# --- SIDEBAR: SPRÁVA KAMPANÍ ---
st.sidebar.header("🎯 Nastavení cílů kampaní")

for campaign in list(st.session_state.goals.keys()):
    col_g1, col_g2 = st.sidebar.columns([4, 1])
    with col_g1:
        new_goal = st.number_input(
            f"{campaign} (Kč)",
            value=float(st.session_state.goals[campaign]),
            step=500.0,
            key=f"goal_{campaign}"
        )
        if new_goal != st.session_state.goals[campaign]:
            st.session_state.goals[campaign] = new_goal
            save_goals()
            st.rerun()
    with col_g2:
        st.write("") # Odsazení
        if st.button("❌", key=f"del_{campaign}", help=f"Smazat kampaň {campaign}"):
            del st.session_state.goals[campaign]
            save_goals()
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("➕ Přidat novou kampaň")
new_campaign_name = st.sidebar.text_input("Název nové kampaně")
new_campaign_goal = st.sidebar.number_input("Cílová částka (Kč)", min_value=0.0, step=1000.0)
if st.sidebar.button("Přidat kampaň"):
    if new_campaign_name and new_campaign_name not in st.session_state.goals:
        st.session_state.goals[new_campaign_name] = new_campaign_goal
        save_goals()
        st.sidebar.success(f"Kampaň '{new_campaign_name}' přidána!")
        st.rerun()

# --- HLAVNÍ OBSAH: 3 ZÁLOŽKY ---
tab1, tab2, tab3 = st.tabs(["📊 Přehled & Cíle", "💰 Správa plateb", "📥 Export & Nastavení"])

with tab1:
    df_p = st.session_state.payments
    
    total_goals = sum(st.session_state.goals.values())
    total_raised = df_p["Částka (Kč)"].sum() if not df_p.empty else 0.0
    total_remaining = max(0.0, total_goals - total_raised)
    overall_progress = (total_raised / total_goals * 100) if total_goals > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Celkový cíl", fmt_czk(total_goals))
    col2.metric("💰 Celkem vybráno", fmt_czk(total_raised))
    col3.metric("⏳ Zbývá vybrat", fmt_czk(total_remaining))
    col4.metric("📈 Celkový pokrok", f"{overall_progress:.1f} %")

    st.markdown("---")
    st.subheader("📈 Pokrok podle jednotlivých kampaní")

    chart_data = []

    for campaign, goal in st.session_state.goals.items():
        camp_df = df_p[df_p["Akce"] == campaign] if not df_p.empty else pd.DataFrame()
        raised = camp_df["Částka (Kč)"].sum() if not camp_df.empty else 0.0
        remaining = max(0.0, goal - raised)
        pct = min(1.0, raised / goal) if goal > 0 else 0.0

        chart_data.append({"Kampaň": campaign, "Vybráno": raised, "Cíl": goal})

        c_col1, c_col2 = st.columns([3, 1])
        with c_col1:
            st.markdown(f"**
