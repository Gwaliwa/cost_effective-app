import streamlit as st
import pandas as pd

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="CEA Helper", layout="wide")

st.title("Cost-Effectiveness Analysis (CEA) Helper")

st.write("""
This tool helps you compute cost-effectiveness (CE) with:
- **Cost per child**
- **Standard deviations (SD) gained per $100**
- **Cost per 1 SD gained**

It also:
- Allows **optional inflation adjustment** (using CPI ratios),
- Provides a simple **sensitivity analysis**, and
- Supports **batch analysis via Excel upload** with a template.
""")

# ===============================
# SIDEBAR: CORE INPUTS
# ===============================
st.sidebar.header("A. Core Inputs")

# Country is just a label – CPI must still be provided by the user
country = st.sidebar.text_input("Country / context label (optional)", value="West Ghana")

# --- Inflation toggle ---
use_inflation = st.sidebar.checkbox("Use inflation adjustment (CPI)?", value=False)

total_cost_nominal = st.sidebar.number_input(
    "Total cost (NOMINAL, in program currency; e.g., USD)",
    min_value=0.0,
    value=74800.0,
    step=1000.0
)

cost_year = st.sidebar.number_input("Cost year (e.g. 2018)", min_value=1900, max_value=2100, value=2018)
target_year = st.sidebar.number_input("Target price year (for real costs)", min_value=1900, max_value=2100, value=2024)

if use_inflation:
    st.sidebar.markdown("**CPI inputs (index values, not %)**")
    cpi_cost_year = st.sidebar.number_input("CPI in cost year", min_value=0.0001, value=100.0)
    cpi_target_year = st.sidebar.number_input("CPI in target year", min_value=0.0001, value=140.0)
else:
    cpi_cost_year = 100.0
    cpi_target_year = 100.0

n_beneficiaries = st.sidebar.number_input("Number of beneficiaries (children reached)", min_value=1, value=12000)
impact = st.sidebar.number_input("Impact per child (SD gain in literacy scores, etc.)", min_value=0.0, value=0.19, step=0.01)
threshold = st.sidebar.number_input("SD per $100 threshold (policy choice)", min_value=0.0, value=1.40, step=0.1)

# ===============================
# CORE CALCULATIONS
# ===============================

# Real cost via CPI ratio (if use_inflation == False, ratio = 1)
cpi_ratio = cpi_target_year / cpi_cost_year
total_cost_real = total_cost_nominal * cpi_ratio

cost_per_child_nominal = total_cost_nominal / n_beneficiaries
cost_per_child_real = total_cost_real / n_beneficiaries

ce_per_100_nominal = (impact * 100) / cost_per_child_nominal if cost_per_child_nominal > 0 else 0.0
ce_per_100_real = (impact * 100) / cost_per_child_real if cost_per_child_real > 0 else 0.0

cost_per_sd_nominal = cost_per_child_nominal / impact if impact > 0 else float("inf")
cost_per_sd_real = cost_per_child_real / impact if impact > 0 else float("inf")

# ===============================
# SECTION A. POINT ESTIMATES
# ===============================
st.subheader("A. Cost-Effectiveness Results")

st.markdown(f"**Context:** {country} | Cost year: {cost_year} | Target (real) year: {target_year}")

c1, c2, c3 = st.columns(3)
c1.metric("Cost per child (nominal)", f"${cost_per_child_nominal:,.2f}")
c2.metric("SD per $100 (nominal)", f"{ce_per_100_nominal:,.2f}")
c3.metric("Cost per 1 SD (nominal)", f"${cost_per_sd_nominal:,.2f}" if cost_per_sd_nominal != float("inf") else "N/A")

c4, c5, c6 = st.columns(3)
c4.metric("Cost per child (REAL, adjusted with CPI)", f"${cost_per_child_real:,.2f}")
c5.metric("SD per $100 (REAL)", f"{ce_per_100_real:,.2f}")
c6.metric("Cost per 1 SD (REAL)", f"${cost_per_sd_real:,.2f}" if cost_per_sd_real != float("inf") else "N/A")

