import pandas as pd
import os

# ============================================================
# MODULE 10E — UBD
# USER BEHAVIOR DESCRIPTOR
# ============================================================

print("=" * 70)
print("MODULE 10E — UBD")
print("USER BEHAVIOR DESCRIPTOR")
print("=" * 70)

BASE_DIR = r"E:\energy_project\behavior_output"

ATF_FILE = os.path.join(
    BASE_DIR,
    "appliance_temporal_fingerprint.csv"
)

ERI_FILE = os.path.join(
    BASE_DIR,
    "energy_routine_index.csv"
)

DSC_FILE = os.path.join(
    BASE_DIR,
    "demand_stability_change.csv"
)

CDI_FILE = os.path.join(
    BASE_DIR,
    "cdi_summary.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "user_behavior_descriptor.csv"
)

# ============================================================
# CHECK FILES
# ============================================================

files = {
    "ATF": ATF_FILE,
    "ERI": ERI_FILE,
    "DSC": DSC_FILE,
    "CDI": CDI_FILE
}

for name, path in files.items():
    if not os.path.exists(path):
        print(f"ERROR: Missing {name} file:")
        print(path)
        raise SystemExit(1)

print("\nAll required behavior files found.")

# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading ATF...")
atf = pd.read_csv(ATF_FILE)

print("Loading ERI...")
eri = pd.read_csv(ERI_FILE)

print("Loading DSC...")
dsc = pd.read_csv(DSC_FILE)

print("Loading CDI...")
cdi = pd.read_csv(CDI_FILE)

print("\nINPUT SHAPES")
print("ATF:", atf.shape)
print("ERI:", eri.shape)
print("DSC:", dsc.shape)
print("CDI:", cdi.shape)

# ============================================================
# STANDARDIZE APPLIANCE COLUMN
# ============================================================

for df in [atf, eri, dsc, cdi]:

    if "appliance" not in df.columns:
        print("ERROR: appliance column missing.")
        print(df.columns.tolist())
        raise SystemExit(1)

    df["appliance"] = df["appliance"].astype(str).str.strip().str.lower()

# ============================================================
# SELECT USEFUL ATF FEATURES
# ============================================================

atf_cols = [
    "appliance",
    "avg_power_w",
    "max_power_w",
    "power_std_w",
    "total_energy_kwh",
    "on_percentage"
]

atf_selected = atf[
    [c for c in atf_cols if c in atf.columns]
].copy()

# ============================================================
# SELECT ERI FEATURES
# ============================================================

eri_cols = [
    "appliance",
    "hourly_power_consistency",
    "hourly_energy_consistency",
    "hourly_on_consistency",
    "weekly_power_consistency",
    "weekly_on_consistency",
    "weekday_weekend_consistency",
    "temporal_coverage",
    "energy_routine_index",
    "routine_class"
]

eri_selected = eri[
    [c for c in eri_cols if c in eri.columns]
].copy()

# ============================================================
# SELECT DSC FEATURES
# ============================================================

dsc_cols = [
    "appliance",
    "coefficient_variation",
    "mean_change_lag1_w",
    "mean_change_lag5_w",
    "high_change_percentage",
    "status_change_rate",
    "hourly_cv",
    "weekly_cv",
    "weekend_weekday_change_pct",
    "stability_score",
    "change_score",
    "dsc_score",
    "demand_class"
]

dsc_selected = dsc[
    [c for c in dsc_cols if c in dsc.columns]
].copy()

# ============================================================
# SELECT CDI FEATURES
# ============================================================

cdi_cols = [
    "appliance",
    "on_percentage",
    "peak_hour",
    "peak_hour_power_w",
    "most_active_hour",
    "most_active_hour_power_w",
    "weekday_mean_power_w",
    "weekend_mean_power_w",
    "weekend_weekday_change_pct",
    "status_change_count",
    "coefficient_variation",
    "peak_to_average_ratio",
    "interaction_intensity",
    "temporal_interaction_score",
    "activity_score",
    "stability_component",
    "interaction_component",
    "weekend_component",
    "cdi_score",
    "interaction_class"
]

cdi_selected = cdi[
    [c for c in cdi_cols if c in cdi.columns]
].copy()

# ============================================================
# REMOVE DUPLICATE COLUMNS BEFORE MERGING
# ============================================================

for df in [atf_selected, eri_selected, dsc_selected, cdi_selected]:
    df.drop_duplicates(
        subset=["appliance"],
        keep="first",
        inplace=True
    )

