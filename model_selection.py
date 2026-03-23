import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_percentage_error

INPUT_FILE = "osr_data.xlsx"
MODEL_SELECTION_FILE = "model_selection.xlsx"
FULL_RESULTS_XLSX = "county_osr_model_comparison_3models.xlsx"
FULL_RESULTS_CSV = "county_osr_model_comparison_3models.csv"

MIN_OBS = 3
ELIG_CORR = 0.5


def mape_levels(y_true_ln, y_pred_ln):
    return mean_absolute_percentage_error(np.exp(y_true_ln), np.exp(y_pred_ln))


def read_excel_robust(filepath):
    raw = pd.read_excel(filepath)
    if isinstance(raw, dict):
        if len(raw) == 0:
            raise ValueError("Excel file has no sheets.")
        first_sheet = list(raw.keys())[0]
        raw = raw[first_sheet]
    return raw


def standardise_columns(df):
    df = df.copy()

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
        "GCP": "gcp",
        "gcp": "gcp",
        "gcp_nominal": "gcp",
    }
    df = df.rename(columns=rename_map)

    needed = ["county", "year", "osr", "gcp"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing columns after renaming: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    df = df.loc[:, ~df.columns.duplicated()].copy()

    df["county"] = df["county"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["osr"] = pd.to_numeric(df["osr"], errors="coerce")
    df["gcp"] = pd.to_numeric(df["gcp"], errors="coerce")

    df = df.dropna(subset=["county", "year", "osr", "gcp"]).copy()
    df = df[(df["osr"] > 0) & (df["gcp"] > 0)].copy()

    df["year"] = df["year"].astype(int)
    df = df.sort_values(["county", "year"]).reset_index(drop=True)

    df["ln_osr"] = np.log(df["osr"])
    df["ln_gcp"] = np.log(df["gcp"])

    return df


def select_models(df, min_obs=MIN_OBS, elig_corr=ELIG_CORR):
    out = []

    print("Rows after cleaning:", len(df))
    print("Counties after cleaning:", df["county"].nunique())

    for county, g in df.groupby("county"):
        g = g.sort_values("year").copy()
        g = g.dropna(subset=["ln_osr", "ln_gcp", "osr", "gcp"])

        if len(g) < min_obs:
            continue

        g["t"] = np.arange(len(g))
        corr = g["ln_osr"].corr(g["ln_gcp"])

        row = {
            "county": county,
            "n_obs": int(len(g)),
            "year_min": int(g["year"].min()),
            "year_max": int(g["year"].max()),
            "corr_ln_osr_ln_gcp": float(corr) if pd.notna(corr) else np.nan,
        }

        # Model A: trend only
        XA = sm.add_constant(g[["t"]], has_constant="add")
        mA = sm.OLS(g["ln_osr"], XA).fit()
        predA = mA.predict(XA)

        row.update({
            "A_a": float(mA.params["const"]),
            "A_b": float(mA.params["t"]),
            "A_r2": float(mA.rsquared),
            "A_mape": float(mape_levels(g["ln_osr"], predA)),
        })

        # Defaults
        row.update({
            "B_gamma": np.nan,
            "B_r2": np.nan,
            "B_mape": np.nan,
            "C_gamma_g": np.nan,
            "C_r2": np.nan,
            "C_mape": np.nan,
            "economic_model_eligible": False,
            "recommended_model": "A_trend_only",
            "best_mape": float(row["A_mape"]),
        })

        eligible = pd.notna(corr) and (corr >= elig_corr)
        row["economic_model_eligible"] = bool(eligible)

        if eligible:
            # Model B: trend + elasticity
            XB = sm.add_constant(g[["t", "ln_gcp"]], has_constant="add")
            mB = sm.OLS(g["ln_osr"], XB).fit()
            gammaB = float(mB.params["ln_gcp"])

            if gammaB >= 0:
                predB = mB.predict(XB)
                row.update({
                    "B_gamma": gammaB,
                    "B_r2": float(mB.rsquared),
                    "B_mape": float(mape_levels(g["ln_osr"], predB)),
                })

            # Model C: trend + growth adjustment
            gC = g.copy()
            gC["dln_osr"] = gC["ln_osr"].diff()
            gC["dln_gcp"] = gC["ln_gcp"].diff()
            gC = gC.dropna(subset=["dln_osr", "dln_gcp"]).copy()

            if len(gC) >= 4:
                XC = sm.add_constant(gC[["dln_gcp"]], has_constant="add")
                mC = sm.OLS(gC["dln_osr"], XC).fit()
                gammaC = max(float(mC.params["dln_gcp"]), 0.0)

                g_align = g.iloc[1:].copy()
                base = mA.predict(sm.add_constant(g_align[["t"]], has_constant="add"))
                growth_adj = gammaC * (
                    g_align["ln_gcp"].values - g.iloc[:-1]["ln_gcp"].values
                )
                predC = base.values + growth_adj

                row.update({
                    "C_gamma_g": gammaC,
                    "C_r2": float(mC.rsquared),
                    "C_mape": float(mape_levels(g_align["ln_osr"], predC)),
                })

        candidates = {
            "A_trend_only": row["A_mape"],
            "B_trend_plus_elasticity": row["B_mape"],
            "C_trend_plus_growth": row["C_mape"],
        }
        candidates = {k: v for k, v in candidates.items() if pd.notna(v)}

        if len(candidates) == 0:
            continue

        best_model = min(candidates, key=candidates.get)
        row["recommended_model"] = best_model
        row["best_mape"] = float(candidates[best_model])

        out.append(row)

    if len(out) == 0:
        raise ValueError(
            "No county models were estimated. Check the input file structure, "
            "column mapping, or observation thresholds."
        )

    final = pd.DataFrame(out).sort_values(["best_mape", "county"]).reset_index(drop=True)
    return final


def main():
    raw = read_excel_robust(INPUT_FILE)
    df = standardise_columns(raw)

    print("\nFirst rows:")
    print(df.head())
    print("\nColumns:")
    print(df.columns.tolist())
    print("\nCounty counts:")
    print(df.groupby("county").size().head())

    final = select_models(df)

    full_results = final[[
        "county", "n_obs", "year_min", "year_max", "corr_ln_osr_ln_gcp",
        "A_a", "A_b", "A_r2", "A_mape",
        "B_gamma", "B_r2", "B_mape",
        "C_gamma_g", "C_r2", "C_mape",
        "economic_model_eligible", "recommended_model", "best_mape"
    ]].copy()

    num_cols = full_results.select_dtypes(include=[np.number]).columns
    full_results[num_cols] = full_results[num_cols].round(4)

    model_selection = final[["county", "recommended_model"]].copy()

    full_results.to_excel(FULL_RESULTS_XLSX, index=False)
    full_results.to_csv(FULL_RESULTS_CSV, index=False)
    model_selection.to_excel(MODEL_SELECTION_FILE, index=False)

    print("\nSaved:", FULL_RESULTS_XLSX)
    print("Saved:", FULL_RESULTS_CSV)
    print("Saved:", MODEL_SELECTION_FILE)
    print("\nModel distribution:")
    print(model_selection["recommended_model"].value_counts())


if __name__ == "__main__":
    main()