# Threshold check using REAL SD per $100 (you can change this if you prefer nominal)
if threshold > 0:
    if ce_per_100_real >= threshold:
        st.success(
            f"Based on REAL cost, the intervention **meets the threshold**: "
            f"{ce_per_100_real:,.2f} ≥ {threshold:,.2f} SD per $100."
        )
    else:
        st.warning(
            f"Based on REAL cost, the intervention **does NOT meet the threshold**: "
            f"{ce_per_100_real:,.2f} < {threshold:,.2f} SD per $100."
        )
else:
    st.info("No threshold specified. Add one in the sidebar to see a pass/fail message.")

st.markdown("""
**Interpretation tip (safe language):**  
> *If our assumptions about costs, CPI, and impact hold, the program is estimated to cost around  
> ${:.2f} per 1 SD gained (real, in {} prices).*  
""".format(cost_per_sd_real, target_year))

# ===============================
# SECTION B. SENSITIVITY ANALYSIS
# ===============================
st.subheader("B. Sensitivity Analysis")

st.write("""
Sensitivity analysis helps you understand **uncertainty** by testing how cost-effectiveness changes
when **costs or impacts are higher or lower than expected**.

We use simple +/- percentages (you can adjust them) rather than confidence intervals,
because in prospective CEA we usually don't have full variance information.
""")

st.markdown("### Choose sensitivity ranges")

col_s1, col_s2 = st.columns(2)
with col_s1:
    cost_delta_pct = st.number_input("Cost variation (± %)", min_value=0.0, value=20.0, step=5.0)
with col_s2:
    impact_delta_pct = st.number_input("Impact variation (± %)", min_value=0.0, value=25.0, step=5.0)

cost_low = cost_per_child_real * (1 - cost_delta_pct / 100)
cost_high = cost_per_child_real * (1 + cost_delta_pct / 100)
impact_low = impact * (1 - impact_delta_pct / 100)
impact_high = impact * (1 + impact_delta_pct / 100)

scenarios = [
    ("Best case (Low cost + High impact)", cost_low, impact_high),
    ("Worst case (High cost + Low impact)", cost_high, impact_low),
    ("Low cost + Low impact", cost_low, impact_low),
    ("High cost + High impact", cost_high, impact_high),
]

rows = []
for label, c, imp in scenarios:
    ce = (imp * 100) / c if c > 0 else 0.0
    rows.append({
        "Scenario": label,
        "Cost_per_child_REAL_USD": round(c, 2),
        "Impact_per_child_SD": round(imp, 3),
        "SD_per_100USD_REAL": round(ce, 2),
    })

df_sensitivity = pd.DataFrame(rows)
st.dataframe(df_sensitivity)

st.markdown("""
**How to use this:**

- If **even the worst-case** scenario is above your threshold, the program is **robustly cost-effective**.
- If **only the best-case** scenario is above the threshold, the program is **fragile** — results depend heavily on optimistic assumptions.
- You can adjust the ±% bands to reflect your own judgement about how uncertain costs and impacts are.
""")

# ===============================
# SECTION C. DOWNLOAD RESULTS
# ===============================
st.subheader("C. Download Point Results")

df_results = pd.DataFrame({
    "Country/Context": [country],
    "Cost_year": [cost_year],
    "Target_year": [target_year],
    "Total_cost_nominal": [total_cost_nominal],
    "Total_cost_real": [total_cost_real],
    "Cost_per_child_nominal": [round(cost_per_child_nominal, 4)],
    "Cost_per_child_real": [round(cost_per_child_real, 4)],
    "Impact_per_child_SD": [impact],
    "SD_per_100USD_nominal": [round(ce_per_100_nominal, 4)],
    "SD_per_100USD_real": [round(ce_per_100_real, 4)],
    "Cost_per_1SD_nominal": [round(cost_per_sd_nominal, 4)],
    "Cost_per_1SD_real": [round(cost_per_sd_real, 4)],
    "Threshold_SD_per_100USD": [threshold],
})

