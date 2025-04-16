import os
import joblib
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_BASE_DIR = CURRENT_DIR
FEATURE_COLUMNS = [
    "cpu_mark", "cpu_cores", "cpu_clock", "cpu_smt", "cpu_tdp", "thread_mark",
    "g3d_mark", "gpu_vram", "gpu_tdp", "gpu_g2d"
]

# Function to process the best synergy matches between CPU & GPU combos based on user's input.
def predict_cpu_gpu_synergy(label, cpu, gpu, use_case="gaming"):
    if use_case not in ["gaming", "editing", "dev"]:
        raise ValueError(f"Invalid use_case: {use_case}. Must be 'gaming', 'editing', or 'dev'.")

    model_dir = os.path.join(MODELS_BASE_DIR, use_case)
    model_path = os.path.join(model_dir, f"model_{label}.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

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
