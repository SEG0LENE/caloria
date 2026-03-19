import streamlit as st
import openai
import json
import datetime
import pandas as pd
import plotly.express as px
import os
from nutrition import analyser_repas, conseil_du_jour

st.set_page_config(page_title="CalorIA", page_icon="🍽", layout="wide")

HISTORIQUE_FILE = "historique.json"

def charger_historique():
    if os.path.exists(HISTORIQUE_FILE):
        with open(HISTORIQUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder_historique(data):
    with open(HISTORIQUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def historique_par_jour(historique):
    jours = {}
    for r in historique:
        d = r.get("date", "")
        jours[d] = jours.get(d, 0) + r.get("total_calories", 0)
    rows = [{"date": d, "calories": cal} for d, cal in sorted(jours.items())[-7:]]
    return pd.DataFrame(rows)

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "historique" not in st.session_state:
    st.session_state.historique = charger_historique()

with st.sidebar:
    st.title("CalorIA 🍽")
    objectif = st.number_input("Objectif calories/jour", value=1800, step=50, min_value=1000, max_value=4000)

today = datetime.date.today().isoformat()
repas_today = [r for r in st.session_state.historique if r.get("date") == today]
total_today = sum(r.get("total_calories", 0) for r in repas_today)
pct = min(int(total_today / objectif * 100), 100)

st.title(f"CalorIA — {datetime.date.today().strftime('%A %d %B %Y')}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Consommé", f"{total_today} kcal")
c2.metric("Restant", f"{max(objectif - total_today, 0)} kcal")
c3.metric("Progression", f"{pct}%")
c4.metric("Repas enregistrés", len(repas_today))
st.progress(pct / 100)

st.divider()
col_rec, col_tip = st.columns(2)

with col_rec:
    st.subheader("🍽 Décrire un repas")
    texte = st.text_area("Décris ce que tu as mangé", placeholder="Ex: j'ai mangé des pâtes bolognaise avec du parmesan et un verre de rouge")
    if st.button("Analyser", type="primary", use_container_width=True):
        if texte.strip():
            with st.spinner("Analyse nutritionnelle..."):
                result = analyser_repas(client, texte)
            st.success(f"~{result['total_calories']} kcal — Fiabilité : {result.get('fiabilite','?')}")
            df = pd.DataFrame(result.get("aliments", []))
            if not df.empty:
                st.dataframe(df, hide_index=True, use_container_width=True)
            st.caption(result.get("hypotheses", ""))
            result["date"] = today
            result["texte"] = texte
            st.session_state.historique.append(result)
            sauvegarder_historique(st.session_state.historique)
            st.rerun()
        else:
            st.warning("Décris d'abord ce que tu as mangé !")

with col_tip:
    st.subheader("💡 Conseil du jour")
    if st.button("Générer un conseil IA", use_container_width=True):
        with st.spinner("Analyse..."):
            conseil = conseil_du_jour(client, repas_today, objectif)
        st.info(conseil)

st.divider()
st.subheader("📊 Évolution 7 jours")
df_week = historique_par_jour(st.session_state.historique)
if not df_week.empty:
    df_week["statut"] = df_week["calories"].apply(
        lambda c: "Dans l'objectif" if c <= objectif else ("Léger dépassement" if c <= objectif * 1.1 else "Dépassement")
    )
    fig = px.bar(df_week, x="date", y="calories", color="statut",
        color_discrete_map={"Dans l'objectif": "#1D9E75", "Léger dépassement": "#BA7517", "Dépassement": "#E24B4A"})
    fig.add_hline(y=objectif, line_dash="dot", line_color="#888", annotation_text=f"Objectif {objectif} kcal")
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🕐 Repas d'aujourd'hui")
for repas in reversed(repas_today):
    with st.expander(f"~{repas.get('total_calories','?')} kcal — {repas.get('texte','')[:70]}"):
        st.dataframe(pd.DataFrame(repas.get("aliments", [])), hide_index=True, use_container_width=True)
        st.caption(repas.get("hypotheses", ""))