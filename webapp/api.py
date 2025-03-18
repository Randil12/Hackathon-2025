import streamlit as st
import pandas as pd
import requests
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import time
import os
import plotly.express as px

st.set_page_config(page_title="Simulation Réseau KDD Cup 99", layout="wide")

st.title("📡 Simulation des Connexions Réseau - KDD Cup 99")

API_URL = "http://fastapi_app:8080"  # Adresse du serveur FastAPI
protocol_map = {0: "tcp", 1: "udp", 2: "icmp"}  # Mapping des protocoles
log_file = "logs_kdd99.csv"  # Fichier CSV de journalisation

# 📌 Mode Playback - Simulation
st.sidebar.header("🎛 Mode Playback")
playback_mode = st.sidebar.radio("Sélectionner un mode :", ["Automatique", "Manuel"])
num_connections = st.sidebar.slider("Nombre de connexions affichées", 10, 200, 50)

# 📌 Fonction pour récupérer les connexions depuis FastAPI
@st.cache_data
def get_data(n):
    try:
        response = requests.get(f"{API_URL}/connections?n={n}")
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        if "protocol_type" in df.columns:
            df["protocol_type"] = df["protocol_type"].map(protocol_map)

        return df
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion à l'API : {e}")
        return pd.DataFrame()

df = get_data(num_connections)

if df.empty:
    st.warning("⚠️ Aucune donnée récupérée. Vérifiez la connexion à FastAPI.")
    st.stop()

# 📌 Sélection des 50 connexions (ou selon le nombre défini)
current_df = df.iloc[:num_connections]

# 📊 Affichage des connexions filtrées
st.subheader("🔍 Connexions Réseau")
st.dataframe(current_df)

# 🚨 Détection des anomalies parmi les 50 connexions
st.subheader("⚠️ Détection des Anomalies en Temps Réel")

@st.cache_data
def get_anomalies(data):
    return data[data["anomaly"] == True]

anomalies = get_anomalies(current_df)

if not anomalies.empty:
    st.error(f"🚨 **{len(anomalies)} anomalies détectées parmi les {num_connections} connexions affichées !**")
    st.dataframe(anomalies)
else:
    st.success("✅ Aucune anomalie détectée parmi les connexions affichées.")

# 📈 🌐 Visualisation du réseau
st.subheader("🌐 Visualisation du Réseau")

G = nx.Graph()

for _, row in current_df.iterrows():
    color = "red" if row["anomaly"] else "green"
    G.add_edge(row["src_ip"], row["dst_ip"], color=color)

net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
net.from_nx(G)
net.save_graph("network.html")

HtmlFile = open("network.html", "r", encoding="utf-8")
components.html(HtmlFile.read(), height=500)

# 📌 Journalisation des événements
st.subheader("📜 Journalisation des Événements")

if not current_df.empty:
    if os.path.exists(log_file):
        current_df.to_csv(log_file, mode='a', index=False, header=False)
    else:
        current_df.to_csv(log_file, index=False)

st.success(f"✅ Journal des connexions enregistré dans `{log_file}`.")

with open(log_file, "rb") as file:
    st.download_button("📥 Télécharger le journal des événements", file, log_file, "text/csv")

# 📊 📈 Dashboards interactifs après la visualisation du réseau
st.subheader("📊 Statistiques et Analyse des Connexions")

if not df.empty:
    # ✅ Graphique des types de protocoles
    protocol_counts = df["protocol_type"].value_counts().reset_index()
    protocol_counts.columns = ["protocol_type", "count"]
    fig_protocol = px.bar(protocol_counts, x="protocol_type", y="count", title="Nombre de connexions par protocole")
    st.plotly_chart(fig_protocol)

    # ✅ Histogramme des scores d'anomalie
    if "anomaly_score" in df.columns:
        fig_anomaly = px.histogram(df, x="anomaly_score", nbins=50, title="Distribution des scores d'anomalie")
        st.plotly_chart(fig_anomaly)
    
    # ✅ Répartition des anomalies (Pie Chart)
    if "anomaly" in df.columns:
        fig_pie = px.pie(df, names="anomaly", title="Répartition des connexions normales vs anomalies")
        st.plotly_chart(fig_pie)
else:
    st.warning("⚠️ Pas de données disponibles pour les statistiques.")

# 📌 Envoi d'une connexion manuelle à FastAPI pour prédiction
st.sidebar.header("🛠 Tester une connexion")

duration = st.sidebar.number_input("⏳ Duration", min_value=0.0, value=0.0)
protocol_type = st.sidebar.selectbox("🖧 Protocol Type", ["tcp", "udp", "icmp"])
src_bytes = st.sidebar.number_input("📤 Src Bytes", min_value=0.0, value=0.0)
dst_bytes = st.sidebar.number_input("📥 Dst Bytes", min_value=0.0, value=0.0)

if st.sidebar.button("🔎 Vérifier l'anomalie"):
    payload = {
        "duration": duration,
        "protocol_type": list(protocol_map.keys())[list(protocol_map.values()).index(protocol_type)],}
