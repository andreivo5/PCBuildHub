import pandas as pd
import json

COLUMNS = [
    "name", "core_count", "core_clock", "boost_clock", "tdp", "graphics", "smt",
    "brand", "series", "model", "cpu_mark", "thread_mark", "socket",
    "offers", "image"
]

gpu_df = pd.read_csv("CPU_gputracker.csv")
gh_df = pd.read_csv("CPU_geizhals.csv")

def make_key(row):
    return f"{row.get('brand', '')}|{row.get('series', '')}|{row.get('model', '')}"

gpu_df["key"] = gpu_df.apply(make_key, axis=1)
gh_df["key"] = gh_df.apply(make_key, axis=1)

gh_lookup = {row["key"]: row for _, row in gh_df.iterrows()}
final_rows = []

for _, gpu_row in gpu_df.iterrows():
    key = gpu_row["key"]
    offers = json.loads(gpu_row.get("offers", "[]"))

    if offers:
        row_data = gpu_row
    elif key in gh_lookup:
        row_data = gh_lookup[key]
    else:
        row_data = gpu_row

    filled_row = {col: row_data.get(col, "") for col in COLUMNS}
    final_rows.append(filled_row)

combined_df = pd.DataFrame(final_rows, columns=COLUMNS)
combined_df.to_csv("CPU_combined.csv", index=False)

print("merge done - output saved to CPU_combined.csv")