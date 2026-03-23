import numpy as np
import pandas as pd
import statsmodels.api as sm


def forecast_county(df, final, county, horizon=4):
    g = df[df["county"] == county].sort_values("year").copy()

    if g.empty:
        raise ValueError(f"No data found for county: {county}")

    needed = ["county", "year", "osr", "gcp", "ln_osr", "ln_gcp"]
    missing = [c for c in needed if c not in g.columns]
    if missing:
        raise ValueError(f"Missing required columns in df: {missing}")

    g = g.loc[:, needed].copy()
    g = g.loc[:, ~g.columns.duplicated()].copy()

    model_row = final.loc[final["county"] == county]
    if model_row.empty:
        raise ValueError(f"No selected model found for county: {county}")

    model_name = model_row["recommended_model"].iloc[0]

    g["t"] = np.arange(len(g))

    if model_name == "B_trend_plus_elasticity":
        X = sm.add_constant(g[["t", "ln_gcp"]], has_constant="add")
    else:
        X = sm.add_constant(g[["t"]], has_constant="add")

    model = sm.OLS(g["ln_osr"], X).fit()

    last_t = int(g["t"].iloc[-1])
    last_year = int(g["year"].max())

    future = pd.DataFrame({
        "county": county,
        "year": np.arange(last_year + 1, last_year + 1 + horizon),
        "osr": np.nan,
        "gcp": np.nan,
        "ln_osr": np.nan,
        "ln_gcp": np.nan,
        "t": np.arange(last_t + 1, last_t + 1 + horizon)
    })

    if model_name == "B_trend_plus_elasticity":
        gcp_trend = sm.OLS(
            g["ln_gcp"],
            sm.add_constant(g[["t"]], has_constant="add")
        ).fit()
        future["ln_gcp"] = gcp_trend.predict(
            sm.add_constant(future[["t"]], has_constant="add")
        )

    cols = ["county", "year", "osr", "gcp", "ln_osr", "ln_gcp", "t"]
    g_all = pd.concat([g[cols], future[cols]], ignore_index=True, axis=0)

    if model_name == "B_trend_plus_elasticity":
        X_all = sm.add_constant(g_all[["t", "ln_gcp"]], has_constant="add")
    else:
        X_all = sm.add_constant(g_all[["t"]], has_constant="add")

    pred = model.get_prediction(X_all).summary_frame(alpha=0.05)

    g_all["forecast"] = np.exp(pred["mean"])
    g_all["lower"] = np.exp(pred["mean_ci_lower"])
    g_all["upper"] = np.exp(pred["mean_ci_upper"])

    fitted = np.exp(model.fittedvalues)
    actual = np.exp(g["ln_osr"])
    mape = np.mean(np.abs(actual - fitted) / actual)
    r2 = model.rsquared

    result = g_all[["year", "forecast", "lower", "upper"]].copy()
    metrics = {
        "r2": float(r2),
        "mape": float(mape),
        "model_name": model_name
    }

    return result, metrics