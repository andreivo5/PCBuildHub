import pandas as pd
import random
import csv
import ast

cpu_df = pd.read_csv("CPU.csv")
gpu_df = pd.read_csv("GPU.csv")

def has_price(offers):
    if not isinstance(offers, str):
        return False
    try:
        offers_list = ast.literal_eval(offers)
        return any("price" in o for o in offers_list)
    except:
        return False

cpu_df.dropna(subset=["offers"], inplace=True)
cpu_df = cpu_df[cpu_df["offers"].apply(has_price)]

gpu_df.dropna(subset=["offers"], inplace=True)
gpu_df = gpu_df[gpu_df["offers"].apply(has_price)]

VIDEO_EDITING_TIERS = {
    "edit_1080p_other":     {"cpu": (8000, 20000),   "gpu": (4000, 9000)},
    "edit_1080p_premiere": {"cpu": (12000, 25000),  "gpu": (6000, 12000)},
    "edit_1080p_resolve":  {"cpu": (15000, 30000),  "gpu": (8000, 14000)},

    "edit_4k_other":        {"cpu": (20000, 40000),  "gpu": (8000, 16000)},
    "edit_4k_premiere":    {"cpu": (25000, 50000),  "gpu": (10000, 20000)},
    "edit_4k_resolve":     {"cpu": (30000, 65000),  "gpu": (14000, 30000)}
}

LABELS = list(VIDEO_EDITING_TIERS.keys())
NUM_SAMPLES = 15000
rows = []
pos_count = 0
neg_count = 0

for _ in range(NUM_SAMPLES):
    label = random.choice(LABELS)
    tier = VIDEO_EDITING_TIERS[label]
    min_cpu_mark, max_cpu_mark = tier["cpu"]
    min_gpu_mark, max_gpu_mark = tier["gpu"]

    is_positive = (random.random() < 0.5)

    if is_positive:
        valid_cpus = cpu_df[(cpu_df["cpu_mark"] >= min_cpu_mark) & (cpu_df["cpu_mark"] <= max_cpu_mark)]
        valid_gpus = gpu_df[(gpu_df["g3d_mark"] >= min_gpu_mark) & (gpu_df["g3d_mark"] <= max_gpu_mark)]
        match_val = 1
    else:
        if random.random() < 0.5:
            valid_cpus = cpu_df[(cpu_df["cpu_mark"] < min_cpu_mark) | (cpu_df["cpu_mark"] > max_cpu_mark)]
            valid_gpus = gpu_df[(gpu_df["g3d_mark"] >= min_gpu_mark) & (gpu_df["g3d_mark"] <= max_gpu_mark)]
        else:
            valid_cpus = cpu_df[(cpu_df["cpu_mark"] >= min_cpu_mark) & (cpu_df["cpu_mark"] <= max_cpu_mark)]
            valid_gpus = gpu_df[(gpu_df["g3d_mark"] < min_gpu_mark) | (gpu_df["g3d_mark"] > max_gpu_mark)]
        match_val = 0

    if len(valid_cpus) == 0 or len(valid_gpus) == 0:
        continue

    cpu_row = valid_cpus.sample(1).iloc[0]
    gpu_row = valid_gpus.sample(1).iloc[0]

    row_dict = {
        "cpu_mark": cpu_row["cpu_mark"],
        "cpu_cores": cpu_row.get("core_count", None),
        "cpu_clock": cpu_row.get("core_clock", None),
        "cpu_smt": 1 if str(cpu_row.get("smt", "")).lower() == "true" else 0,
        "cpu_tdp": cpu_row.get("tdp", None),
        "thread_mark": cpu_row.get("thread_mark", None),

        "g3d_mark": gpu_row["g3d_mark"],
        "gpu_vram": gpu_row.get("vram", gpu_row.get("VRAM", None)),
        "gpu_tdp": gpu_row.get("tdp", None),
        "gpu_g2d": gpu_row.get("g2d_mark", None),

        "label": label,
        "match": match_val
    }

    rows.append(row_dict)
    if match_val == 1:
        pos_count += 1
    else:
        neg_count += 1

print(f"Generated {len(rows)} rows. Positives: {pos_count}, Negatives: {neg_count}")

csv_out = "cpu_gpu_video_editing_data.csv"
if rows:
    fieldnames = list(rows[0].keys())
    with open(csv_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

print(f"Saved dataset to {csv_out}")