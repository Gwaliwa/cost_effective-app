import streamlit as st
import pandas as pd

st.set_page_config(page_title="CEA Helper", layout="wide")

st.title("Cost-Effectiveness Analysis (CEA) Helper")
st.write("A simple app to explore prospective and retrospective cost-effectiveness, inspired by J-PAL training examples.")

st.sidebar.header("Analysis type")
analysis_type = st.sidebar.selectbox(
    "What are you analyzing?",
    ["Prospective pilot", "Retrospective pilot", "Prospective scale-up"]
)

st.sidebar.header("Core inputs")
total_cost = st.sidebar.number_input("Total cost of the program (USD, per year or per cohort)", min_value=0.0, value=74800.0, step=1000.0)
n_beneficiaries = st.sidebar.number_input("Number of beneficiaries (e.g., children reached)", min_value=1, value=12000, step=100)
impact_per_child = st.sidebar.number_input("Impact per beneficiary (e.g., SD gain in test scores)", min_value=0.0, value=0.19, step=0.01)
threshold_sd_per_100 = st.sidebar.number_input("Threshold: minimum SD per $100 (optional)", min_value=0.0, value=1.40, step=0.1)

cost_per_child = total_cost / n_beneficiaries
ce_sd_per_100 = (impact_per_child * 100) / cost_per_child if cost_per_child > 0 else 0.0
cost_per_1sd = cost_per_child / impact_per_child if impact_per_child > 0 else float("inf")

st.subheader("A. Point estimate of cost-effectiveness")
col1, col2, col3 = st.columns(3)
col1.metric("Cost per child (USD)", f"{cost_per_child:,.2f}")
col2.metric("SD gained per $100", f"{ce_sd_per_100:,.2f}")
col3.metric("Cost per 1 SD (USD)", f"{cost_per_1sd:,.2f}" if cost_per_1sd != float("inf") else "N/A")

if threshold_sd_per_100 > 0:
    if ce_sd_per_100 >= threshold_sd_per_100:
        st.success(f"Based on your inputs, the intervention meets the threshold: {ce_sd_per_100:,.2f} ≥ {threshold_sd_per_100:,.2f} SD per $100.")
    else:
        st.warning(f"Based on your inputs, the intervention does NOT meet the threshold: {ce_sd_per_100:,.2f} < {threshold_sd_per_100:,.2f} SD per $100.")
else:
    st.info("No threshold specified. Add one in the sidebar to see a pass/fail message.")

st.subheader("B. Sensitivity analysis")
st.write("Adjust cost and impact to see how sensitive cost-effectiveness is to your assumptions.")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Cost scenarios (USD per child)**")
    cost_low = st.number_input("Low cost per child", min_value=0.0, value=max(cost_per_child * 0.8, 0.01), step=0.5)
    cost_high = st.number_input("High cost per child", min_value=0.0, value=cost_per_child * 1.2, step=0.5)
with c2:
    st.markdown("**Impact scenarios (SD per child)**")
    impact_low = st.number_input("Low impact per child", min_value=0.0, value=max(impact_per_child * 0.75, 0.0), step=0.01)
    impact_high = st.number_input("High impact per child", min_value=0.0, value=impact_per_child * 1.25, step=0.01)

scenarios = []
for label, c, imp in [
    ("Low cost, low impact", cost_low, impact_low),
    ("Low cost, high impact", cost_low, impact_high),
    ("High cost, low impact", cost_high, impact_low),
    ("High cost, high impact", cost_high, impact_high),
]:
    ce = (imp * 100) / c if c > 0 else 0.0
    scenarios.append({"Scenario": label, "Cost_per_child": c, "Impact_per_child_SD": imp, "SD_per_100USD": ce})

df_scenarios = pd.DataFrame(scenarios)
st.dataframe(df_scenarios)

st.subheader("C. Assumptions and interpretation notes")
st.markdown(
    """
- **Perspective:** These calculations are from an implementer/program perspective. To move toward a societal perspective, add opportunity costs (e.g., participant time, volunteer labor).
- **Uncertainty:** Prospective CEA (before a pilot) uses assumed costs and impacts based on other contexts. Retrospective CEA (after an RCT) uses observed costs and impacts, but may not generalize to scale or new regions.
- **Thresholds:** Your SD-per-$100 threshold is a policy choice, not a universal rule. It should reflect your budget constraints and priorities.
- **Scale-up:** At larger scale, costs per child may fall (economies of scale) or rise (logistics, weaker supervision), and impacts may change. Treat pilot CEAs as a starting point, not a guarantee.
- **Safe language:** Prefer: *“If our assumptions hold, the program is estimated to cost around $X per SD gained”* rather than *“The program will cost $X per SD gained everywhere.”*
"""
)

st.subheader("D. Optional: Upload an Excel file for multiple interventions")
uploaded = st.file_uploader("Upload an Excel file structured like the provided template (sheet: 'Interventions')", type=["xlsx"])
if uploaded is not None:
    try:
        df_up = pd.read_excel(uploaded, sheet_name="Interventions")
        # Derive CE columns if not already present
        if "Cost_per_child_USD" not in df_up.columns and {"Total_Cost_USD_per_year", "Number_of_children"}.issubset(df_up.columns):
            df_up["Cost_per_child_USD"] = df_up["Total_Cost_USD_per_year"] / df_up["Number_of_children"]
        if "CE_SD_per_100USD" not in df_up.columns and {"Impact_per_child_SD", "Cost_per_child_USD"}.issubset(df_up.columns):
            df_up["CE_SD_per_100USD"] = (df_up["Impact_per_child_SD"] * 100) / df_up["Cost_per_child_USD"]
        if "Cost_per_1SD_USD" not in df_up.columns and {"Impact_per_child_SD", "Cost_per_child_USD"}.issubset(df_up.columns):
            df_up["Cost_per_1SD_USD"] = df_up["Cost_per_child_USD"] / df_up["Impact_per_child_SD"]
        st.write("Computed cost-effectiveness for uploaded interventions:")
        st.dataframe(df_up)
    except Exception as e:
        st.error(f"Could not read Excel file: {e}")
