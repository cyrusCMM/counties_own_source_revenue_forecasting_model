import numpy as np
import pandas as pd
from model import forecast_county

# example load
df = pd.read_excel("data/osr_data.xlsx")
final = pd.read_excel("data/model_selection.xlsx")

# basic preparation
if "gcp" not in df.columns and "gcp_nominal" in df.columns:
    df["gcp"] = df["gcp_nominal"]

df["ln_osr"] = np.log(df["osr"])
df["ln_gcp"] = np.log(df["gcp"])

result = forecast_county(df, final, "Nairobi", horizon=4)
print(result)