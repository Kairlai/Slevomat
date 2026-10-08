import streamlit as st
import pandas as pd

# Konfigurace stránky
st.set_page_config(page_title="Slevomat Dashboard", page_icon="🕯️", layout="wide")

def fmt_czk(amount):
    """Formátování částky na český tvar (1 234,56 Kč)"""
    return f"{amount:,.2f} Kč".replace(",", " ").replace(".", ",")

# --- INICIALIZACE DATOVÉHO STAVU ---
if "goals" not in st.session_state:
    st.session_state.goals = {
        "Jen tak (celoroční)": 15436.0,
        "Podzim": 17643.0,
        "Vánoce": 0.0
    }

if "payments" not in st.session_state:
    # Přesná data z obrázku
    st.session_state.payments = pd.DataFrame([
        {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "Platba 1", "Částka (Kč)": 1770.94},
        {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "Platba 2", "Částka (Kč)": 208.55},
        {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "Platba 3", "Částka (Kč)": 812.58},
        {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "Platba 4", "Částka (Kč)": 611.00},
        {"Akce": "Jen tak (celoroční)", "Datum / Doklad": "Platba 5", "Částka (Kč)": 1236.65},
        {"Akce": "Podzim", "Datum / Doklad": "Platba 1", "Částka (Kč)": 2245.28},
    ])

# --- HLAVIČKA ---
st.title("🕯️ Slevomat Účtování & Sledování Cílů")
st.markdown("Přehledná aplikace pro evidenci vyúčtování ze Slevomatu a plnění prodejních cílů.")

# --- SIDEBAR: EDITACE CÍLŮ S TLAČÍTKEM ULOŽIT (OPTIMALIZOVÁNO PRO MOBILY) ---
st.sidebar.header("🎯 Nastavení cílů kampaní")

with st.sidebar.form("goals_form"):
    st.write("Upravte cíle a stiskněte tlačítko níže:")
    updated_goals = {}
    
    for campaign, current_goal in st.session_state.goals.items():
        updated_goals[campaign] = st.number_input(
            f"Cíl: {campaign} (Kč)",
            value=float(current_goal),
            min_value=0.0,
            step=500.0,
            key=f"input_goal_{campaign}"
        )
    
    save_goals_submitted = st.form_submit_button("💾 Uložit všechny cíle", use_container_width=True)
    if save_goals_submitted:
        st.session_state.goals = updated_goals
        st.success("Cíle byly úspěšně uloženy!")
        st.rerun()

st.sidebar.markdown("---")

# Správa - Přidání nové kampaně
st.sidebar.subheader("➕ Přidat novou kampaň")
new_campaign_name = st.sidebar.text_input("Název kampaně", key="new_camp_name")
new_campaign_goal = st.sidebar.number_input("Cílová částka (Kč)", min_value=0.0, step=1000.0, key="new_camp_goal")

if st.sidebar.button("➕ Přidat kampaň", use_container_width=True):
    if new_campaign_name and new_campaign_name not in st.session_state.goals:
        st.session_state.goals[new_campaign_name] = new_campaign_goal
        st.sidebar.success(f"Kampaň '{new_campaign_name}' přidána!")
        st.rerun()

# Správa - Smazání kampaně
if st.session_state.goals:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗑️ Smazat kampaň")
    camp_to_delete = st.sidebar.selectbox("Vyberte kampaň ke smazání", ["-- Vyberte --"] + list(st.session_state.goals.keys()))
    if st.sidebar.button("❌ Smazat kampaň", use_container_width=True):
        if camp_to_delete != "-- Vyberte --":
            del st.session_state.goals[camp_to_delete]
            st.sidebar.success(f"Kampaň '{camp_to_delete}' byla smazána!")
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
                doc_label = st.text_input("Číslo dokladu / Poznámka", value="Platba")
            with col_c:
                amount = st.number_input("Částka (Kč)", min_value=0.0, step=100.0, format="%.2f")
                
            submitted = st.form_submit_button("Uložit platbu")
            if submitted and amount > 0:
                new_entry = pd.DataFrame([{"Akce": selected_camp, "Datum / Doklad": doc_label, "Částka (Kč)": amount}])
                st.session_state.payments = pd.concat([st.session_state.payments, new_entry], ignore_index=True)
                st.success("Platba byla úspěšně přidána!")
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Seznam a úprava evidovaných plateb")
    st.caption("💡 Údaje můžete upravovat přímo v tabulce. Nové řádky lze přidat na konci tabulky.")
    
    edited_df = st.data_editor(
        st.session_state.payments,
        use_container_width=True,
        num_rows="dynamic",
        key="payments_editor_grid"
    )
    st.session_state.payments = edited_df

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
    
    # Export pro český Excel (středník + utf-8-sig)
    csv_bytes = df_summary.to_csv(index=False, sep=';').encode('utf-8-sig')
    
    st.download_button(
        label="📄 Stáhnout přehled jako CSV",
        data=csv_bytes,
        file_name="slevomat_prehled_cilu.csv",
        mime="text/csv",
        key="download_csv_main"
    )
