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
            st.markdown(f"**{campaign}** — Vybráno: **{fmt_czk(raised)}** z **{fmt_czk(goal)}** *(Zbývá: {fmt_czk(remaining)})*")
            st.progress(pct)
        with c_col2:
            if raised >= goal and goal > 0:
                st.success("🎉 Cíl splněn!")
            else:
                st.info(f"{pct*100:.1f} % splněno")

    # Vizuální srovnání grafem
    if chart_data:
        st.markdown("---")
        st.subheader("📊 Vizuální srovnání kampaní")
        df_chart = pd.DataFrame(chart_data).set_index("Kampaň")
        st.bar_chart(df_chart)

with tab2:
    st.subheader("➕ Vložit novou platbu ze Slevomatu")
    if not st.session_state.goals:
        st.warning("Nejdříve přidejte alespoň jednu kampaň v levém menu!")
    else:
        with st.form("add_payment_form"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                selected_camp = st.selectbox("Kampaň / Akce", list(st.session_state.goals.keys()))
            with col_b:
                doc_label = st.text_input("Číslo dokladu / Poznámka", value="FVSP-XXXXXX/2026")
            with col_c:
                amount = st.number_input("Částka (Kč)", min_value=0.0, step=100.0, format="%.2f")
                
            submitted = st.form_submit_button("Uložit platbu")
            if submitted and amount > 0:
                new_entry = pd.DataFrame([{"Akce": selected_camp, "Datum / Doklad": doc_label, "Částka (Kč)": amount}])
                st.session_state.payments = pd.concat([st.session_state.payments, new_entry], ignore_index=True)
                save_payments()
                st.success("Platba byla úspěšně přidána a uložena!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Seznam a úprava evidovaných plateb")
    st.caption("💡 Záznamy můžete přímo v tabulce upravovat nebo mazat (označením řádku a stisknutím klávesy Delete).")
    
    edited_df = st.data_editor(
        st.session_state.payments,
        use_container_width=True,
        num_rows="dynamic",
        key="payments_editor"
    )
    
    # Detekce zmen změn v editoru
    if not edited_df.equals(st.session_state.payments):
        st.session_state.payments = edited_df
        save_payments()
        st.rerun()

with tab3:
    st.subheader("📥 Export dat")
    
    summary_data = []
    for campaign, goal in st.session_state.goals.items():
        camp_df = st.session_state.payments[st.session_state.payments["Akce"] == campaign] if not st.session_state.payments.empty else pd.DataFrame()
        raised = camp_df["Částka (Kč)"].sum() if not camp_df.empty else 0.0
        remaining = max(0.0, goal - raised)
        pct = (raised / goal * 100) if goal > 0 else 0.0
        summary_data.append({
            "Kampaň": campaign,
            "Cílová částka (Kč)": goal,
            "Vybráno (Kč)": raised,
            "Zbývá (Kč)": remaining,
            "Splněno (%)": round(pct, 2)
        })
    df_summary = pd.DataFrame(summary_data)
    
    st.markdown("#### Souhrnný přehled cílů")
    st.dataframe(df_summary, use_container_width=True)
    
  # sep=';' rozstrká data do samostatných buněk v českém Excelu
    # 'utf-8-sig' zajistí správné zobrazení češtiny (háčky/čárky)
    csv_data = df_summary.to_csv(index=False, sep=';').encode('utf-8-sig')
