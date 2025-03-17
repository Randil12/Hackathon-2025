import streamlit as st
import pandas as pd
import requests
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="Simulation Réseau KDD Cup 99", layout="wide")

st.title("📡 Simulation des Connexions Réseau - KDD Cup 99")

API_URL = "http://fastapi_app:8080"  # Adresse du serveur FastAPI



# 📌 Mode Playback - Simulation
st.sidebar.header("🎛 Mode Playback")
playback_mode = st.sidebar.radio("Sélectionner un mode :", ["Automatique", "Manuel"])
num_connections = st.sidebar.slider("Nombre de connexions affichées", 10, 200, 50)

# Charger les connexions depuis FastAPI
@st.cache_data
def get_data(n):
    response = requests.get(f"{API_URL}/connections?n={n}")
    return pd.DataFrame(response.json())

df = get_data(num_connections)

# 📌 Lecture progressive du DataFrame en mode "temps réel"
if "index" not in st.session_state:
    st.session_state.index = 0

if playback_mode == "Automatique":
    speed = st.sidebar.slider("Vitesse (secondes par tick)", 0.1, 2.0, 0.5)
    play_button = st.sidebar.button("▶️ Démarrer la Simulation")

if playback_mode == "Manuel":
    st.session_state.index = st.sidebar.slider("Temps (itérations)", 0, len(df) - 1, st.session_state.index, step=1)

def update_index():
    if st.session_state.index < len(df) - 1:
        st.session_state.index += 1

if playback_mode == "Automatique" and play_button:
    while st.session_state.index < len(df) - 1:
        update_index()
        time.sleep(speed)
        st.experimental_rerun()

# 📌 Filtres pour l’analyse
st.sidebar.header("🔎 Filtres")
all_ips = list(set(df["src_ip"].tolist() + df["dst_ip"].tolist()))
selected_src_ip = st.sidebar.selectbox("IP Source", ["Toutes"] + all_ips)
selected_dst_ip = st.sidebar.selectbox("IP Destination", ["Toutes"] + all_ips)
selected_protocol = st.sidebar.selectbox("Protocole", ["Tous"] + df["protocol_type"].unique().tolist())
min_duration = st.sidebar.slider("Durée minimum", 0, int(df["duration"].max()), 0)

filtered_df = df[
    (selected_src_ip == "Toutes" or df["src_ip"] == selected_src_ip)
    & (selected_dst_ip == "Toutes" or df["dst_ip"] == selected_dst_ip)
    & (selected_protocol == "Tous" or df["protocol_type"] == selected_protocol)
    & (df["duration"] >= min_duration)
]

st.subheader("🔍 Connexions Réseau")
st.dataframe(filtered_df)

# 📈 Graphique interactif du réseau
st.subheader("🌐 Visualisation du Réseau")

G = nx.Graph()

for _, row in filtered_df.iterrows():
    color = "red" if row["anomaly"] else "green"
    G.add_edge(row["src_ip"], row["dst_ip"], color=color)

net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
net.from_nx(G)
net.save_graph("network.html")

HtmlFile = open("network.html", "r", encoding="utf-8")
components.html(HtmlFile.read(), height=500)

# 🚨 Alertes des Anomalies
anomalies = filtered_df[filtered_df["anomaly"] == True]
if not anomalies.empty:
    st.error("🚨 **ALERTE : Anomalies détectées !**")
    st.write(anomalies)
