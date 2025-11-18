import streamlit as st
import pandas as pd

st.set_page_config(page_title="CEA Helper", layout="wide")

st.title("Cost-Effectiveness Analysis (CEA) Helper")

st.write("""
This tool calculates cost-effectiveness (CE) using:
- Cost per child
- SD gained per $100
- Cost per 1 SD gain
You can enter values manually or upload an Excel file using the template.
""")

# -------------------------------
# SIDEBAR INPUTS
# -------------------------------
st.sidebar.header("Manual Input")

total_cost = st.sidebar.number_input("Total cost (USD)", min_value=0.0, value=74800.0)
n_beneficiaries = st.sidebar.number_input("Number of beneficiaries", min_value=1, value=12000)
impact = st.sidebar.number_input("Impact per child (SD)", min_value=0.0, value=0.19)
threshold = st.sidebar.number_input("SD per $100 threshold", min_value=0.0, value=1.40)

# -------------------------------
# COMPUTE MAIN CE VALUES
# -------------------------------
cost_per_child = total_cost / n_beneficiaries
ce_per_100 = (impact * 100) / cost_per_child
cost_per_sd = cost_per_child / impact if impact > 0 else float("inf")

st.subheader("A. Cost-Effectiveness Results")
col1, col2, col3 = st.columns(3)

col1.metric("Cost per child", f"${cost_per_child:.2f}")
col2.metric("SD per $100", f"{ce_per_100:.2f}")
col3.metric("Cost per 1 SD", f"${cost_per_sd:.2f}")

# Threshold assessment
if ce_per_100 >= threshold:
    st.success(f"The intervention meets the threshold ({ce_per_100:.2f} ≥ {threshold}).")
else:
    st.warning(f"The intervention does NOT meet the threshold ({ce_per_100:.2f} < {threshold}).")

# -------------------------------
# SENSITIVITY ANALYSIS
# -------------------------------
st.subheader("B. Sensitivity Analysis")
st.write("""
Sensitivity analysis helps you understand uncertainty by testing how cost-effectiveness changes 
when costs or impacts are higher or lower than expected.
""")

low_cost = cost_per_child * 0.8
high_cost = cost_per_child * 1.2
low_impact = impact * 0.75
high_impact = impact * 1.25

scenarios = [
    ("Best case (Low cost + High impact)", low_cost, high_impact),
    ("Worst case (High cost + Low impact)", high_cost, low_impact),
    ("Low cost + Low impact", low_cost, low_impact),
    ("High cost + High impact", high_cost, high_impact),
]

sensitivity_rows = []
for label, c, imp in scenarios:
    ce = (imp * 100) / c
    sensitivity_rows.append({
        "Scenario": label,
        "Cost per child": round(c, 2),
        "Impact per child (SD)": round(imp, 3),
        "SD per $100": round(ce, 2),
    })

df_sensitivity = pd.DataFrame(sensitivity_rows)
st.dataframe(df_sensitivity)

# -------------------------------
# DOWNLOAD RESULTS
# -------------------------------
st.subheader("C. Download Results")

df_results = pd.DataFrame({
    "Cost_per_child_USD": [round(cost_per_child, 2)],
    "SD_per_100USD": [round(ce_per_100, 2)],
    "Cost_per_1SD_USD": [round(cost_per_sd, 2)]
})

st.download_button(
    "Download cost-effectiveness results (CSV)",
    df_results.to_csv(index=False),
    "CEA_results.csv",
    "text/csv"
)

# -------------------------------
# UPLOAD EXCEL OPTION
# -------------------------------
st.subheader("D. Upload Excel (Batch CEA)")

uploaded = st.file_uploader("Upload Excel template", type=["xlsx"])
if uploaded:
    df_up = pd.read_excel(uploaded)
    df_up["Cost_per_child_USD"] = df_up["Total_Cost_USD_per_year"] / df_up["Number_of_children"]
    df_up["SD_per_100USD"] = (df_up["Impact_per_child_SD"] * 100) / df_up["Cost_per_child_USD"]
    df_up["Cost_per_1SD_USD"] = df_up["Cost_per_child_USD"] / df_up["Impact_per_child_SD"]

    st.write("Computed cost-effectiveness:")
    st.dataframe(df_up.round(2))

    st.download_button(
        "Download batch results (CSV)",
        df_up.to_csv(index=False),
        "CEA_batch_results.csv",
        "text/csv"
    )
