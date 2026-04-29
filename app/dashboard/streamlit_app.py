import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import os

# --- API CONFIG ---
API_URL = "http://localhost:8000"

# --- PAGE CONFIG ---
st.set_page_config(page_title="Peakstack Energy Platform", layout="wide")

# Modern SaaS CSS - Executive Professional Mode
st.markdown("""
    <style>
    .main { background-color: #0f172a; }

    /* Global Container */
    .main-container {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 24px;
        padding: 30px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3) !important;
        color: #f8fafc !important;
    }

    /* KPI Cards */
    .kpi-card {
        background: #1e293b !important;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155 !important;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    .kpi-card:hover {
        border: 1px solid #38bdf8 !important;
        transform: translateY(-2px);
    }

    /* Decision Card */
    .decision-card {
        background: linear-gradient(135deg, #065f46 0%, #064e3b 100%);
        color: #ccfbf1;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #10b981;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-bottom: 30px;
    }
    .decision-card-negative {
        background: linear-gradient(135deg, #7f1d1d 0%, #450a0a 100%);
        color: #fee2e2;
        padding: 30px;
        border-radius: 20px;
        border: 1px solid #ef4444;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        margin-bottom: 30px;
    }

    /* Context Strip */
    .context-strip {
        background: #1e293b;
        border-radius: 12px;
        padding: 10px 20px;
        color: #94a3b8;
        font-size: 14px;
        text-align: center;
        border: 1px solid #334155;
        margin-bottom: 30px;
    }

    /* Summary Banner */
    .summary-banner {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10b981;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 30px;
    }

    /* Cost Strip */
    .cost-strip {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-bottom: 30px;
        color: #f8fafc;
    }

    /* Insights Card */
    .insights-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 25px;
        color: #f8fafc;
    }

    /* Step Indicator */
    .step-indicator {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-bottom: 20px;
    }
    .step {
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 500;
        color: #64748b;
        background: #0f172a;
        border: 1px solid #334155;
    }
    .step-active {
        background: #38bdf8;
        color: #0f172a;
        border-color: #38bdf8;
    }
    .footer {
        text-align: center;
        color: #64748b;
        font-size: 12px;
        margin-top: 50px;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.header("⚙️ Config")
dark_mode = st.sidebar.toggle("🌙 Dark Mode Interface", value=True)
industry = st.sidebar.selectbox("Industry Type", ["Manufacturing", "Data Center", "Commercial Building", "Cold Storage", "Hospital"], index=0)

st.sidebar.markdown("### 📁 Data Input")
data_mode = st.sidebar.radio("Data Source", ["Demo Mode", "Real Mode"], index=0)
csv_path = None
if data_mode == "Real Mode":
    uploaded_file = st.sidebar.file_uploader("Upload EB Load Data (CSV)", type=["csv"])
    if uploaded_file:
        try:
            response = requests.post(f"{API_URL}/upload-data", files={"file": uploaded_file})
            if response.status_code == 200:
                st.sidebar.success("Data uploaded!")
        except Exception as e:
            st.sidebar.error(f"API Error: {e}")
        csv_path = f"data/uploads/{uploaded_file.name}"

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Quick Scenarios")
scenario_col1, scenario_col2 = st.sidebar.columns(2)
with scenario_col1:
    if st.sidebar.button("🏭 High Peak"):
        st.session_state.batt_cap, st.session_state.batt_pwr = 1200, 400
        st.session_state.solar_cap, st.session_state.wind_cap = 200, 50
with scenario_col2:
    if st.sidebar.button("☀️ Solar Rich"):
        st.session_state.batt_cap, st.session_state.batt_pwr = 600, 200
        st.session_state.solar_cap, st.session_state.wind_cap = 800, 100

if st.sidebar.button("🔋 DG Heavy Site", use_container_width=True):
    st.session_state.batt_cap, st.session_state.batt_pwr = 1000, 300
    st.session_state.solar_cap, st.session_state.wind_cap = 100, 50

st.sidebar.markdown("---")
st.sidebar.markdown("### 🛠️ System Parameters")
state = st.sidebar.selectbox("Select State", ["Maharashtra", "Gujarat", "Karnataka", "Tamil Nadu", "Rajasthan", "Telangana", "Uttar Pradesh"])
batt_cap = st.sidebar.slider("Battery Capacity (kWh)", 100, 2000, st.session_state.get('batt_cap', 600), 100)
batt_pwr = st.sidebar.slider("Battery Max Power (kW)", 50, 500, st.session_state.get('batt_pwr', 200), 50)
solar_cap = st.sidebar.slider("Solar Capacity (kW)", 0, 1000, st.session_state.get('solar_cap', 400), 50)
wind_cap = st.sidebar.slider("Wind Capacity (kW)", 0, 500, st.session_state.get('wind_cap', 100), 50)

st.session_state.batt_cap, st.session_state.batt_pwr = batt_cap, batt_pwr
st.session_state.solar_cap, st.session_state.wind_cap = solar_cap, wind_cap

if st.sidebar.button("💾 Save Scenario", use_container_width=True):
    if 'scenarios' not in st.session_state: st.session_state.scenarios = []
    st.session_state.scenarios.append({"name": f"Scenario {len(st.session_state.scenarios)+1}", "params": {"batt_cap": batt_cap, "batt_pwr": batt_pwr, "solar_cap": solar_cap, "wind_cap": wind_cap, "state": state, "industry": industry}})
    st.sidebar.success("Scenario saved!")

net_metering = st.sidebar.toggle("Enable Net Metering", value=False)
include_emerging_tech = st.sidebar.toggle("Include Emerging Tech", value=False)
run_btn = st.sidebar.button("🚀 Run Analysis", type="primary", use_container_width=True)

def call_analyze_api(params):
    try:
        resp = requests.post(f"{API_URL}/analyze", json=params)
        return resp.json() if resp.status_code == 200 else None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- MAIN CONTENT START ---
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 1. TOP CONTROL BAR
control_col1, control_col2 = st.columns([6, 2])
with control_col1:
    current_step = "Step 1: Configure" if not st.session_state.get('analysis_done', False) else "Step 2: Analyze"
    step_html = f'<div class="step-indicator"><div class="step {"step-active" if current_step == "Step 1: Configure" else ""}">Step 1: Configure</div><div class="step {"step-active" if current_step == "Step 2: Analyze" else ""}">Step 2: Analyze</div><div class="step {"step-active" if current_step == "Step 3: Decision" else ""}">Step 3: Decision</div></div>'
    st.markdown(step_html, unsafe_allow_html=True)

with control_col2:
    if st.session_state.get('analysis_done', False):
        if st.button("📄 Download Report", use_container_width=True):
            report_id = st.session_state.api_result.get('report_id')
            if report_id:
                st.markdown(f"### [Download PDF]({API_URL}/analyze/report/{report_id})")

# Header
h_col1, h_col2 = st.columns([1, 6])
with h_col1: st.image("assets/logo.png", width=100)
with h_col2:
    st.markdown("<h1 style='margin:0; color:#f8fafc;'>PEAKSTACK ENERGY</h1>", unsafe_allow_html=True)
    st.markdown("<span style='color:#94a3b8; font-size:14px;'>Smart Energy Investment Platform</span>", unsafe_allow_html=True)

if run_btn:
    with st.spinner("Analyzing..."):
        params = {"state": state, "battery_capacity_kwh": batt_cap, "battery_power_kw": batt_pwr, "solar_capacity_kw": solar_cap, "wind_capacity_kw": wind_cap, "net_metering_enabled": net_metering, "include_emerging_tech": include_emerging_tech, "mode": "real" if data_mode == "Real Mode" else "demo", "csv_file_path": csv_path}
        result = call_analyze_api(params)
        if result:
            st.session_state.analysis_done, st.session_state.api_result = True, result

if st.session_state.get('analysis_done', False):
    tab1, tab2 = st.tabs(["📈 Executive Summary", "🧪 What-If Analysis"])

    with tab1:
        data = st.session_state.api_result
        sum_data, rec_data, res_data, bill_data = data['summary'], data['recommendation'], data['results'], data.get('bill_breakdown', {})

        # 2. SUMMARY BANNER
        st.markdown(f"""
        <div class="summary-banner">
            <p style="font-size: 22px; color: #f8fafc; margin: 0;">
                This facility can save <b style="color: #34d399; font-size: 28px;">₹{sum_data['daily_savings']*30:,.0f}/month</b> with a <b style="color: #38bdf8; font-size: 24px;">{rec_data['size']:.0f} kWh</b> BESS system.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 3. CONTEXT STRIP
        st.markdown(f'<div class="context-strip">Industry: {industry} | Location: {state} | Tariff: Industrial HT | Model: Behind-the-Meter</div>', unsafe_allow_html=True)

        # 4. HERO DECISION CARD
        if rec_data.get('decision') == "INSTALL":
            st.markdown(f"""
            <div class="decision-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 40px;">✅</span>
                        <h2 style="margin: 0; color: white; font-size: 32px;">INSTALL BESS</h2>
                    </div>
                    <div style="display: flex; gap: 30px; text-align: right;">
                        <div>
                            <span style="display: block; font-size: 12px; color: #ccfbf1;">SIZE</span>
                            <b style="font-size: 20px;">{rec_data['size']:.0f} kWh</b>
                        </div>
                        <div>
                            <span style="display: block; font-size: 12px; color: #ccfbf1;">PAYBACK</span>
                            <b style="font-size: 20px;">{sum_data['payback_years']:.1f} Yrs</b>
                        </div>
                        <div>
                            <span style="display: block; font-size: 12px; color: #ccfbf1;">CONFIDENCE</span>
                            <span style="background: #16a34a; padding: 2px 8px; border-radius: 8px; font-size: 14px; font-weight: bold;">{rec_data['confidence']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="decision-card-negative">
                <h2 style="margin: 0; color: white; font-size: 32px; text-align: center;">❌ DO NOT INSTALL</h2>
                <p style="text-align: center; font-size: 18px; color: #fee2e2;">{rec_data.get('reasoning', 'Investment not viable')}</p>
            </div>
            """, unsafe_allow_html=True)

        # 5. KPI CARDS
        k1, k2, k3 = st.columns(3)
        with k1:
            st.markdown(f"""<div class="kpi-card">
                <span style="color: #94a3b8; font-size: 12px; font-weight: bold;">MONTHLY SAVINGS</span>
                <div style="font-size: 36px; font-weight: bold; color: #38bdf8; margin: 10px 0;">₹{sum_data["daily_savings"]*30:,.0f}</div>
                <span style="color: #34d399; font-size: 14px;">↑ {sum_data["savings_pct"]:.1f}% Reduction</span>
            </div>""", unsafe_allow_html=True)
        with k2:
            st.markdown(f"""<div class="kpi-card">
                <span style="color: #94a3b8; font-size: 12px; font-weight: bold;">PAYBACK PERIOD</span>
                <div style="font-size: 36px; font-weight: bold; color: #f8fafc; margin: 10px 0;">{sum_data["payback_years"]:.1f} Years</div>
                <span style="color: #64748b; font-size: 14px;">Projected ROI</span>
            </div>""", unsafe_allow_html=True)
        with k3:
            st.markdown(f"""<div class="kpi-card">
                <span style="color: #94a3b8; font-size: 12px; font-weight: bold;">PEAK REDUCTION</span>
                <div style="font-size: 36px; font-weight: bold; color: #f8fafc; margin: 10px 0;">{sum_data["peak_reduction_pct"]:.1f}%</div>
                <span style="color: #64748b; font-size: 14px;">Demand Shift</span>
            </div>""", unsafe_allow_html=True)

        # 6. COST COMPARISON STRIP
        baseline_total = bill_data.get('total_bill', 0) * 1.15 if bill_data else 0
        st.markdown(f"""
        <div class="cost-strip">
            <div style="text-align: center;">
                <span style="color: #94a3b8; font-size: 12px;">WITHOUT BESS</span>
                <div style="font-size: 20px; font-weight: bold;">₹{baseline_total:,.0f}</div>
            </div>
            <div style="text-align: center; font-size: 24px; color: #38bdf8; font-weight: bold;">➔</div>
            <div style="text-align: center;">
                <span style="color: #94a3b8; font-size: 12px;">WITH BESS</span>
                <div style="font-size: 20px; font-weight: bold;">₹{bill_data.get('total_bill', 0):,.0f}</div>
            </div>
            <div style="text-align: center; margin-left: 40px;">
                <span style="color: #34d399; font-size: 12px; font-weight: bold;">MONTHLY SAVINGS</span>
                <div style="font-size: 24px; font-weight: bold; color: #34d399;">₹{baseline_total - bill_data.get('total_bill', 0):,.0f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 7. CHARTS & INSIGHTS
        c_left, c_right = st.columns([3, 1])
        with c_left:
            st.markdown("### 📉 Energy Performance")
            fig_load = go.Figure()
            fig_load.add_trace(go.Scatter(y=res_data['load'], name="Demand", line=dict(color='#475569', width=1)))
            fig_load.add_trace(go.Scatter(y=res_data['grid_import'], name="Optimized", line=dict(color='#38bdf8', width=3)))
            fig_load.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20),
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                 font_color='#94a3b8', xaxis_title=None, yaxis_title="kW")
            st.plotly_chart(fig_load, use_container_width=True)

        with c_right:
            st.markdown("### 🧠 Insights")
            st.markdown(f"""
            <div class="insights-card">
                <p style="margin: 0 0 15px 0; color: #38bdf8; font-weight: bold;">Decision Drivers</p>
                <ul style="padding-left: 20px; margin: 0; color: #cbd5e1; font-size: 14px; line-height: 1.6;">
                    <li>{rec_data.get('reasoning', ['Optimization focus'])[0] if isinstance(rec_data.get('reasoning'), list) else rec_data.get('reasoning', 'N/A')}</li>
                    <li>Optimal Size: {rec_data['size']:.0f} kWh</li>
                    <li>Tech: {rec_data['tech']}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.header("🧪 What-If Analysis")
        st.info("Adjust parameters below to see real-time impact on ROI and savings.")

        wi_col1, wi_col2 = st.columns([1, 2])
        with wi_col1:
            wi_batt_cap = st.slider("Battery Capacity (kWh)", 100, 2000, batt_cap, 100)
            wi_batt_pwr = st.slider("Battery Max Power (kW)", 50, 500, batt_pwr, 50)
            wi_solar_cap = st.slider("Solar Capacity (kW)", 0, 1000, solar_cap, 50)
            wi_wind_cap = st.slider("Wind Capacity (kW)", 0, 500, wind_cap, 50)
            if st.button("🚀 Run What-If", type="primary", use_container_width=True):
                wi_params = {"state": state, "battery_capacity_kwh": wi_batt_cap, "battery_power_kw": wi_batt_pwr, "solar_capacity_kw": wi_solar_cap, "wind_capacity_kw": wi_wind_cap, "net_metering_enabled": net_metering, "include_emerging_tech": include_emerging_tech, "mode": "real" if data_mode == "Real Mode" else "demo", "csv_file_path": csv_path, "fast_mode": True}
                wi_result = call_analyze_api(wi_params)
                if wi_result: st.session_state.what_if_result = wi_result

        with wi_col2:
            if st.session_state.get('what_if_result'):
                wi_data = st.session_state.what_if_result
                wi_sum = wi_data['summary']
                orig_sum = st.session_state.api_result['summary']

                st.markdown("### 📊 ROI Shift")
                m1, m2, m3 = st.columns(3)
                with m1:
                    diff = (wi_sum['daily_savings']*30) - (orig_sum['daily_savings']*30)
                    st.metric("Monthly Savings", f"₹{wi_sum['daily_savings']*30:,.0f}", f"₹{diff:,.0f}")
                with m2:
                    diff_p = wi_sum['payback_years'] - orig_sum['payback_years']
                    st.metric("Payback", f"{wi_sum['payback_years']:.1f} Yrs", f"{diff_p:.1f} Yrs")
                with m3:
                    diff_peak = wi_sum['peak_reduction_pct'] - orig_sum['peak_reduction_pct']
                    st.metric("Peak Red.", f"{wi_sum['peak_reduction_pct']:.1f}%", f"{diff_peak:.1f}%")

                if st.button("✅ Commit to Full Report", type="primary", use_container_width=True):
                    full_params = {"state": state, "battery_capacity_kwh": wi_batt_cap, "battery_power_kw": wi_batt_pwr, "solar_capacity_kw": wi_solar_cap, "wind_capacity_kw": wi_wind_cap, "net_metering_enabled": net_metering, "include_emerging_tech": include_emerging_tech, "mode": "real" if data_mode == "Real Mode" else "demo", "csv_file_path": csv_path, "fast_mode": False}
                    full_res = call_analyze_api(full_params)
                    if full_res:
                        st.session_state.api_result, st.session_state.analysis_done = full_res, True
                        st.success("Updated! Switching to Executive Summary...")

else:
    st.info("👈 Configure parameters in the sidebar and click 'Run Analysis' to start.")

st.markdown('<div class="footer">Powered by BESS Investment Advisor | Industrial Energy SaaS v1.0</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
