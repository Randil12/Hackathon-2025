import streamlit as st
import pandas as pd
import requests
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import os
import plotly.express as px
import random

# 📌 Configuration de la page
st.set_page_config(page_title="Simulation Réseau KDD Cup 99", layout="wide")
st.title("📡 Simulation des Connexions Réseau - KDD Cup 99")

# 📌 Variables globales
protocol_map = {0: "tcp", 1: "udp", 2: "icmp"}
reverse_protocol_map = {v: k for k, v in protocol_map.items()}  # Inverse le mapping
log_file = "logs_kdd99.csv"

# 📌 Mode Simulation
n_connections = st.sidebar.slider("Nombre de connexions affichées", 10, 200, 50)

# 📌 Fonction pour récupérer les connexions depuis FastAPI
@st.cache_data
def get_data(n):
    try:
        response = requests.get(f"http://fastapi_app:8080/connections?n={n}")
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        # ✅ Correction du protocol_type (0,1,2 ➝ tcp, udp, icmp)
        if "protocol_type" in df.columns:
            df["protocol_type"] = df["protocol_type"].replace(protocol_map)

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

# 📌 Correction du slider Durée minimum
if df["duration"].isna().all() or df["duration"].max() == 0:
    max_duration = 1  # Valeur par défaut pour éviter l'erreur
else:
    max_duration = int(df["duration"].max())

# 📌 Correction du slider
min_duration = st.sidebar.slider("Durée minimum", 0, max_duration, 0)


# 📌 Appliquer les filtres APRÈS la définition de `filtered_df`
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


st.subheader("📊 Statistiques et Analyse des Connexions")

# Déterminer le DataFrame à utiliser (filtré ou non)
df_to_use = filtered_df if not filtered_df.empty else df

if not df_to_use.empty:
    # ✅ Distribution des protocoles TCP/UDP/ICMP
    if "protocol_type" in df_to_use.columns:
        protocol_counts = df_to_use["protocol_type"].replace({0: "tcp", 1: "udp", 2: "icmp"}).value_counts().reset_index()
        protocol_counts.columns = ["protocol", "count"]
        fig_protocols = px.bar(protocol_counts, x="protocol", y="count", title="Distribution des Protocoles (TCP/UDP/ICMP)")
        st.plotly_chart(fig_protocols)

    # ✅ Répartition des anomalies (normal vs anomalies)
    if "anomaly" in df_to_use.columns:
        fig_pie = px.pie(df_to_use, names="anomaly", title="Répartition des connexions normales vs anomalies")
        st.plotly_chart(fig_pie)
else:
    st.warning("⚠️ Pas de données disponibles pour les statistiques.")

# 📌 Tester une connexion
st.sidebar.header("🛠 Tester une connexion")

# Valeurs définies par l'utilisateur
duration = st.sidebar.number_input("⏳ Duration", min_value=0.0, value=10.0)
protocol_type = st.sidebar.selectbox("🖧 Protocol Type", ["tcp", "udp", "icmp"])
src_bytes = st.sidebar.number_input("📤 Src Bytes", min_value=0.0, value=500.0)
dst_bytes = st.sidebar.number_input("📥 Dst Bytes", min_value=0.0, value=200.0)
service = st.sidebar.number_input("💾 Service", min_value=0, value=5)
flag = st.sidebar.number_input("🚩 Flag", min_value=0, value=2)

if st.sidebar.button("🔎 Vérifier l'anomalie"):
    payload = {
        "duration": float(duration),
        "protocol_type": protocol_type,  # ✅ Garde le string ("tcp", "udp", "icmp")
        "src_bytes": int(src_bytes),
        "dst_bytes": int(dst_bytes),
        "service": int(service),
        "flag": int(flag),
        "land": 0,
        "wrong_fragment": 0,
        "urgent": 0,
        "hot": random.randint(0, 10),
        "num_failed_logins": random.randint(0, 5),
        "logged_in": random.choice([0, 1]),
        "lnum_compromised": random.randint(0, 5),
        "lroot_shell": random.randint(0, 1),
        "lsu_attempted": random.randint(0, 1),
        "lnum_root": random.randint(0, 5),
        "lnum_file_creations": random.randint(0, 5),
        "lnum_shells": random.randint(0, 5),
        "lnum_access_files": random.randint(0, 5),
        "lnum_outbound_cmds": 0,
        "is_host_login": random.choice([0, 1]),
        "is_guest_login": random.choice([0, 1]),
        "count": random.randint(0, 500),
        "srv_count": random.randint(0, 500),
        "serror_rate": round(random.uniform(0, 1), 2),
        "srv_serror_rate": round(random.uniform(0, 1), 2),
        "rerror_rate": round(random.uniform(0, 1), 2),
        "srv_rerror_rate": round(random.uniform(0, 1), 2),
        "same_srv_rate": round(random.uniform(0, 1), 2),
        "diff_srv_rate": round(random.uniform(0, 1), 2),
        "srv_diff_host_rate": round(random.uniform(0, 1), 2),
        "dst_host_count": random.randint(0, 255),
        "dst_host_srv_count": random.randint(0, 255),
        "dst_host_same_srv_rate": round(random.uniform(0, 1), 2),
        "dst_host_diff_srv_rate": round(random.uniform(0, 1), 2),
        "dst_host_same_src_port_rate": round(random.uniform(0, 1), 2),
        "dst_host_srv_diff_host_rate": round(random.uniform(0, 1), 2),
        "dst_host_serror_rate": round(random.uniform(0, 1), 2),
        "dst_host_srv_serror_rate": round(random.uniform(0, 1), 2),
        "dst_host_rerror_rate": round(random.uniform(0, 1), 2),
        "dst_host_srv_rerror_rate": round(random.uniform(0, 1), 2)
    }

    try:
        response = requests.post(f"http://fastapi_app:8080/predict", json=payload)
        response.raise_for_status()
        result = response.json()
        st.sidebar.write(f"Résultat: {result.get('prediction', 'Erreur')} (Score: {result.get('score', 0):.4f})")
    except requests.exceptions.RequestException as e:
        st.sidebar.error(f"⚠️ Réponse invalide de l'API : {e}")