# ============================================================
# MERGE BEHAVIORAL DESCRIPTORS
# ============================================================

print("\nMerging ATF + ERI + DSC + CDI...")

ubd = atf_selected.merge(
    eri_selected,
    on="appliance",
    how="outer",
    suffixes=("", "_eri")
)

ubd = ubd.merge(
    dsc_selected,
    on="appliance",
    how="outer",
    suffixes=("", "_dsc")
)

ubd = ubd.merge(
    cdi_selected,
    on="appliance",
    how="outer",
    suffixes=("", "_cdi")
)

# ============================================================
# HANDLE DUPLICATED METRICS
# ============================================================

if "on_percentage_eri" in ubd.columns:
    ubd.drop(columns=["on_percentage_eri"], inplace=True)

if "on_percentage_dsc" in ubd.columns:
    ubd.drop(columns=["on_percentage_dsc"], inplace=True)

if "on_percentage_cdi" in ubd.columns:
    ubd.drop(columns=["on_percentage_cdi"], inplace=True)

# ============================================================
# CREATE NORMALIZED BEHAVIOR COMPONENTS
# ============================================================

def normalize(series):
    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(0.0, index=series.index)

    if maximum == minimum:
        return pd.Series(1.0, index=series.index)

    return (series - minimum) / (maximum - minimum)


# ERI component
if "energy_routine_index" in ubd.columns:
    ubd["routine_component"] = normalize(
        ubd["energy_routine_index"]
    )
else:
    ubd["routine_component"] = 0.0


# DSC stability component
if "stability_score" in ubd.columns:
    ubd["stability_behavior_component"] = normalize(
        ubd["stability_score"]
    )
else:
    ubd["stability_behavior_component"] = 0.0


# CDI component
if "cdi_score" in ubd.columns:
    ubd["interaction_behavior_component"] = normalize(
        ubd["cdi_score"]
    )
else:
    ubd["interaction_behavior_component"] = 0.0


# ============================================================
# USER BEHAVIOR SCORE
# ============================================================

ubd["user_behavior_score"] = (
    ubd["routine_component"] * 0.35
    + ubd["stability_behavior_component"] * 0.30
    + ubd["interaction_behavior_component"] * 0.35
) * 100

# ============================================================
# BEHAVIOR CLASSIFICATION
# ============================================================

def classify_behavior(score):

    if score >= 75:
        return "Highly Predictable"

    elif score >= 50:
        return "Predictable"

    elif score >= 25:
        return "Moderately Predictable"

    else:
        return "Variable"


ubd["behavior_class"] = ubd[
    "user_behavior_score"
].apply(classify_behavior)

# ============================================================
# BEHAVIOR PROFILE
# ============================================================

def profile(row):

    routine = row["routine_component"]
    stability = row["stability_behavior_component"]
    interaction = row["interaction_behavior_component"]

    components = {
        "Routine Driven": routine,
        "Stable Demand": stability,
        "Interactive Usage": interaction
    }

    return max(
        components,
        key=components.get
    )


ubd["dominant_behavior"] = ubd.apply(
    profile,
    axis=1
)

# ============================================================
# ROUND NUMERIC VALUES
# ============================================================

numeric_cols = ubd.select_dtypes(
    include=["float64", "float32"]
).columns

ubd[numeric_cols] = ubd[numeric_cols].round(6)

# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("UBD VALIDATION")
print("=" * 70)

print("\nROWS:", len(ubd))
print("COLUMNS:", len(ubd.columns))

print("\nNULLS:")

nulls = ubd.isna().sum()

print(
    nulls[nulls > 0]
    if (nulls > 0).any()
    else "NO NULLS"
)

print("\nUSER BEHAVIOR SCORE RANGE:")

print(
    round(ubd["user_behavior_score"].min(), 4),
    "to",
    round(ubd["user_behavior_score"].max(), 4)
)

print("\nBEHAVIOR CLASSES:")

print(
    ubd[
        [
            "appliance",
            "user_behavior_score",
            "behavior_class",
            "dominant_behavior"
        ]
    ].to_string(index=False)
)

# ============================================================
# SAVE
# ============================================================

ubd.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("MODULE 10E COMPLETE")
print("=" * 70)

print(ubd[
    [
        "appliance",
        "user_behavior_score",
        "behavior_class",
        "dominant_behavior"
    ]
].to_string(index=False))

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)