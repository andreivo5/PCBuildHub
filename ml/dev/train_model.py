import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from collections import Counter
import os

df = pd.read_csv("cpu_gpu_dev_data.csv")
print(f"Loaded dataset with {len(df)} rows.")
print("Labels:", df["label"].unique())

df["cpu_cores"]   = df["cpu_cores"].fillna(0)
df["cpu_clock"]   = df["cpu_clock"].fillna(0)
df["cpu_tdp"]     = df["cpu_tdp"].fillna(0)
df["thread_mark"] = df["thread_mark"].fillna(0)
df["gpu_vram"]    = df["gpu_vram"].fillna(0)
df["gpu_tdp"]     = df["gpu_tdp"].fillna(0)
df["gpu_g2d"]     = df["gpu_g2d"].fillna(0)

FEATURES = [
    "cpu_mark", "cpu_cores", "cpu_clock", "cpu_smt", "cpu_tdp", "thread_mark",
    "g3d_mark", "gpu_vram", "gpu_tdp", "gpu_g2d"
]

os.makedirs("models_dev", exist_ok=True)

unique_labels = df["label"].unique()

for label_name in unique_labels:
    print(f"\n=== Training model for {label_name} ===")
    subset = df[df["label"] == label_name].copy()

    print(f"Label distribution for {label_name} =>", Counter(subset["match"]))

    X = subset[FEATURES]
    y = subset["match"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = lgb.LGBMClassifier(random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    print(confusion_matrix(y_test, y_pred))

    model_filename = f"models_dev/model_{label_name}.pkl"
    joblib.dump(model, model_filename)
    print(f"Saved to {model_filename}")

print("\nAll software development models trained and saved.")