import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import io

# ==========================================
# 1. PAGE CONFIGURATION & CLEAN CSS OVERRIDE
# ==========================================
st.set_page_config(page_title="MRP Lot Sizing Calculator", layout="wide")

st.markdown("""
    <style>
    html, body, .stApp {
        background-color: #faf8f2;
        color: #111111;
    }
    
    h1, h2, h3 {
        color: #6a0708 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #6a0708 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5,
    [data-testid="stSidebar"] h6,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #f4efdc !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stSidebar"] input {
        color: #111111 !important;
        font-weight: normal !important;
        background-color: #ffffff !important;
    }
    
    .stButton>button {
        background-color: #6a0708 !important;
        color: #faf8f2 !important;
        border-radius: 4px !important;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #d90429 !important;
    }
    
    .text-justify {
        text-align: justify !important;
        line-height: 1.5 !important;
        font-size: 14px !important;
    }

    .glossary-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 6px;
        border: 1px solid #e0dbcd;
        border-top: 4px solid #6a0708;
        min-height: 160px;
        margin-bottom: 10px;
    }
    .glossary-title {
        color: #6a0708;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 6px;
    }
    
    .math-justify .katex-display {
        text-align: justify !important;
        margin-left: 0px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 MRP Lot Sizing Calculator")
st.markdown("---")


# ==========================================
# 2. GLOSSARY SECTION
# ==========================================
st.subheader("📚 Glossary")

g_r1c1, g_r1c2, g_r1c3, g_r1c4 = st.columns(4)
with g_r1c1:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>📋 1. Lot-for-Lot (L4L)</div><div class='text-justify'><b>Concept:</b> Orders exact net requirements per discrete period, no more and no less.<br><b>Function:</b> Eliminates holding cost entirely by zeroing out inventory between periods.</div></div>""", unsafe_allow_html=True)
with g_r1c2:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>🎯 2. Economic Order Quantity (EOQ)</div><div class='text-justify'><b>Concept:</b> Derives a fixed optimal lot size by balancing setup cost against holding cost using average demand.<br><b>Function:</b> Minimizes total inventory cost under stable, predictable demand conditions.</div></div>""", unsafe_allow_html=True)
with g_r1c3:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>⏱️ 3. Period Order Quantity (POQ)</div><div class='text-justify'><b>Concept:</b> Converts the EOQ quantity into a time-based ordering interval (number of periods per order).<br><b>Function:</b> Provides a stable ordering frequency derived automatically from cost parameters.</div></div>""", unsafe_allow_html=True)
with g_r1c4:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>🔒 4. Fixed Order Quantity (FOQ)</div><div class='text-justify'><b>Concept:</b> Orders a predetermined fixed quantity (or its multiples) set by supplier or operational constraints.<br><b>Function:</b> Standardizes order sizes for environments with rigid container or pallet sizing.</div></div>""", unsafe_allow_html=True)

g_r2c1, g_r2c2, g_r2c3, g_r2c4 = st.columns(4)
with g_r2c1:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>📅 5. Fixed Period Requirements (FPR)</div><div class='text-justify'><b>Concept:</b> Accumulates net requirements over a manually defined fixed period window and places one order at the window start.<br><b>Function:</b> Gives planners direct control over ordering frequency without relying on cost-derived intervals.</div></div>""", unsafe_allow_html=True)
with g_r2c2:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>💰 6. Incremental Unit Cost (IUC)</div><div class='text-justify'><b>Concept:</b> Evaluates the marginal cost per unit added when extending the lot to cover one more period, stopping when this marginal cost rises.<br><b>Function:</b> Captures true marginal cost dynamics, distinguishing it from LUC which uses cumulative average.</div></div>""", unsafe_allow_html=True)
with g_r2c3:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>💸 7. Least Total Cost (LTC)</div><div class='text-justify'><b>Concept:</b> Adds periods to the current lot until cumulative holding cost meets or exceeds the setup cost, then stops.<br><b>Function:</b> Achieves rough cost balance between setup and holding through a simple threshold comparison.</div></div>""", unsafe_allow_html=True)
with g_r2c4:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>🔍 8. Least Unit Cost (LUC)</div><div class='text-justify'><b>Concept:</b> Iteratively adds future periods to the lot and stops when the total cost per unit (setup + holding) starts to increase.<br><b>Function:</b> Minimizes average cost per unit ordered across the consolidation window.</div></div>""", unsafe_allow_html=True)

g_r3c1, g_r3c2, g_r3c3, g_r3c4 = st.columns(4)
with g_r3c1:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>⚖️ 9. Part Period Balancing (PPB)</div><div class='text-justify'><b>Concept:</b> Searches for the lot coverage that brings cumulative holding cost (in part-periods) closest to the Economic Part Period (EPP = Setup/Holding).<br><b>Function:</b> Balances setup and holding costs by targeting an equilibrium part-period value.</div></div>""", unsafe_allow_html=True)
with g_r3c2:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>🚀 10. Silver-Meal (SM)</div><div class='text-justify'><b>Concept:</b> Stops adding periods when the average total cost per period covered begins to rise, rather than per unit.<br><b>Function:</b> Performs well under volatile demand by optimizing cost per time period rather than per unit.</div></div>""", unsafe_allow_html=True)
with g_r3c3:
    st.markdown("""<div class='glossary-card'><div class='glossary-title'>🔬 11. Wagner-Whitin (WW)</div><div class='text-justify'><b>Concept:</b> Uses dynamic programming to evaluate all possible lot combinations across the entire planning horizon simultaneously.<br><b>Function:</b> Guarantees the mathematically global minimum total cost — the benchmark all heuristics are measured against.</div></div>""", unsafe_allow_html=True)
with g_r3c4:
    st.markdown("""<div class='glossary-card' style='background-color: #faf8f2; border: 1px solid #e0dbcd; border-top: 4px solid #e0dbcd;'><div class='text-justify' style='color: #aaa; font-size: 13px; padding-top: 8px;'>MOQ is not a lot sizing method — it is a universal supplier constraint applied on top of any method. Enable it via the sidebar.</div></div>""", unsafe_allow_html=True)

st.markdown("---")


# ==========================================
# 3. SIDEBAR PARAMETER INPUTS
# ==========================================
st.sidebar.header("⚙️ Control Dashboard")

st.sidebar.subheader("💰 Financial Factors")
setup_cost = st.sidebar.number_input("Setup Cost", min_value=0.0, value=100.0, step=5.0)
holding_cost = st.sidebar.number_input("Holding Cost (per unit/period)", min_value=0.0, value=2.0, step=0.5)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🗂️ Inventory Profiles")
initial_inv = st.sidebar.number_input("Initial Inventory", min_value=0, value=20, step=5)
safety_stock = st.sidebar.number_input("Safety Stock", min_value=0, value=0, step=1)
lead_time = st.sidebar.number_input("Lead Time", min_value=0, value=1, step=1)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🏭 Operational Boundaries")
max_capacity = st.sidebar.number_input("Maximum Warehouse Capacity (Units)", min_value=1, value=500, step=10)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🔧 Universal Constraint")
use_moq = st.sidebar.checkbox("Apply MOQ Constraint to All Methods", value=False)
moq_value = st.sidebar.number_input("MOQ Value (units)", min_value=1, value=50, step=5, disabled=not use_moq)
moq_val = moq_value if use_moq else 0


# ==========================================
# UTILITY CORE HELPERS
# ==========================================
def find_matching_column(columns, targets):
    for col in columns:
        col_clean = str(col).strip().lower().replace("_", "").replace(" ", "")
        if col_clean in targets:
            return col
    return None

def style_mrp_grid(df_transposed, max_cap, ss):
    def check_capacity(row):
        styles = []
        if row.name == 'Projected On Hand':
            for val in row:
                if val > max_cap:
                    styles.append('background-color: #ffe0b2; color: #6a0708; font-weight: bold;')
                elif val < ss:
                    styles.append('background-color: #ffcdd2; color: #b71c1c; font-weight: bold;')
                else:
                    styles.append('')
            return styles
        return [''] * len(row)
    return df_transposed.style.apply(check_capacity, axis=1)

def style_iteration_rows(df_step):
    style_matrix = pd.DataFrame('', index=df_step.index, columns=df_step.columns)
    for idx, row in df_step.iterrows():
        status_str = str(row['Status'])
        if "Stop" in status_str:
            style_matrix.loc[idx] = 'background-color: #ffebee; color: #c62828; font-weight: bold;'
        elif "Selected" in status_str or "Horizon End" in status_str or "Optimal" in status_str:
            style_matrix.loc[idx] = 'background-color: #e8f5e9; color: #2e7d32; font-weight: bold;'
    return style_matrix


# ==========================================
# 4. DATA ACQUISITION WORKBENCH
# ==========================================
st.subheader("📊 Data Input workbench")

input_method = st.radio(
    "Select Input Configuration Method:", 
    ["Upload File", "Manual Entry", "Load Template"]
)

df_workbench = None

if input_method == "Upload File":
    uploaded_file = st.file_uploader("Upload demand documents (.csv, .xlsx)", type=["csv", "xlsx"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
                
            col_p = find_matching_column(df_raw.columns, ['periode', 'mingguke', 'p', 'minggu', 'period', 'week'])
            col_gr = find_matching_column(df_raw.columns, ['gr', 'grossrequirement', 'grossrequirements', 'kebutuhankotor'])
            col_sr = find_matching_column(df_raw.columns, ['sr', 'scheduledreceipt', 'scheduledreceipts', 'penerimaanterjadwal'])
            
            df_workbench = pd.DataFrame()
            if col_p and col_p in df_raw.columns:
                df_workbench['Period'] = df_raw[col_p].astype(str)
            else:
                df_workbench['Period'] = [f"P{i+1}" for i in range(len(df_raw))]
                
            if col_gr and col_gr in df_raw.columns:
                df_workbench['Gross Requirements'] = df_raw[col_gr].fillna(0).astype(int)
            else:
                st.error("Failed to map Gross Requirements attribute automatically.")
                st.stop() 
                
            if col_sr and col_sr in df_raw.columns:
                df_workbench['Scheduled Receipts'] = df_raw[col_sr].fillna(0).astype(int)
            else:
                df_workbench['Scheduled Receipts'] = 0
        except Exception as e:
            st.error(f"Engine parsing failure: {e}")
            st.stop()
            
elif input_method == "Manual Entry":
    num_periods_input = st.number_input("Planning Horizon Length (Periods):", min_value=1, max_value=52, value=10, step=1)
    
    init_data = {
        'Period': [f"P{i+1}" for i in range(num_periods_input)],
        'Gross Requirements': [0] * num_periods_input,
        'Scheduled Receipts': [0] * num_periods_input
    }
    
    st.markdown("##### ✏️ Edit Demand & Scheduled Receipts Data Below:")
    df_raw_manual = pd.DataFrame(init_data)
    df_workbench = st.data_editor(df_raw_manual, use_container_width=True, hide_index=True)

else:
    default_data = {
        'Period': [f"P{i}" for i in range(1, 11)],
        'Gross Requirements': [35, 30, 40, 0, 10, 40, 30, 0, 30, 55],
        'Scheduled Receipts': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    df_workbench = pd.DataFrame(default_data)

if df_workbench is not None and not df_workbench.empty:
    gross_req = df_workbench['Gross Requirements'].fillna(0).astype(int).tolist()
    sched_rec = df_workbench['Scheduled Receipts'].fillna(0).astype(int).tolist()
    period_labels = df_workbench['Period'].astype(str).tolist()
    
    st.markdown("##### Input Data Matrix Summary View (Transposed):")
    df_preview_transposed = pd.DataFrame({
        'Gross Requirements': gross_req,
        'Scheduled Receipts': sched_rec
    }, index=period_labels).T
    
    if input_method == "Manual Entry":
        st.dataframe(df_preview_transposed, use_container_width=True)
        df_edited_preview = df_preview_transposed
    else:
        df_edited_preview = st.data_editor(df_preview_transposed, use_container_width=True)
        
    gross_req = df_edited_preview.loc['Gross Requirements'].astype(int).tolist()
    sched_rec = df_edited_preview.loc['Scheduled Receipts'].astype(int).tolist()


    # ==========================================
    # TABS INITIALIZATION
    # ==========================================
    st.markdown("---")
    st.subheader("⚙️ Lot Sizing Operational Performance Strategy Modules")

    if use_moq:
        st.info(f"🔧 **MOQ Constraint Active ({moq_val} units):** Applied as a post-fulfillment adjustment to all method order quantities. Note: Each method's lot grouping decision is based on original net requirements; MOQ scales up individual orders to meet the minimum threshold, and the resulting surplus inventory is reflected in the Projected On Hand.")

    tabs_list = st.tabs([
        "📋 L4L", "🎯 EOQ", "⏱️ POQ", "🔒 FOQ", "📅 FPR",
        "💰 IUC", "💸 LTC", "🔍 LUC", "⚖️ PPB", "🚀 Silver-Meal", "🔬 Wagner-Whitin"
    ])

    with tabs_list[3]:
        fixed_lot_size = st.number_input("Enter Fixed Order Size (FOQ Multiplier):", min_value=0, value=50, step=5)

    with tabs_list[4]:
        fpr_interval = st.number_input(
            "FPR Interval (periods):",
            min_value=0, max_value=len(gross_req), value=3, step=1,
            help="Isi angka > 0 untuk mengaktifkan kalkulasi FPR. Angka ini menentukan berapa periode yang digabung dalam satu window pemesanan."
        )


    # ==========================================
    # CORE PROCESSING MATHEMATICAL ALGORITHMS
    # ==========================================
    def calculate_multi_mrp(demands, s_receipts, setup, hold, init_inv, ss, lt, f_lot, moq_val, fpr_interval, build_trace=True):
        n = len(demands)
        
        # Net Requirements calculation stays inside engine for lot selection logic
        net_req = []
        prev_inv = init_inv
        for i in range(n):
            available_stock = prev_inv + s_receipts[i]
            net_val = demands[i] + ss - available_stock
            if net_val > 0:
                net_req.append(net_val)
                prev_inv = ss
            else:
                net_req.append(0)
                prev_inv = available_stock - demands[i]

        def generate_poh_and_release(rec_lot, moq_v=0):
            actual_rec = []
            for i in range(n):
                raw = rec_lot[i]
                actual = max(raw, moq_v) if (moq_v > 0 and raw > 0) else raw
                actual_rec.append(actual)

            poh = []
            r_inv = init_inv
            for i in range(n):
                r_inv += s_receipts[i] + actual_rec[i] - demands[i]
                poh.append(r_inv)

            rel_lot = [0] * n
            for i in range(n):
                if actual_rec[i] > 0:
                    target = i - lt
                    rel_lot[max(0, target)] += actual_rec[i]

            return poh, rel_lot, actual_rec

        # 1. LOT-FOR-LOT (L4L)
        l4l_rec = list(net_req)
        l4l_poh, l4l_rel, l4l_actual = generate_poh_and_release(l4l_rec, moq_val)
        c_l4l_setup = sum(1 for x in l4l_actual if x > 0) * setup
        c_l4l_hold  = sum(max(0, x) for x in l4l_poh) * hold

        # 2. LEAST UNIT COST (LUC)
        luc_rec = [0] * n
        luc_trace_logs = []
        idx = 0
        while idx < n:
            if net_req[idx] == 0:
                idx += 1
                continue
            best_k = idx
            min_uc = float('inf')
            acc_d, acc_h = 0, 0
            t_log = []
            
            for k in range(idx, n):
                acc_d += net_req[k]
                acc_h += net_req[k] * hold * (k - idx)
                t_cost = setup + acc_h
                uc = t_cost / acc_d if acc_d > 0 else float('inf')
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if uc <= min_uc:
                    min_uc, best_k = uc, k
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Setup Cost': setup, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                            'Unit Cost': uc, 'Status': 'Feasible'
                        })
                else:
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Setup Cost': setup, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                            'Unit Cost': uc, 'Status': 'Stop ⚠️ (Limit Exceeded)'
                        })
                    break
            
            if build_trace:
                df_step = pd.DataFrame(t_log)
                if not df_step.empty:
                    stop_exists = df_step['Status'].str.contains('Stop').any()
                    if stop_exists:
                        stop_idx = df_step[df_step['Status'].str.contains('Stop')].index[0]
                        if stop_idx > 0:
                            df_step.at[stop_idx - 1, 'Status'] = 'Selected (Optimal)'
                    else:
                        df_step.at[df_step.index[-1], 'Status'] = 'Horizon End (Optimal)'
                luc_trace_logs.append(df_step)
                
            luc_rec[idx] = sum(net_req[idx:best_k+1])
            idx = best_k + 1
            
        luc_poh, luc_rel, luc_actual = generate_poh_and_release(luc_rec, moq_val)
        c_luc_setup = sum(1 for x in luc_actual if x > 0) * setup
        c_luc_hold  = sum(max(0, x) for x in luc_poh) * hold

        # 3. ECONOMIC ORDER QUANTITY (EOQ)
        avg_demand_gross = np.mean(demands)
        eoq_raw_size = math.sqrt((2 * avg_demand_gross * setup) / hold) if hold > 0 else 0
        eoq_size = math.ceil(eoq_raw_size)
        eoq_rec = [0] * n
        rem_stok = 0
        
        if hold > 0:
            for i in range(n):
                if net_req[i] > 0:
                    if rem_stok < net_req[i]:
                        needed = net_req[i] - rem_stok
                        lots_to_order = math.ceil(needed / eoq_size) if eoq_size > 0 else 1
                        eoq_rec[i] = lots_to_order * eoq_size
                        rem_stok = (eoq_rec[i] + rem_stok) - net_req[i]
                    else:
                        rem_stok -= net_req[i]
                        
        eoq_poh, eoq_rel, eoq_actual = generate_poh_and_release(eoq_rec, moq_val)
        c_eoq_setup = sum(1 for x in eoq_actual if x > 0) * setup
        c_eoq_hold  = sum(max(0, x) for x in eoq_poh) * hold

        # 4. PART PERIOD BALANCING (PPB)
        ppb_rec = [0] * n
        ppb_trace_logs = []
        epp_limit = setup / hold if hold > 0 else float('inf')
        
        idx = 0
        while idx < n:
            if net_req[idx] == 0:
                idx += 1
                continue
            best_k = idx
            cum_part_period = 0
            acc_d = 0
            t_log = []
            
            for k in range(idx, n):
                part_period_k = net_req[k] * (k - idx)
                new_cum_part_period = cum_part_period + part_period_k
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if new_cum_part_period <= epp_limit:
                    acc_d += net_req[k]
                    cum_part_period = new_cum_part_period
                    best_k = k
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Target EPP': epp_limit, 'Accumulated Part-Period': cum_part_period,
                            'Status': 'Feasible'
                        })
                else:
                    dist_before = abs(cum_part_period - epp_limit)
                    dist_after  = abs(new_cum_part_period - epp_limit)
                    
                    if dist_after < dist_before:
                        acc_d += net_req[k]
                        cum_part_period = new_cum_part_period
                        best_k = k
                        if build_trace:
                            t_log.append({
                                'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                                'Target EPP': epp_limit, 'Accumulated Part-Period': cum_part_period,
                                'Status': 'Feasible (Closer Beyond Limit)'
                            })
                    else:
                        if build_trace:
                            t_log.append({
                                'Periods Covered': covered_periods_str, 'Total Units': acc_d + net_req[k],
                                'Target EPP': epp_limit, 'Accumulated Part-Period': new_cum_part_period,
                                'Status': 'Stop ⚠️ (Limit Exceeded)'
                            })
                    break
                    
            if build_trace:
                df_step = pd.DataFrame(t_log)
                if not df_step.empty:
                    stop_exists = df_step['Status'].str.contains('Stop').any()
                    if stop_exists:
                        stop_idx = df_step[df_step['Status'].str.contains('Stop')].index[0]
                        if stop_idx > 0:
                            df_step.at[stop_idx - 1, 'Status'] = 'Selected (Optimal)'
                    else:
                        df_step.at[df_step.index[-1], 'Status'] = 'Horizon End (Optimal)'
                ppb_trace_logs.append(df_step)
                
            ppb_rec[idx] = sum(net_req[idx:best_k+1])
            idx = best_k + 1
            
        ppb_poh, ppb_rel, ppb_actual = generate_poh_and_release(ppb_rec, moq_val)
        c_ppb_setup = sum(1 for x in ppb_actual if x > 0) * setup
        c_ppb_hold  = sum(max(0, x) for x in ppb_poh) * hold

        # 5. SILVER-MEAL (SM)
        sm_rec = [0] * n
        sm_trace_logs = []
        idx = 0
        while idx < n:
            if net_req[idx] == 0:
                idx += 1
                continue
            best_k = idx
            min_avg_cost = float('inf')
            acc_d, acc_h = 0, 0
            t_log = []
            
            for k in range(idx, n):
                acc_d += net_req[k]
                acc_h += net_req[k] * hold * (k - idx)
                t_cost = setup + acc_h
                n_periods_covered = k - idx + 1
                avg_cost = t_cost / n_periods_covered
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if avg_cost <= min_avg_cost:
                    min_avg_cost = avg_cost
                    best_k = k
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Setup Cost': setup, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                            'Average Cost/Period': avg_cost, 'Status': 'Feasible'
                        })
                else:
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Setup Cost': setup, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                            'Average Cost/Period': avg_cost, 'Status': 'Stop ⚠️ (Limit Exceeded)'
                        })
                    break
                    
            if build_trace:
                df_step = pd.DataFrame(t_log)
                if not df_step.empty:
                    stop_exists = df_step['Status'].str.contains('Stop').any()
                    if stop_exists:
                        stop_idx = df_step[df_step['Status'].str.contains('Stop')].index[0]
                        if stop_idx > 0:
                            df_step.at[stop_idx - 1, 'Status'] = 'Selected (Optimal)'
                    else:
                        df_step.at[df_step.index[-1], 'Status'] = 'Horizon End (Optimal)'
                sm_trace_logs.append(df_step)
                
            sm_rec[idx] = sum(net_req[idx:best_k+1])
            idx = best_k + 1
            
        sm_poh, sm_rel, sm_actual = generate_poh_and_release(sm_rec, moq_val)
        c_sm_setup = sum(1 for x in sm_actual if x > 0) * setup
        c_sm_hold  = sum(max(0, x) for x in sm_poh) * hold

        # 6. PERIOD ORDER QUANTITY (POQ)
        poq_raw_interval = eoq_size / avg_demand_gross if avg_demand_gross > 0 and eoq_size > 0 else 1
        poq_interval = max(1, round(poq_raw_interval))
        poq_rec = [0] * n
        i = 0
        while i < n:
            window_end = min(i + poq_interval, n)
            total_window_net = sum(net_req[i:window_end])
            if total_window_net > 0:
                poq_rec[i] = total_window_net
            i = window_end
            
        poq_poh, poq_rel, poq_actual = generate_poh_and_release(poq_rec, moq_val)
        c_poq_setup = sum(1 for x in poq_actual if x > 0) * setup
        c_poq_hold  = sum(max(0, x) for x in poq_poh) * hold

        # 7. FIXED ORDER QUANTITY (FOQ)
        foq_rec = [0] * n
        c_foq_setup, c_foq_hold = 0.0, 0.0
        if f_lot > 0:
            rem_foq_stok = 0
            for i in range(n):
                if net_req[i] > 0:
                    if rem_foq_stok < net_req[i]:
                        needed = net_req[i] - rem_foq_stok
                        multipliers = math.ceil(needed / f_lot)
                        foq_rec[i] = multipliers * f_lot
                        rem_foq_stok = (foq_rec[i] + rem_foq_stok) - net_req[i]
                    else:
                        rem_foq_stok -= net_req[i]

        foq_poh, foq_rel, foq_actual = generate_poh_and_release(foq_rec, moq_val)
        if f_lot > 0:
            c_foq_setup = sum(1 for x in foq_actual if x > 0) * setup
            c_foq_hold  = sum(max(0, x) for x in foq_poh) * hold

        # 8. LEAST TOTAL COST (LTC)
        ltc_rec = [0] * n
        ltc_trace_logs = []
        idx = 0
        while idx < n:
            if net_req[idx] == 0:
                idx += 1
                continue
            best_k = idx
            acc_d, acc_h = 0, 0
            t_log = []
            for k in range(idx, n):
                acc_d += net_req[k]
                acc_h += net_req[k] * hold * (k - idx)
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if acc_h < setup:
                    best_k = k
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Setup Cost': setup, 'Holding Cost': acc_h, 'Status': 'Feasible'
                        })
                    if hold == 0:
                        break
                else:
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Setup Cost': setup, 'Holding Cost': acc_h, 'Status': 'Stop ⚠️ (Holding ≥ Setup)'
                        })
                    break
                    
            if build_trace:
                df_step = pd.DataFrame(t_log)
                if not df_step.empty:
                    stop_exists = df_step['Status'].str.contains('Stop').any()
                    if stop_exists:
                        stop_idx = df_step[df_step['Status'].str.contains('Stop')].index[0]
                        if stop_idx > 0:
                            df_step.at[stop_idx - 1, 'Status'] = 'Selected (Optimal)'
                    else:
                        df_step.at[df_step.index[-1], 'Status'] = 'Horizon End (Optimal)'
                ltc_trace_logs.append(df_step)
                
            ltc_rec[idx] = sum(net_req[idx:best_k+1])
            idx = best_k + 1
            
        ltc_poh, ltc_rel, ltc_actual = generate_poh_and_release(ltc_rec, moq_val)
        c_ltc_setup = sum(1 for x in ltc_actual if x > 0) * setup
        c_ltc_hold  = sum(max(0, x) for x in ltc_poh) * hold

        # 9. INCREMENTAL UNIT COST (IUC)
        iuc_rec = [0] * n
        iuc_trace_logs = []
        idx = 0
        while idx < n:
            if net_req[idx] == 0:
                idx += 1
                continue
            best_k = idx
            prev_incremental_cost = float('inf')
            acc_d = 0
            t_log = []
            
            for k in range(idx, n):
                acc_d += net_req[k]
                marginal_holding = net_req[k] * hold * (k - idx)
                marginal_setup = setup if k == idx else 0
                incremental_cost = (marginal_setup + marginal_holding) / net_req[k] if net_req[k] > 0 else 0
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if incremental_cost <= prev_incremental_cost or k == idx:
                    prev_incremental_cost = incremental_cost
                    best_k = k
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Current Lot Size': acc_d,
                            'Marginal Cost': incremental_cost, 'Status': 'Feasible'
                        })
                else:
                    if build_trace:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Current Lot Size': acc_d,
                            'Marginal Cost': incremental_cost, 'Status': 'Stop ⚠️ (Cost Increased)'
                        })
                    break
                    
            if build_trace:
                df_step = pd.DataFrame(t_log)
                if not df_step.empty:
                    stop_exists = df_step['Status'].str.contains('Stop').any()
                    if stop_exists:
                        stop_idx = df_step[df_step['Status'].str.contains('Stop')].index[0]
                        if stop_idx > 0:
                            df_step.at[stop_idx - 1, 'Status'] = 'Selected (Optimal)'
                    else:
                        df_step.at[df_step.index[-1], 'Status'] = 'Horizon End (Optimal)'
                iuc_trace_logs.append(df_step)
                
            iuc_rec[idx] = sum(net_req[idx:best_k+1])
            idx = best_k + 1
            
        iuc_poh, iuc_rel, iuc_actual = generate_poh_and_release(iuc_rec, moq_val)
        c_iuc_setup = sum(1 for x in iuc_actual if x > 0) * setup
        c_iuc_hold  = sum(max(0, x) for x in iuc_poh) * hold

        # 10. FIXED PERIOD REQUIREMENTS (FPR)
        fpr_rec = [0] * n
        c_fpr_setup, c_fpr_hold = 0.0, 0.0
        if fpr_interval > 0:
            i = 0
            while i < n:
                w_end = min(i + fpr_interval, n)
                fpr_rec[i] = sum(net_req[i:w_end])
                i = w_end
                
        fpr_poh, fpr_rel, fpr_actual = generate_poh_and_release(fpr_rec, moq_val)
        if fpr_interval > 0:
            c_fpr_setup = sum(1 for x in fpr_actual if x > 0) * setup
            c_fpr_hold  = sum(max(0, x) for x in fpr_poh) * hold

        # 11. WAGNER-WHITIN (WW)
        ww_rec = [0] * n
        f = [0.0] * (n + 1)
        j_best = [0] * (n + 1)
        
        for t in range(1, n + 1):
            min_cost = float('inf')
            best_j = 0
            for j in range(1, t + 1):
                h_cost = 0.0
                for k in range(j, t + 1):
                    h_cost += net_req[k-1] * hold * (k - j)
                current_total = f[j-1] + setup + h_cost
                if current_total < min_cost:
                    min_cost = current_total
                    best_j = j
            f[t] = min_cost
            j_best[t] = best_j
            
        t = n
        while t > 0:
            j = j_best[t]
            ww_rec[j-1] = sum(net_req[j-1:t])
            t = j - 1
            
        ww_poh, ww_rel, ww_actual = generate_poh_and_release(ww_rec, moq_val)
        c_ww_setup = sum(1 for x in ww_actual if x > 0) * setup
        c_ww_hold  = sum(max(0, x) for x in ww_poh) * hold

        return {
            'L4L': (l4l_poh, l4l_actual, l4l_rel, c_l4l_setup + c_l4l_hold, None),
            'EOQ': (eoq_poh, eoq_actual, eoq_rel, c_eoq_setup + c_eoq_hold, eoq_size),
            'POQ': (poq_poh, poq_actual, poq_rel, c_poq_setup + c_poq_hold, poq_interval),
            'FOQ': (foq_poh, foq_actual, foq_rel, c_foq_setup + c_foq_hold, f_lot),
            'FPR': (fpr_poh, fpr_actual, fpr_rel, c_fpr_setup + c_fpr_hold, fpr_interval),
            'IUC': (iuc_poh, iuc_actual, iuc_rel, c_iuc_setup + c_iuc_hold, iuc_trace_logs),
            'LTC': (ltc_poh, ltc_actual, ltc_rel, c_ltc_setup + c_ltc_hold, ltc_trace_logs),
            'LUC': (luc_poh, luc_actual, luc_rel, c_luc_setup + c_luc_hold, luc_trace_logs),
            'PPB': (ppb_poh, ppb_actual, ppb_rel, c_ppb_setup + c_ppb_hold, ppb_trace_logs),
            'SM':  (sm_poh, sm_actual, sm_rel, c_sm_setup + c_sm_hold, sm_trace_logs),
            'WW':  (ww_poh, ww_actual, ww_rel, c_ww_setup + c_ww_hold, f[n])
        }

    # Run execution engine
    mrp_results = calculate_multi_mrp(
        gross_req, sched_rec, setup_cost, holding_cost, 
        initial_inv, safety_stock, lead_time, fixed_lot_size, moq_val, fpr_interval
    )

    # Rendering standard template without Net Requirements Row
    def render_mrp_module_tab(tab_object, key_name, method_title, extra_meta=None):
        poh, rec, rel, total_cost, trace = mrp_results[key_name]
        with tab_object:
            st.markdown(f"#### 📊 {method_title} Matrix Performance Output")
            if extra_meta:
                st.caption(extra_meta)
                
            df_output = pd.DataFrame({
                'Gross Requirements': gross_req,
                'Scheduled Receipts': sched_rec,
                'Projected On Hand': poh,
                'Planned Order Receipts': rec,
                'Planned Order Releases': rel
            }, index=period_labels).T
            
            st.dataframe(style_mrp_grid(df_output, max_capacity, safety_stock), use_container_width=True)
            st.markdown(f"💰 **Total Functional Cost ({method_title}):** `Rp {total_cost:,.2f}`")
            
            if trace and isinstance(trace, list):
                st.markdown("##### 🔍 Mathematical Selection Steps Logs")
                for sub_idx, log_df in enumerate(trace):
                    if not log_df.empty:
                        st.caption(f"Iteration Loop Grouping Window Plan {sub_idx + 1}:")
                        st.dataframe(log_df.style.apply(style_iteration_rows, axis=1), use_container_width=True, hide_index=True)

    # Render All 11 Modules
    render_mrp_module_tab(tabs_list[0], 'L4L', "Lot-for-Lot (L4L)")
    render_mrp_module_tab(tabs_list[1], 'EOQ', "Economic Order Quantity (EOQ)", f"Calculated Stable Lot Size Constant: {mrp_results['EOQ'][4]} units")
    render_mrp_module_tab(tabs_list[2], 'POQ', "Period Order Quantity (POQ)", f"Calculated Order Interval Matrix Step: {mrp_results['POQ'][4]} Periods")
    
    if fixed_lot_size > 0:
        render_mrp_module_tab(tabs_list[3], 'FOQ', "Fixed Order Quantity (FOQ)", f"Fixed Operational Constraint Value: {fixed_lot_size}")
    else:
        with tabs_list[3]:
            st.warning("Please specify an FOQ value above 0 in the numeric box to initialize validation.")
            
    if fpr_interval > 0:
        render_mrp_module_tab(tabs_list[4], 'FPR', "Fixed Period Requirements (FPR)", f"Manual Frame Aggregation Window: {fpr_interval} periods")
    else:
        with tabs_list[4]:
            st.warning("Please fill the FPR Interval box with a number > 0 to see the calculation.")

    render_mrp_module_tab(tabs_list[5], 'IUC', "Incremental Unit Cost (IUC)")
    render_mrp_module_tab(tabs_list[6], 'LTC', "Least Total Cost (LTC)")
    render_mrp_module_tab(tabs_list[7], 'LUC', "Least Unit Cost (LUC)")
    render_mrp_module_tab(tabs_list[8], 'PPB', "Part Period Balancing (PPB)")
    render_mrp_module_tab(tabs_list[9], 'SM', "Silver-Meal (SM)")
    render_mrp_module_tab(tabs_list[10], 'WW', "Wagner-Whitin (WW)", f"True Global Minimum Dynamic Cost Solution: Rp {mrp_results['WW'][4]:,.2f}")


    # ==========================================
    # 5. GLOBAL STRATEGIC PERFORMANCE BENCHMARK
    # ==========================================
    st.markdown("---")
    st.subheader("🏁 Global Strategic Cost Benchmarking Profile Dashboard")
    
    cost_comparison_data = {
        'Lot Sizing Strategy': [],
        'Total Financial Cost (Rp)': [],
        'Operational Execution Feasibility Status': []
    }
    
    for key in mrp_results.keys():
        poh, rec, rel, total_cost, _ = mrp_results[key]
        
        # Skip conditionally locked strategies if parameters are missing
        if key == 'FOQ' and fixed_lot_size <= 0:
            continue
        if key == 'FPR' and fpr_interval <= 0:
            continue
            
        is_feasible = "✅ Fully Feasible"
        if any(v < safety_stock for v in poh):
            is_feasible = "❌ Stockout Violation Alert"
        if any(v > max_capacity for v in poh):
            is_feasible = "⚠️ Warehouse Capacity Overflow"
            
        cost_comparison_data['Lot Sizing Strategy'].append(key)
        cost_comparison_data['Total Financial Cost (Rp)'].append(total_cost)
        cost_comparison_data['Operational Execution Feasibility Status'].append(is_feasible)
        
    df_comparison = pd.DataFrame(cost_comparison_data).sort_values(by='Total Financial Cost (Rp)')
    
    col_bench_1, col_bench_2 = st.columns([2, 3])
    
    with col_bench_1:
        st.markdown("##### 🏆 Strategy Efficiency Ranking Matrix")
        st.dataframe(df_comparison.style.highlight_min(subset=['Total Financial Cost (Rp)'], color='#e8f5e9'), use_container_width=True, hide_index=True)
        
    with col_bench_2:
        st.markdown("##### 📊 Cost Distribution Variance Chart")
        fig, ax = plt.subplots(figsize=(7, 3.8))
        fig.patch.set_facecolor('#faf8f2')
        ax.set_facecolor('#ffffff')
        
        colors = ['#6a0708' if x != df_comparison['Total Financial Cost (Rp)'].min() else '#2e7d32' for x in df_comparison['Total Financial Cost (Rp)']]
        bars = ax.bar(df_comparison['Lot Sizing Strategy'], df_comparison['Total Financial Cost (Rp)'], color=colors, width=0.55)
        
        ax.set_ylabel('Total Cost (Rp)', color='#111111', fontsize=10, fontweight='bold')
        ax.tick_params(colors='#111111', labelsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.3, color='#cccccc')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#e0dbcd')
        ax.spines['bottom'].set_color('#e0dbcd')
        
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:,.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=8, color='#111111', fontweight='500')
                        
        plt.tight_layout()
        st.pyplot(fig)


    # ==========================================
    # 6. EXPORT WORKBENCH
    # ==========================================
    st.markdown("---")
    st.subheader("💾 Strategic Procurement Report Export Engine")
    
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # Sheet 1: Master Inputs
        df_preview_transposed.to_excel(writer, sheet_name="Master Demand Plan Inputs")
        
        # Sheet 2: Cross-Tabulated Planned Receipts Breakdown
        receipts_matrix_export = {}
        for key in mrp_results.keys():
            if key == 'FOQ' and fixed_lot_size <= 0: continue
            if key == 'FPR' and fpr_interval <= 0: continue
            receipts_matrix_export[f'{key} Order Receipts'] = mrp_results[key][1]
            
        pd.DataFrame(receipts_matrix_export, index=period_labels).T.to_excel(writer, sheet_name="Lot Sizing Receipts Breakdown")
        
    st.download_button(
        label="📥 Download Unified Multi-Method Strategic MRP Report",
        data=excel_buffer.getvalue(),
        file_name="MRP_Multi_Method_Strategic_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
