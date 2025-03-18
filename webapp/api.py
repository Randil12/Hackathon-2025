import streamlit as st
import pandas as pd
import requests
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os
import plotly.express as px

# 📌 Configuration de la page
st.set_page_config(page_title="Simulation Réseau KDD Cup 99", layout="wide")
st.title("📡 Simulation des Connexions Réseau - KDD Cup 99")

# 📌 Variables globales
API_URL = "http://fastapi_app:8080"
protocol_map = {0: "tcp", 1: "udp", 2: "icmp"}
log_file = "logs_kdd99.csv"

# 📌 Mode Simulation
display_mode = st.sidebar.radio("Mode de Simulation", ["Temps réel", "Replay"])
n_connections = st.sidebar.slider("Nombre de connexions affichées", 10, 200, 50)

# 📌 Fonction pour récupérer les connexions depuis FastAPI
@st.cache_data
def get_data(n):
    try:
        response = requests.get(f"http://fastapi_app:8080/connections?n={n}")
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        # ✅ Vérification de la colonne protocol_type
        print("🔍 Valeurs uniques de protocol_type AVANT correction :", df["protocol_type"].unique())

        # ✅ Conversion explicite en `int` pour éviter les erreurs d'affichage
        df["protocol_type"] = df["protocol_type"].astype(int)

        # ✅ Vérification après conversion
        print("✅ Valeurs uniques de protocol_type APRÈS correction :", df["protocol_type"].unique())

        return df
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Erreur de connexion à l'API : {e}")
        return pd.DataFrame()


df = get_data(n_connections)

if df.empty:
    st.warning("⚠️ Aucune donnée récupérée. Vérifiez la connexion à FastAPI.")
    st.stop()

# 📌 Filtres interactifs
st.sidebar.header("🔎 Filtres")
all_ips = list(set(df["src_ip"].dropna().tolist() + df["dst_ip"].dropna().tolist()))
selected_src_ip = st.sidebar.selectbox("IP Source", ["Toutes"] + all_ips)
selected_dst_ip = st.sidebar.selectbox("IP Destination", ["Toutes"] + all_ips)
selected_protocol = st.sidebar.selectbox("Protocole", ["Tous"] + df["protocol_type"].dropna().unique().tolist())
min_duration = st.sidebar.slider("Durée minimum", 0, int(df["duration"].max()), 0)

filtered_df = df[
    ((selected_src_ip == "Toutes") | (df["src_ip"] == selected_src_ip)) &
    ((selected_dst_ip == "Toutes") | (df["dst_ip"] == selected_dst_ip)) &
    ((selected_protocol == "Tous") | (df["protocol_type"] == selected_protocol)) &
    (df["duration"] >= min_duration)
]

# 📌 Affichage des connexions filtrées
st.subheader("🔍 Connexions Réseau")
st.dataframe(filtered_df)

# 📌 Détection des anomalies
st.subheader("⚠️ Détection des Anomalies")
@st.cache_data
def get_anomalies(data):
    return data[data["anomaly"] != "normal"]  # Tous ceux qui ne sont PAS "normal" sont des anomalies

anomalies = get_anomalies(filtered_df)

if not anomalies.empty:
    st.error(f"🚨 **{len(anomalies)} anomalies détectées parmi les {n_connections} connexions affichées !**")
    st.dataframe(anomalies)
else:
    st.success("✅ Aucune anomalie détectée parmi les connexions affichées.")

# 📌 Visualisation du réseau
st.subheader("🌐 Visualisation du Réseau")
G = nx.Graph()

for _, row in filtered_df.iterrows():
    color = "red" if row["anomaly"] != "normal" else "green"
    G.add_edge(row["src_ip"], row["dst_ip"], color=color)

net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white")
net.from_nx(G)
net.save_graph("network.html")

HtmlFile = open("network.html", "r", encoding="utf-8")
components.html(HtmlFile.read(), height=500)

# 📌 Journalisation des événements
st.subheader("📜 Journalisation des Événements")

if not filtered_df.empty:
    if os.path.exists(log_file):
        filtered_df.to_csv(log_file, mode='a', index=False, header=False)
    else:
        filtered_df.to_csv(log_file, index=False)

st.success(f"✅ Journal des connexions enregistré dans `{log_file}`.")
with open(log_file, "rb") as file:
    st.download_button("📥 Télécharger le journal des événements", file, log_file, "text/csv")

# 📊 📈 Statistiques et Analyse des Connexions
st.subheader("📊 Statistiques et Analyse des Connexions")

if not df.empty:
    # 📌 Nombre de connexions par label (anomaly)
    label_counts = df["anomaly"].value_counts().reset_index()
    label_counts.columns = ["anomaly", "count"]
    fig_labels = px.bar(label_counts, x="anomaly", y="count", title="Nombre de connexions par label (normal vs anomalies)")
    st.plotly_chart(fig_labels)

    # 📌 Répartition des anomalies
    if "anomaly" in df.columns:
        fig_pie = px.pie(df, names="anomaly", title="Répartition des connexions normales vs anomalies")
        st.plotly_chart(fig_pie)
else:
    st.warning("⚠️ Pas de données disponibles pour les statistiques.")

# 📌 Tester une connexion
st.sidebar.header("🛠 Tester une connexion")
duration = st.sidebar.number_input("⏳ Duration", min_value=0.0, value=0.0)
protocol_type = st.sidebar.selectbox("🖧 Protocol Type", ["tcp", "udp", "icmp"])
src_bytes = st.sidebar.number_input("📤 Src Bytes", min_value=0.0, value=0.0)
dst_bytes = st.sidebar.number_input("📥 Dst Bytes", min_value=0.0, value=0.0)
service = st.sidebar.number_input("💾 Service", min_value=0, value=0)
flag = st.sidebar.number_input("🚩 Flag", min_value=0, value=0)

if st.sidebar.button("🔎 Vérifier l'anomalie"):
    payload = {
        "duration": duration,
        "protocol_type": list(protocol_map.keys())[list(protocol_map.values()).index(protocol_type)],
        "src_bytes": src_bytes,
        "dst_bytes": dst_bytes,
        "service": service,
        "flag": flag
    }
    try:
        response = requests.post(f"http://fastapi_app:8080/predict", json=payload)
        response.raise_for_status()
        result = response.json()
        st.sidebar.write(f"Résultat: {result.get('prediction', 'Erreur')} (Score: {result.get('score', 0):.4f})")
    except requests.exceptions.RequestException as e:
        st.sidebar.error("⚠️ Réponse invalide de l'API")