st.download_button(
    "Download cost-effectiveness results (CSV)",
    df_results.to_csv(index=False),
    "CEA_point_results.csv",
    "text/csv",
)

# Also allow download of sensitivity analysis
st.download_button(
    "Download sensitivity analysis (CSV)",
    df_sensitivity.to_csv(index=False),
    "CEA_sensitivity_results.csv",
    "text/csv",
)

# ===============================
# SECTION D. BATCH ANALYSIS VIA EXCEL
# ===============================
st.subheader("D. Upload Excel for Batch CEA")

st.markdown("""
**Expected columns in your Excel (sheet: `Interventions`):**

- `Intervention_Name`  
- `Context/Country`  
- `CEA_Type` (e.g. Prospective_Pilot, Retrospective_Pilot)  
- `Total_Cost_USD_per_year`  
- `Number_of_children`  
- `Impact_per_child_SD`  
- *(Optional, for inflation)* `Cost_Year`, `CPI_Cost_Year`, `Target_Price_Year`, `CPI_Target_Year`
""")

uploaded = st.file_uploader("Upload an Excel file", type=["xlsx"])

use_batch_inflation = st.checkbox(
    "Apply CPI-based real cost adjustment for uploaded file (if CPI columns exist)?",
    value=False
)

if uploaded:
    try:
        df_up = pd.read_excel(uploaded, sheet_name="Interventions")
    except Exception as e:
        st.error(f"Could not read Excel file: {e}")
    else:
        # If inflation columns exist and user wants it, compute real cost; else use nominal.
        if use_batch_inflation and {"Cost_Year", "CPI_Cost_Year", "Target_Price_Year", "CPI_Target_Year", "Total_Cost_USD_per_year"}.issubset(df_up.columns):
            df_up["Total_Cost_Real_USD_per_year"] = df_up["Total_Cost_USD_per_year"] * (
                df_up["CPI_Target_Year"] / df_up["CPI_Cost_Year"]
            )
            cost_col_name = "Total_Cost_Real_USD_per_year"
        else:
            cost_col_name = "Total_Cost_USD_per_year"

        # Derive CE columns
        if {"Number_of_children", "Impact_per_child_SD", cost_col_name}.issubset(df_up.columns):
            df_up["Cost_per_child_USD"] = df_up[cost_col_name] / df_up["Number_of_children"]
            df_up["SD_per_100USD"] = (df_up["Impact_per_child_SD"] * 100) / df_up["Cost_per_child_USD"]
            df_up["Cost_per_1SD_USD"] = df_up["Cost_per_child_USD"] / df_up["Impact_per_child_SD"]

        st.write("Computed cost-effectiveness for uploaded interventions:")
        st.dataframe(df_up.round(3))

        st.download_button(
            "Download batch CEA results (CSV)",
            df_up.to_csv(index=False),
            "CEA_batch_results.csv",
            "text/csv",
        )

# ===============================
# SECTION E. SHORT REMINDER ON ASSUMPTIONS
# ===============================

st.subheader("E. Key Assumptions to Remember")

st.markdown("""
- **Perspective:** This is closer to a *program/implementer* perspective. To move toward a *societal* perspective,
  add opportunity costs like participant time, volunteer time, etc.
- **Inflation:** Real costs are computed as  
  `Real cost = Nominal cost × (CPI_target_year / CPI_cost_year)`.
- **CPI:** CPI is an index (e.g. 2018 = 100, 2024 = 140). The **ratio** of indices is what matters.
- **Uncertainty:** Prospective CE uses assumed impact from other contexts and forecasted costs.
  Retrospective CE uses actual data from one pilot. Neither directly predicts scale-up performance.
- **Sensitivity analysis:** We do simple ±% around costs and impacts. This is not a formal confidence interval, but
  a way to see how fragile or robust your CE is to plausible changes.
- **Language:** Use cautious statements like:  
  *"If our assumptions hold, ATI-ASR is estimated to cost about $X per 1 SD gained in literacy."*
""")
