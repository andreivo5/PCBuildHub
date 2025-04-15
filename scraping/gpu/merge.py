import pandas as pd
import json

tracker_df = pd.read_csv("gpu_gputracker.csv")
geizhals_df = pd.read_csv("gpu_geizhals.csv")

geizhals_offers = geizhals_df.set_index("name")["offers"].to_dict()

def merge_offers_verbose(name, current_offers):
    geizhals = geizhals_offers.get(name)
    try:
        current_list = json.loads(current_offers) if isinstance(current_offers, str) else []
    except:
        current_list = []
    try:
        geizhals_list = json.loads(geizhals) if isinstance(geizhals, str) else []
    except:
        geizhals_list = []

    if geizhals_list:
        if not current_list:
            print(f"- ADDED - {name}")
        else:
            print(f"- REPLACED - {name}")
        return json.dumps(geizhals_list)
    else:
        return current_offers

tracker_df["offers"] = tracker_df.apply(lambda row: merge_offers_verbose(row["name"], row["offers"]), axis=1)

tracker_df.to_csv("GPU_prices.csv", index=False)
print("merge done - saved to GPU_prices.csv")