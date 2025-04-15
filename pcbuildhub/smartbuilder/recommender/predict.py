import os
import joblib
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(CURRENT_DIR, "gaming")
FEATURE_COLUMNS = [
    "cpu_mark", "cpu_cores", "cpu_clock", "cpu_smt", "cpu_tdp", "thread_mark",
    "g3d_mark", "gpu_vram", "gpu_tdp", "gpu_g2d"
]

def predict_cpu_gpu_synergy(label, cpu, gpu):
    model_path = os.path.join(MODELS_DIR, f"model_{label}.pkl")
    model = joblib.load(model_path)

    row_dict = {
        "cpu_mark":    cpu.cpu_mark or 0,
        "cpu_cores":   cpu.core_count or 0,
        "cpu_clock":   cpu.core_clock or 0.0,
        "cpu_smt":     1 if cpu.smt else 0,
        "cpu_tdp":     cpu.tdp or 0,
        "thread_mark": cpu.thread_mark or 0,

        "g3d_mark":    gpu.g3d_mark or 0,
        "gpu_vram":    gpu.vram or 0,
        "gpu_tdp":     gpu.tdp or 0,
        "gpu_g2d":     gpu.g2d_mark or 0,
    }

    X = pd.DataFrame([row_dict], columns=FEATURE_COLUMNS)

    proba = model.predict_proba(X)[0, 1]
    return proba