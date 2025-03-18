import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import pickle 

df =pd.read_csv('KDDCup99.csv')
# Encode categorical features
categorical_columns = ["protocol_type", "service", "flag"]
df[categorical_columns] = df[categorical_columns].apply(LabelEncoder().fit_transform)

# Separate features and labels
X = df.drop("label", axis=1)
y = df["label"]  # Keep the original labels

# Step 3: Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 4: Standardize the features (important for PCA)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Step 5: Apply PCA to reduce dimensionality
pca = PCA(n_components=0.95, random_state=42)  # Retain 95% of the variance
X_train_pca = pca.fit_transform(X_train)
X_test_pca = pca.transform(X_test)


# Step 6: Train the Random Forest classifier for multi-class classification
rf = RandomForestClassifier(
    n_estimators=100,  # Number of trees in the forest
    max_depth=None,    # Maximum depth of the tree
    min_samples_split=2,  # Minimum number of samples required to split a node
    min_samples_leaf=1,   # Minimum number of samples required at each leaf node
    random_state=42,      
    n_jobs=-1            
)

# Train the model
rf.fit(X_train_pca, y_train)

# Step 7: Evaluate the model
# Predict on the test set
y_pred = rf.predict(X_test_pca)




with open("random_forest_pca_multi_class_anomaly_detection.pkl", "wb") as f:
    pickle.dump(rf, f)

# Save the PCA object
with open("pca_object.pkl", "wb") as f:
    pickle.dump(pca, f)

# Save the scaler object
with open("scaler_object.pkl", "wb") as f:
    pickle.dump(scaler, f)

