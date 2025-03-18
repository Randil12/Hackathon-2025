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

class DataPoint(BaseModel):
    duration: float
    protocol_type: int
    src_bytes: int
    dst_bytes: int
    
protocol_map = {"tcp": 0, "udp": 1, "icmp": 2}

@app.post("/predict")
def predict_anomaly(data: DataPoint):
    # Convertir les données en DataFrame
    df = pd.DataFrame([data.dict()])

    # Encodage manuel du protocole
    df["protocol_type"] = df["protocol_type"].map(protocol_map)

    # Gérer les valeurs non reconnues
    if df["protocol_type"].isnull().any():
        return {"error": "Protocol type must be 'tcp', 'udp', or 'icmp'."}

    # Normalisation simple (moyenne/écart-type fictifs issus du dataset d'entraînement)
    df["duration"] = (df["duration"] - 100) / 200
    df["src_bytes"] = (df["src_bytes"] - 500) / 1000
    df["dst_bytes"] = (df["dst_bytes"] - 300) / 800

    # Prédiction
    prediction = model.predict(df)[0]
    score = model.decision_function(df)[0]

    return {
        "prediction": "Anomalie" if prediction == -1 else "Normal",
        "score": score
    }
