
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(
    page_title="GovCon Proposal Cost Build & Profitability Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #003865 0%, #005a9e 100%);
        padding: 24px 32px; border-radius: 8px; margin-bottom: 24px;
    }
    .main-header h1 { color: white; font-size: 24px; margin: 0; font-weight: 600; }
    .main-header p  { color: #b3d1f0; font-size: 13px; margin: 6px 0 0; }
    .kpi-card {
        background: white; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 16px 20px;
        border-left: 4px solid #003865;
    }
    .kpi-label { font-size: 11px; color: #64748b; font-weight: 600;
                 text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { font-size: 24px; color: #1a1a2e; font-weight: 700; margin: 4px 0; }
    .kpi-sub   { font-size: 12px; color: #64748b; }
    .section-header {
        font-size: 14px; font-weight: 600; color: #003865;
        border-bottom: 2px solid #003865;
        padding-bottom: 6px; margin: 24px 0 16px;
    }
    div[data-testid="stSidebar"] { background: #f8fafc; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base = os.path.join(os.path.dirname(__file__), "data")
    return {
        "contracts":     pd.read_csv(os.path.join(base, "contracts.csv")),
        "profitability": pd.read_csv(os.path.join(base, "profitability.csv")),
        "labor":         pd.read_csv(os.path.join(base, "labor_categories.csv")),
        "indirect":      pd.read_csv(os.path.join(base, "indirect_rates.csv")),
    }

d = load_data()
contracts, profitability, labor, indirect = (
    d["contracts"], d["profitability"], d["labor"], d["indirect"]
)

fringe_base   = float(indirect.loc[indirect["rate_type"] == "Fringe",   "base_rate"].values[0])
overhead_base = float(indirect.loc[indirect["rate_type"] == "Overhead", "base_rate"].values[0])
ga_base       = float(indirect.loc[indirect["rate_type"] == "G&A",      "base_rate"].values[0])

with st.sidebar:
    st.markdown("### Navigation")
    module = st.radio("Select Module", [
        "Proposal Cost Build",
        "Indirect Rate Scenario Analysis",
        "Program Profitability Dashboard",
        "Data Sources and Methodology",
    ])
    st.markdown("---")
    st.markdown(
        "<small style='color:#94a3b8'>"
        "<b>GovCon Proposal Cost Build</b><br>"
        "<b>& Profitability Dashboard</b><br><br>"
        "Built by Prakash Balasubramanian<br><br>"
        "Contract data: USASpending.gov<br>"
        "Rates: DCAA benchmarks<br>"
        "Actuals: Modeled synthetic data<br><br>"
        "Companion Excel model available on GitHub</small>",
        unsafe_allow_html=True
    )

st.markdown("""
<div class="main-header">
  <h1>GovCon Proposal Cost Build & Program Profitability Dashboard</h1>
  <p>Proposal Pricing | Indirect Rate Stack | Scenario Analysis | Program Margin Tracking
  | Contract data: USASpending.gov | Rates: DCAA benchmarks
  | Companion Excel cost model available on GitHub</p>
</div>
""", unsafe_allow_html=True)

# ===================================================
# MODULE 1 - PROPOSAL COST BUILD
# ===================================================
if module == "Proposal Cost Build":
    st.markdown("<div class='section-header'>Proposal Cost Buildup</div>", unsafe_allow_html=True)
    st.caption(
        "This module replicates the cost buildup a Project Financial Analyst prepares when supporting a new proposal. "
        "Direct labor is burdened with Fringe, Overhead, and G&A to produce a fully wrapped cost. "
        "Fee is then applied based on contract type. "
        "Hours and bill rates are benchmarked to GSA Multiple Award Schedule for NAICS 541."
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("**Direct Labor Inputs**")
        labor_display = labor[["labor_category","hours","bill_rate","direct_labor"]].copy()
        labor_display.columns = ["Labor Category","Hours","Bill Rate ($/hr)","Direct Labor Cost"]
        labor_display["Bill Rate ($/hr)"]  = labor_display["Bill Rate ($/hr)"].apply(lambda x: f"${x:,.0f}")
        labor_display["Direct Labor Cost"] = labor_display["Direct Labor Cost"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(labor_display, use_container_width=True, hide_index=True)
        total_dl = labor["direct_labor"].sum()
        st.markdown(f"**Total Direct Labor: ${total_dl:,.0f}**")

    with col_right:
        st.markdown("**Indirect Cost Stack**")
        st.caption("Rates benchmarked to DCAA provisional rate guidance for NAICS 541.")
        fringe_cost   = total_dl * fringe_base
        overhead_cost = total_dl * overhead_base
        subtotal      = total_dl + fringe_cost + overhead_cost
        ga_cost       = subtotal * ga_base
        tci           = subtotal + ga_cost

        stack = pd.DataFrame([
            {"Cost Element": "Direct Labor",                "Rate": "",                            "Amount": f"${total_dl:,.0f}"},
            {"Cost Element": "Fringe",                      "Rate": f"{fringe_base*100:.1f}%",     "Amount": f"${fringe_cost:,.0f}"},
            {"Cost Element": "Overhead",                    "Rate": f"{overhead_base*100:.1f}%",   "Amount": f"${overhead_cost:,.0f}"},
            {"Cost Element": "Subtotal (DL + Fringe + OH)", "Rate": "",                            "Amount": f"${subtotal:,.0f}"},
            {"Cost Element": "G&A",                         "Rate": f"{ga_base*100:.1f}%",         "Amount": f"${ga_cost:,.0f}"},
            {"Cost Element": "Total Cost Input (TCI)",      "Rate": "",                            "Amount": f"${tci:,.0f}"},
        ])
        st.dataframe(stack, use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Fee and Total Price by Contract Type</div>", unsafe_allow_html=True)
    st.caption(
        "Fee mechanics differ by contract type. "
        "CPFF fee is fixed at award — cost overruns reduce profit. "
        "T&M fee is earned per hour billed — no ceiling risk. "
        "FFP fee is residual — the less you spend the more you keep."
    )
    fee_rates = {
        "Cost-Plus-Fixed-Fee (CPFF)": 0.07,
        "Time and Materials (T&M)":   0.10,
        "Firm-Fixed-Price (FFP)":     0.12,
    }
    fee_rows = []
    for ctype, frate in fee_rates.items():
        fee_amt     = tci * frate
        total_price = tci + fee_amt
        margin_pct  = fee_amt / total_price * 100
        fee_rows.append({
            "Contract Type": ctype,
            "Fee Rate":      f"{frate*100:.1f}%",
            "Fee Amount":    f"${fee_amt:,.0f}",
            "Total Price":   f"${total_price:,.0f}",
            "Gross Margin":  f"{margin_pct:.1f}%",
        })
    st.dataframe(pd.DataFrame(fee_rows), use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Cost Composition</div>", unsafe_allow_html=True)
    labels = ["Direct Labor","Fringe","Overhead","G&A","Fee (FFP)"]
    values = [total_dl, fringe_cost, overhead_cost, ga_cost, tci * 0.12]
    colors = ["#003865","#005a9e","#1e7fc2","#7fb3d3","#b3d1f0"]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=colors,
        text=[f"${v/1e3:.0f}K" for v in values], textposition="outside"
    ))
    fig.update_layout(
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=40,b=20,l=40,r=20),
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9"),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ===================================================
# MODULE 2 - INDIRECT RATE SCENARIO ANALYSIS
# ===================================================
elif module == "Indirect Rate Scenario Analysis":
    st.markdown("<div class='section-header'>Indirect Rate Scenario Analysis</div>", unsafe_allow_html=True)
    st.caption(
        "Adjust indirect rates to model how changes in provisional rates affect total contract price and margin. "
        "This replicates the what-if analysis a financial analyst performs before proposal submission "
        "or when DCAA issues revised provisional rates mid-contract."
    )

    total_dl = labor["direct_labor"].sum()
    col_ctrl, col_out = st.columns([1, 2])

    with col_ctrl:
        st.markdown("**Adjust Rates**")
        fringe   = st.slider("Fringe (%)",   20, 45, int(fringe_base*100)) / 100
        overhead = st.slider("Overhead (%)", 30, 60, int(overhead_base*100)) / 100
        ga       = st.slider("G&A (%)",       8, 20, int(ga_base*100)) / 100
        contract_type = st.selectbox("Contract Type", ["CPFF (7%)","T&M (10%)","FFP (12%)"])
        fee_map  = {"CPFF (7%)": 0.07, "T&M (10%)": 0.10, "FFP (12%)": 0.12}
        fee_rate = fee_map[contract_type]
        st.markdown("---")
        st.markdown("**DCAA Benchmark Ranges**")
        st.markdown("Fringe: 29% to 36%")
        st.markdown("Overhead: 41% to 51%")
        st.markdown("G&A: 10% to 15%")
        st.caption("Source: DCAA provisional rate guidance NAICS 541")

    fringe_cost   = total_dl * fringe
    overhead_cost = total_dl * overhead
    subtotal      = total_dl + fringe_cost + overhead_cost
    ga_cost       = subtotal * ga
    tci           = subtotal + ga_cost
    fee_amt       = tci * fee_rate
    total_price   = tci + fee_amt
    margin_pct    = fee_amt / total_price * 100

    base_subtotal = total_dl * (1 + fringe_base + overhead_base)
    base_tci      = base_subtotal * (1 + ga_base)
    base_total    = base_tci * (1 + fee_rate)

    with col_out:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Cost Input", f"${tci:,.0f}",         delta=f"${tci-base_tci:+,.0f} vs base")
        c2.metric("Fee Amount",       f"${fee_amt:,.0f}")
        c3.metric("Total Price",      f"${total_price:,.0f}", delta=f"${total_price-base_total:+,.0f} vs base")
        c4.metric("Gross Margin",     f"{margin_pct:.1f}%")

        scenarios  = ["Low Rates","Base Case","High Rates","Current"]
        fringe_s   = [0.29, fringe_base, 0.36, fringe]
        overhead_s = [0.41, overhead_base, 0.51, overhead]
        ga_s       = [0.10, ga_base, 0.15, ga]
        bar_colors = ["#16a34a","#003865","#dc2626","#d97706"]

        prices = []
        for f,o,g in zip(fringe_s, overhead_s, ga_s):
            sub = total_dl * (1 + f + o)
            t   = sub * (1 + g)
            prices.append(t * (1 + fee_rate))

        fig = go.Figure(go.Bar(
            x=scenarios, y=prices, marker_color=bar_colors,
            text=[f"${p/1e3:.0f}K" for p in prices], textposition="outside"
        ))
        fig.add_hline(y=base_total, line_dash="dot", line_color="#003865",
                      annotation_text="Base Case", annotation_position="top right")
        fig.update_layout(
            height=300, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=40,b=20,l=40,r=20),
            yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9"),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    price_swing = prices[2] - prices[0]
    st.info(
        f"At current settings (Fringe: {fringe*100:.0f}%, Overhead: {overhead*100:.0f}%, G&A: {ga*100:.0f}%), "
        f"the total {contract_type} contract price is ${total_price:,.0f}. "
        f"The swing between low and high rate scenarios is ${price_swing:,.0f} — "
        f"a {price_swing/prices[0]*100:.1f}% difference in total price. "
        f"This represents the financial risk a program manager must account for "
        f"when DCAA adjusts provisional rates mid-contract."
    )

# ===================================================
# MODULE 3 - PROGRAM PROFITABILITY DASHBOARD
# ===================================================
elif module == "Program Profitability Dashboard":
    st.markdown("<div class='section-header'>Program Profitability Dashboard</div>", unsafe_allow_html=True)
    st.caption(
        "Tracks revenue, cost, and gross margin by contract over time. "
        "Contract ceiling and award data sourced from USASpending.gov. "
        "Monthly actuals are synthetic projections calibrated to real award values."
    )

    summary = profitability.groupby(["contract_id","contract_name","contract_type"]).agg(
        total_cost=("cost_incurred","sum"),
        total_revenue=("revenue","sum"),
        total_margin=("gross_margin","sum"),
    ).reset_index()
    summary = summary.merge(
        contracts[["contract_id","award_id","contract_ceiling","fee_rate"]], on="contract_id"
    )
    summary["margin_pct"]  = summary["total_margin"] / summary["total_revenue"] * 100
    summary["pct_ceiling"] = summary["total_cost"] / summary["contract_ceiling"] * 100
    summary["fee_at_risk"] = summary.apply(
        lambda r: max(0,(r["total_cost"]/r["contract_ceiling"]-0.90)*r["contract_ceiling"]*r["fee_rate"]),
        axis=1
    )

    c1,c2,c3,c4 = st.columns(4)
    for col,label,value,sub in zip(
        [c1,c2,c3,c4],
        ["Total Portfolio Revenue","Total Costs Incurred","Total Gross Margin","Avg Margin Rate"],
        [f"${summary['total_revenue'].sum()/1e6:.2f}M",
         f"${summary['total_cost'].sum()/1e6:.2f}M",
         f"${summary['total_margin'].sum()/1e3:.0f}K",
         f"{summary['total_margin'].sum()/summary['total_revenue'].sum()*100:.1f}%"],
        ["Across 3 contracts","YTD actuals","YTD across portfolio","Portfolio blended"]
    ):
        col.markdown(f"""<div class='kpi-card'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Profitability by Contract</div>", unsafe_allow_html=True)
    disp = summary[[
        "award_id","contract_name","contract_type",
        "total_cost","total_revenue","total_margin","margin_pct","fee_at_risk"
    ]].copy()
    disp.columns = ["Award ID","Contract","Type","Total Cost","Revenue","Gross Margin","Margin %","Fee at Risk"]
    for c in ["Total Cost","Revenue","Gross Margin","Fee at Risk"]:
        disp[c] = disp[c].apply(lambda x: f"${x:,.0f}")
    disp["Margin %"] = disp["Margin %"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.markdown("<div class='section-header'>Monthly Margin Trend</div>", unsafe_allow_html=True)
    col_filter, _ = st.columns([1,3])
    with col_filter:
        selected = st.selectbox("Filter by Contract",
                                ["All Contracts"] + contracts["contract_name"].tolist())

    if selected == "All Contracts":
        plot_data = profitability.groupby("month")[
            ["cost_incurred","revenue","gross_margin"]
        ].sum().reset_index()
        plot_data["margin_pct"] = plot_data["gross_margin"] / plot_data["revenue"] * 100
        title = "All Contracts"
    else:
        plot_data = profitability[profitability["contract_name"] == selected].copy()
        title = selected

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=plot_data["month"], y=plot_data["gross_margin"],
        name="Gross Margin $", marker_color="#003865", opacity=0.85
    ))
    fig.add_trace(go.Scatter(
        x=plot_data["month"], y=plot_data["margin_pct"],
        name="Margin %", yaxis="y2",
        line=dict(color="#e85d04", width=2), mode="lines+markers"
    ))
    fig.update_layout(
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(t=20,b=40,l=40,r=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        yaxis=dict(tickprefix="$", tickformat=",.0f", gridcolor="#f1f5f9", title="Gross Margin ($)"),
        yaxis2=dict(ticksuffix="%", overlaying="y", side="right", title="Margin %", showgrid=False),
        xaxis=dict(gridcolor="#f1f5f9")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div class='section-header'>Analyst Commentary</div>", unsafe_allow_html=True)
    best  = summary.loc[summary["margin_pct"].idxmax()]
    worst = summary.loc[summary["margin_pct"].idxmin()]
    total_far = summary["fee_at_risk"].sum()
    st.markdown(
        f"Portfolio blended margin is "
        f"**{summary['total_margin'].sum()/summary['total_revenue'].sum()*100:.1f}%** "
        f"across 3 active contracts. "
        f"Highest margin contract: **{best['contract_name']}** ({best['contract_type']}) "
        f"at **{best['margin_pct']:.1f}%**. "
        f"Lowest margin contract: **{worst['contract_name']}** ({worst['contract_type']}) "
        f"at **{worst['margin_pct']:.1f}%** — recommend reviewing labor mix and subcontractor "
        f"utilization on this program. "
        f"Total fee at risk across portfolio: **${total_far:,.0f}**. "
        f"Recommend escalating to program leadership if cost trajectory does not improve by next EAC cycle."
    )

# ===================================================
# MODULE 4 - DATA SOURCES AND METHODOLOGY
# ===================================================
elif module == "Data Sources and Methodology":
    st.markdown("<div class='section-header'>Data Sources and Methodology</div>", unsafe_allow_html=True)
    st.markdown(
        "This project uses a hybrid data approach. "
        "Real public procurement data is used where available. "
        "Professionally modeled synthetic data is used where real data is proprietary by law."
    )

    st.markdown("#### What Is Real")
    real_data = pd.DataFrame([
        {"Data Element": "Contract award numbers",
         "Value": "75FCMC22F0046 | 70T02021F7560N005 | 75N97023F00001",
         "Source": "USASpending.gov"},
        {"Data Element": "Awarding agencies",
         "Value": "HHS/CMS | Dept. of Homeland Security | HHS/NIH",
         "Source": "USASpending.gov"},
        {"Data Element": "Contract ceiling values",
         "Value": "$8.07M | $1.01M | $7.34M",
         "Source": "USASpending.gov cumulative obligations"},
        {"Data Element": "Indirect rate ranges",
         "Value": "Fringe 29-36%, Overhead 41-51%, G&A 10-15%",
         "Source": "DCAA provisional rate guidance for NAICS 541"},
        {"Data Element": "Labor bill rate benchmarks",
         "Value": "GSA Schedule SIN rates for IT and consulting",
         "Source": "GSA Multiple Award Schedule"},
        {"Data Element": "CPFF fee cap",
         "Value": "7% per FAR 15.404-4",
         "Source": "Federal Acquisition Regulation"},
    ])
    st.dataframe(real_data, use_container_width=True, hide_index=True)

    st.markdown("#### What Is Modeled (Synthetic)")
    st.info(
        "Monthly cost actuals, labor hours, and profitability data are synthetic projections. "
        "In a live GovCon environment this data lives inside Deltek Costpoint and is never publicly disclosed. "
        "This model replicates the structure and math exactly."
    )
    synth_data = pd.DataFrame([
        {"Data Element": "Monthly cost actuals",
         "Why Synthetic": "Internal contractor records — never publicly disclosed"},
        {"Data Element": "Revenue by period",
         "Why Synthetic": "Derived from synthetic cost actuals and fee rates"},
        {"Data Element": "Gross margin by month",
         "Why Synthetic": "Derived from synthetic revenue and cost"},
        {"Data Element": "Labor hours by category",
         "Why Synthetic": "Internal timesheet data — proprietary"},
        {"Data Element": "Proposal labor inputs",
         "Why Synthetic": "Pre-award cost estimates — proprietary"},
    ])
    st.dataframe(synth_data, use_container_width=True, hide_index=True)

    st.markdown("#### Excel Cost Model")
    st.markdown(
        "A companion Excel proposal cost model was built alongside this dashboard. "
        "It contains the full cost buildup, indirect rate stack, fee by contract type, "
        "scenario analysis, and profitability tracker across all four tabs. "
        "It is available for download on GitHub and replicates the exact deliverable "
        "a Project Financial Analyst would send to a program manager or pricing lead."
    )

    st.markdown("#### Sources")
    st.markdown(
        "USASpending.gov — Official federal spending transparency database (DATA Act, P.L. 113-101). "
        "DCAA — Defense Contract Audit Agency provisional rate guidance. "
        "GSA Multiple Award Schedule — Publicly available labor category bill rates. "
        "FAR 15.404-4 — Federal Acquisition Regulation fee limitations for CPFF contracts. "
        "RELI Group Inc UEI: ZZEFBLYZN5B1 | CAGE: 6VJE6."
    )
