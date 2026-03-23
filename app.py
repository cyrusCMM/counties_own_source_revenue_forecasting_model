import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from model import forecast_county

st.set_page_config(
    page_title="County Revenue Forecasting System",
    layout="wide"
)


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

model_labels = {
    "A_trend_only": "Trend only",
    "B_trend_plus_elasticity": "Trend + economic base",
    "C_trend_plus_growth": "Trend + growth adjustment"
}

st.title("County Revenue Forecasting System")
st.caption("A data-driven tool for county own-source revenue forecasting")

left, right = st.columns([1, 3])

with left:
    st.subheader("Inputs")
    county_list = sorted(df["county"].dropna().unique().tolist())
    county = st.selectbox("County", county_list)
    horizon = st.slider("Forecast horizon (years)", min_value=1, max_value=5, value=5)
    st.markdown("---")
    st.write(f"Counties in current deployment: {df['county'].nunique()}")

result, metrics = forecast_county(df, final, county, horizon=horizon)

model_used_raw = metrics["model_name"]
model_used = model_labels.get(model_used_raw, model_used_raw)

county_hist = df[df["county"] == county].sort_values("year").copy()
last_actual_year = int(county_hist["year"].max())
first_forecast_year = last_actual_year + 1

with right:
    st.subheader(f"{county}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Model selected", model_used)
    c2.metric("R²", f"{metrics['r2']:.3f}")
    c3.metric("MAPE", f"{metrics['mape']*100:.1f}%")
    c4.metric("Last observed year", f"{last_actual_year}")

    st.caption(
        f"Forecast period: {first_forecast_year}–{int(result['year'].max())} | "
        f"Values shown with 95% confidence bands"
    )

    fig, ax = plt.subplots(figsize=(10, 5.5))

    # actual history
    ax.plot(
        county_hist["year"],
        county_hist["osr"],
        color="#1f4e79",
        linewidth=2.2,
        marker="o",
        label="Actual OSR"
    )

    # forecast line
    ax.plot(
        result["year"],
        result["forecast"],
        color="#2e86c1",
        linewidth=2.0,
        linestyle="--",
        label="Forecast"
    )

    # outer band
    ax.fill_between(
        result["year"],
        result["lower"],
        result["upper"],
        color="#5dade2",
        alpha=0.20,
        label="95% confidence band"
    )

    # inner band
    mid_lower = (result["forecast"] + result["lower"]) / 2
    mid_upper = (result["forecast"] + result["upper"]) / 2
    ax.fill_between(
        result["year"],
        mid_lower,
        mid_upper,
        color="#2e86c1",
        alpha=0.20
    )

    ax.axvline(last_actual_year, linestyle="--", color="gray", linewidth=1)

    ax.set_title(f"{county}: Own-Source Revenue Projection", fontsize=12)
    ax.set_xlabel("Year")
    ax.set_ylabel("Revenue")
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(frameon=False)

    st.pyplot(fig)

st.subheader("Forecast table")
display_table = result.copy()
st.dataframe(
    display_table.style.format({
        "forecast": "{:,.0f}",
        "lower": "{:,.0f}",
        "upper": "{:,.0f}"
    }),
    use_container_width=True
)

csv_data = result.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download forecast as CSV",
    data=csv_data,
    file_name=f"{county.lower().replace(' ', '_')}_forecast.csv",
    mime="text/csv"
)

with st.expander("Method note"):
    st.markdown(
        """
This tool applies a county-specific model selected from three alternatives:
- Trend only
- Trend plus economic base
- Trend plus growth adjustment

Model selection is based on empirical fit and forecast performance. The framework is designed to reflect structural differences across counties rather than impose a single forecasting rule.
        """
    )