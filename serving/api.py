from fastapi import FastAPI
import pandas as pd
import random
import joblib
import numpy as np
import traceback
from pydantic import BaseModel

app = FastAPI()

# Charger les objets nécessaires
scaler = joblib.load("../artifacts/scaler_object.pkl")
pca = joblib.load("../artifacts/pca_object.pkl")
model = joblib.load("../artifacts/random_forest_pca_multi_class_anomaly_detection.pkl")

# Charger le dataset KDD Cup 99
df = pd.read_csv("../artifacts/KDDCup99.csv", sep=",", low_memory=False)

# Sélectionner les colonnes pertinentes
feature_columns = df.columns.tolist()  # On garde toutes les features
df = df[feature_columns]

# Convertir "protocol_type" et autres catégories si elles existent
protocol_map = {"tcp": 0, "udp": 1, "icmp": 2}
if "protocol_type" in df.columns:
    df["protocol_type"] = df["protocol_type"].map(protocol_map)

# Ajouter des colonnes IP fictives pour la simulation
df["src_ip"] = [f"192.168.1.{random.randint(1, 100)}" for _ in range(len(df))]
df["dst_ip"] = [f"10.0.0.{random.randint(1, 100)}" for _ in range(len(df))]

@app.get("/")
def home():
    return {"message": "API de simulation réseau KDD Cup 99"}
  
@app.get('/connections')
def get_connections(n: int = 50):
    """Renvoie n connexions réseau avec détection d’anomalies"""
    try:
        sample = df.sample(n).copy()

        # ✅ Vérifier les colonnes attendues
        expected_columns = scaler.feature_names_in_
        print("🟢 Colonnes avant transformation :", sample.columns.tolist())
        print("🟢 Features attendues :", list(expected_columns))

        # ✅ Vérification et correction de `protocol_type`
        if "protocol_type" in sample.columns:
            print("🔍 Valeurs uniques de `protocol_type` AVANT transformation :", sample["protocol_type"].unique())

            # ✅ Si `protocol_type` est déjà numérique, ne rien faire
            if sample["protocol_type"].dtype == "int64":
                print("✅ `protocol_type` est déjà numérique, pas besoin de mapping.")
            else:
                sample["protocol_type"] = sample["protocol_type"].str.lower().map(protocol_map)

            print("✅ `protocol_type` APRÈS transformation :", sample["protocol_type"].unique())

        # ✅ Encodage des variables catégoriques
        if "service" in sample.columns:
            sample["service"] = sample["service"].astype("category").cat.codes
        if "flag" in sample.columns:
            sample["flag"] = sample["flag"].astype("category").cat.codes

        # ✅ Vérifier et remplacer les NaN
        if sample.isna().sum().sum() > 0:
            print("⚠️ NaN détectés ! Remplacement par -1")
            sample.fillna(-1, inplace=True)

        # ✅ Sélectionner uniquement les features utilisées par le modèle
        features = sample[expected_columns]

        # ✅ Appliquer la normalisation et la PCA
        features_scaled = scaler.transform(features)
        features_pca = pca.transform(features_scaled)

        # ✅ Prédiction des anomalies
        sample["anomaly"] = model.predict(features_pca)  # 1 = Normal, 0 = Anomalie

        # ✅ Remplacer le label par "normal" ou "anomalie"
        if "label" in sample.columns:
            sample["anomaly"] = sample["label"].apply(lambda x: "normal" if x == "normal" else "anomalie")

        # ✅ Vérification finale
        print("🟢 Sample après transformation :", sample.head())

        return sample.to_dict(orient="records")

    except Exception as e:
        print("❌ ERREUR DANS /connections")
        print(traceback.format_exc())  
        return {"error": f"Problème dans /connections : {str(e)}"}





# Définition du modèle Pydantic pour prédiction
class DataPoint(BaseModel):
    duration: float
    protocol_type: str  # Reste en string, sera converti en int après
    src_bytes: int
    dst_bytes: int
    service: int
    flag: int
    land: int
    wrong_fragment: int
    urgent: int
    hot: int
    num_failed_logins: int
    logged_in: int
    lnum_compromised: int
    lroot_shell: int
    lsu_attempted: int
    lnum_root: int
    lnum_file_creations: int
    lnum_shells: int
    lnum_access_files: int
    lnum_outbound_cmds: int
    is_host_login: int
    is_guest_login: int
    count: int
    srv_count: int
    serror_rate: float
    srv_serror_rate: float
    rerror_rate: float
    srv_rerror_rate: float
    same_srv_rate: float
    diff_srv_rate: float
    srv_diff_host_rate: float
    dst_host_count: int
    dst_host_srv_count: int
    dst_host_same_srv_rate: float
    dst_host_diff_srv_rate: float
    dst_host_same_src_port_rate: float
    dst_host_srv_diff_host_rate: float
    dst_host_serror_rate: float
    dst_host_srv_serror_rate: float
    dst_host_rerror_rate: float
    dst_host_srv_rerror_rate: float

@app.post("/predict")
def predict_anomaly(data: DataPoint):
    """Prédit si une connexion est une anomalie"""
    try:
        df = pd.DataFrame([data.dict()])

        # ✅ Vérification et correction de `protocol_type`
        if "protocol_type" in df.columns:
            print("🔍 Avant transformation :", df["protocol_type"].unique())
            df["protocol_type"] = df["protocol_type"].str.lower().map(protocol_map)
            print("✅ Après transformation :", df["protocol_type"].unique())

        # ✅ Encodage des variables catégoriques
        if "service" in df.columns:
            df["service"] = df["service"].astype("category").cat.codes
        if "flag" in df.columns:
            df["flag"] = df["flag"].astype("category").cat.codes

        # ✅ Vérifier si toutes les colonnes attendues sont là
        expected_columns = list(scaler.feature_names_in_)

        # ✅ Réorganiser les colonnes dans le bon ordre
        df = df[expected_columns]

        # ✅ Appliquer la normalisation et la PCA
        features_scaled = scaler.transform(df)
        features_pca = pca.transform(features_scaled)

        # ✅ Prédiction
        prediction = model.predict(features_pca)[0]
        score = model.predict_proba(features_pca)[:, 1][0]

        return {
            "prediction": "Anomalie" if prediction == 0 else "Normal",
            "score": score
        }

    except Exception as e:
        print("❌ ERREUR DANS /predict :", traceback.format_exc())  
        return {"error": f"Problème dans /predict : {str(e)}"}
