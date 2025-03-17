from fastapi import FastAPI
import pandas as pd
import random
import joblib
from pydantic import BaseModel

app = FastAPI()

# Charger le dataset KDD Cup 99
df = pd.read_csv("../artifacts/KDDCup99.csv", sep=",", low_memory=False)

# Sélectionner les colonnes pertinentes
df = df.iloc[:, [0, 1, 4, 5]]  # Durée, Protocole, Bytes source/destination
df.columns = ["duration", "protocol_type", "src_bytes", "dst_bytes"]

# Convertir "protocol_type" en numérique
protocol_map = {"tcp": 0, "udp": 1, "icmp": 2}
df["protocol_type"] = df["protocol_type"].map(protocol_map)

# Ajouter des colonnes IP source et destination fictives
df["src_ip"] = [f"192.168.1.{random.randint(1, 100)}" for _ in range(len(df))]
df["dst_ip"] = [f"10.0.0.{random.randint(1, 100)}" for _ in range(len(df))]

# Charger le modèle de détection d’anomalies
model = joblib.load("../artifacts/isolation_forest.pkl")

@app.get("/")
def home():
    return {"message": "API de simulation réseau KDD Cup 99"}

@app.get("/connections")
def get_connections(n: int = 50):
    """Renvoie `n` connexions réseau simulées avec détection d’anomalies"""
    sample = df.sample(n).copy()

    # Détection d’anomalies
    features = sample[["duration", "protocol_type", "src_bytes", "dst_bytes"]]
    sample["anomaly_score"] = model.decision_function(features)
    sample["anomaly"] = model.predict(features) == -1  # Anomalie si -1

    return sample.to_dict(orient="records")

class Connection(BaseModel):
    duration: float
    protocol_type: int
    src_bytes: int
    dst_bytes: int

@app.post("/predict")
def predict_anomaly(conn: Connection):
    """Prédit si une connexion est une anomalie"""
    data = pd.DataFrame([conn.dict()])
    anomaly_score = model.decision_function(data)[0]
    is_anomaly = model.predict(data)[0] == -1  # -1 = anomalie

    return {"anomaly_score": anomaly_score, "anomaly": is_anomaly}
