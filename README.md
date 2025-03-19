# Hackathon Cybersécurité et Détection d'Intrusions

# 📌 Description

La cybersécurité et la détection d'intrusions sont aujourd’hui des enjeux cruciaux dans le monde numérique. Le dataset KDD Cup 99, bien que datant, reste un référentiel pédagogique et technique intéressant pour expérimenter des méthodes de détection d’anomalies. Ce hackathon vise à combiner des compétences en data science, machine learning, infrastructure et DevOps.

# 📂 Structure du Projet

serving/ : Contient le code du serveur FastAPI pour exposer les endpoints de l'API.

webapp/ : Contient l'application Streamlit pour l'affichage des résultats et l'interaction avec l'utilisateur.

artifacts/ : Stocke les modèles entraînés et les datasets utilisés.

.gitignore : Fichier définissant les exclusions pour Git.

README.md : Ce fichier de documentation.

docker-compose.yml : Fichier de configuration pour déployer les services via Docker Compose.

test_data_processing.py : Script pour la création du model.

# 🚀 Installation et Lancement

Prérequis

Docker & Docker Compose

Déploiement avec Docker Compose

docker-compose up --build

Accès à l'Application

L'interface Streamlit est accessible à l'adresse suivante :
🔗 http://4.233.193.108:8501/

# 📡 Endpoints de l'API FastAPI

L'API expose plusieurs endpoints pour interagir avec le modèle.

GET / : Vérification du statut du serveur.

POST /predict : Envoie des données et obtient une prédiction.

GET /connections : Récupère les informations sur les connections.

# 🎨 Interface Streamlit

L'application Streamlit permet de :

🖥️ Interface de Simulation

Affichage des connexions : Visualisation des flux réseau avec informations détaillées (IP source/destination, protocole, port, durée, etc.).

Lecture en temps réel ou en mode replay : Permet la simulation dynamique à partir d’un dataset prétraité.

🎛️ Interactivité

Filtres, zoom, recherche d’événements spécifiques et visualisation des statistiques globales.

🤖 Agent de Détection d’Anomalies

Modèle de Machine Learning : Implémentation d’un entraînés sur le dataset KDD Cup 99.

Analyse en temps réel : Traitement des données issues de l’interface pour identifier les anomalies.

Alertes et visualisation : Affichage des anomalies détectées.

🔗 Intégration et Communication

API de communication : Définition d’une API pour l’échange de données entre l’interface et l’agent.

Journalisation : Enregistrement des événements et des alertes pour une traçabilité et un audit post-incident.

# 📌 Contributeur

Lucas MASTROGIOVANNI
Anne-Laure VIRICEL
David NGUYEN
Jamil ABO-ALRUB





Ce projet est sous licence MIT.
