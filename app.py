import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from model import forecast_county

st.set_page_config(page_title="County OSR Forecast", layout="wide")


@st.cache_data
def load_data():
    df = pd.read_excel("osr_data.xlsx")
    final = pd.read_excel("model_selection.xlsx")

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .str.replace(r"\s+", " ", regex=True)
    )

    rename_map = {
        "County": "county",
        "county": "county",
        "Year": "year",
        "year": "year",
        "County_revenue": "osr",
        "county_revenue": "osr",
        "OSR": "osr",
        "osr": "osr",
        "Nominal_GCP": "gcp",
        "nominal_gcp": "gcp",
        "gcp": "gcp",
        "gcp_nominal": "gcp"
    }
    df = df.rename(columns=rename_map)

    needed = ["county", "year", "osr", "gcp"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing columns after renaming: {missing}. Found columns: {list(df.columns)}"
        )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["osr"] = pd.to_numeric(df["osr"], errors="coerce")
    df["gcp"] = pd.to_numeric(df["gcp"], errors="coerce")

    df = df.dropna(subset=["county", "year", "osr", "gcp"]).copy()
    df = df[(df["osr"] > 0) & (df["gcp"] > 0)].copy()

    df["county"] = df["county"].astype(str).str.strip()
    df["year"] = df["year"].astype(int)

    df["ln_osr"] = np.log(df["osr"])
    df["ln_gcp"] = np.log(df["gcp"])

    return df, final


df, final = load_data()

st.title("County OSR Forecasting Tool")

county_list = sorted(df["county"].dropna().unique().tolist())
county = st.selectbox("Select county", county_list)
horizon = st.slider("Forecast horizon", min_value=1, max_value=5, value=4)

result, metrics = forecast_county(df, final, county, horizon=horizon)

model_labels = {
    "A_trend_only": "Trend only",
    "B_trend_plus_elasticity": "Trend + elasticity",
    "C_trend_plus_growth": "Trend + growth"
}

model_used = model_labels.get(metrics["model_name"], metrics["model_name"])

st.subheader(f"{county} forecast")
st.write(f"Model used: {model_used}")

st.dataframe(
    result.style.format({
        "forecast": "{:,.0f}",
        "lower": "{:,.0f}",
        "upper": "{:,.0f}"
    }),
    use_container_width=True
)

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    result["year"],
    result["forecast"],
    color="#1f4e79",
    linewidth=2.2,
    label="Forecast"
)

ax.fill_between(
    result["year"],
    result["lower"],
    result["upper"],
    color="#5dade2",
    alpha=0.20,
    label="95% band"
)

mid_lower = (result["forecast"] + result["lower"]) / 2
mid_upper = (result["forecast"] + result["upper"]) / 2

ax.fill_between(
    result["year"],
    mid_lower,
    mid_upper,
    color="#2e86c1",
    alpha=0.25,
    label="Inner band"
)

last_actual_year = int(df[df["county"] == county]["year"].max())
ax.axvline(last_actual_year, linestyle="--", color="gray", linewidth=1)

ax.set_title(f"{county} OSR forecast")
ax.set_xlabel("Year")
ax.set_ylabel("OSR")

textstr = f"R²: {metrics['r2']:.3f}\nMAPE: {metrics['mape']*100:.1f}%"
ax.text(
    0.02, 0.95, textstr,
    transform=ax.transAxes,
    fontsize=10,
    verticalalignment="top",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.75)
)

ax.grid(alpha=0.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False)

st.pyplot(fig)

csv_data = result.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download forecast as CSV",
    data=csv_data,
    file_name=f"{county.lower().replace(' ', '_')}_forecast.csv",
    mime="text/csv"
)
