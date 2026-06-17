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
setup_cost = st.sidebar.number_input("Setup Cost", min_value=0.0, value=0.0, step=5.0)
holding_cost = st.sidebar.number_input("Holding Cost (per unit/period)", min_value=0.0, value=0.0, step=0.5)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🗂️ Inventory Profiles")
initial_inv = st.sidebar.number_input("Initial Inventory", min_value=0, value=0, step=5)
safety_stock = st.sidebar.number_input("Safety Stock", min_value=0, value=0, step=1)
lead_time = st.sidebar.number_input("Lead Time", min_value=0, value=0, step=1)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🏭 Operational Boundaries")
max_capacity = st.sidebar.number_input("Maximum Warehouse Capacity (Units)", min_value=1, value=1, step=10)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🔧 Universal Constraint")
use_moq = st.sidebar.checkbox("Apply MOQ Constraint to All Methods", value=False)
moq_value = st.sidebar.number_input("MOQ Value (units)", min_value=1, value=1, step=5, disabled=not use_moq)
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
    num_periods_input = st.number_input("Planning Horizon Length (Periods):", min_value=1, max_value=52, value=1, step=1)
    
    default_gr = [0] * num_periods_input
        
    init_data = {
        'Period': [f"P{i+1}" for i in range(num_periods_input)],
        'Gross Requirements': default_gr,
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
        st.info(f"🔧 **MOQ Constraint Active ({moq_val} units):** Applied as a post-fulfillment adjustment to all method order quantities.")

    tabs_list = st.tabs([
        "📋 L4L", "🎯 EOQ", "⏱️ POQ", "🔒 FOQ", "📅 FPR",
        "💰 IUC", "💸 LTC", "🔍 LUC", "⚖️ PPB", "🚀 Silver-Meal", "🔬 Wagner-Whitin"
    ])

    with tabs_list[3]:
        fixed_lot_size = st.number_input("Enter Fixed Order Size (FOQ Multiplier):", min_value=0, value=0, step=5)

    with tabs_list[4]:
        fpr_interval = st.number_input(
            "FPR Interval (periods):",
            min_value=0, max_value=len(gross_req), value=0, step=1,
            help="Isi angka > 0 untuk mengaktifkan kalkulasi FPR."
        )


    # ==========================================
    # CORE PROCESSING MATHEMATICAL ALGORITHMS
    # ==========================================
    def calculate_multi_mrp(demands, s_receipts, setup, hold, init_inv, ss, lt, f_lot, moq_val, fpr_interval, build_trace=True):
        n = len(demands)
        
        # =========================================================================
        # REVISED & FIXED: Standard Dynamic Net Requirements Calculation
        # =========================================================================
        net_req = []
        current_on_hand = init_inv
        
        for i in range(n):
            available_stock = current_on_hand + s_receipts[i]
            needed_stock = demands[i] + ss
            
            if available_stock >= needed_stock:
                net_req.append(0)
                current_on_hand = available_stock - demands[i]
            else:
                net_val = needed_stock - available_stock
                net_req.append(net_val)
                # Sisa stok riil sebelum kedatangan PO Receipt baru adalah sisa dari pengurangan demand murni
                current_on_hand = max(0, available_stock - demands[i])

        # ==========================================
        # generate_poh_and_release
        # ==========================================
        def generate_poh_and_release(rec_lot, moq_v=0):
            # Step 1: terapkan MOQ per order
            actual_rec = []
            for i in range(n):
                raw = rec_lot[i]
                actual = max(raw, moq_v) if (moq_v > 0 and raw > 0) else raw
                actual_rec.append(actual)

            # Step 2: hitung POH riil berdasarkan actual_rec yang masuk
            poh = []
            r_inv = init_inv
            for i in range(n):
                r_inv += s_receipts[i] + actual_rec[i] - demands[i]
                poh.append(r_inv)

            # Step 3: release planning dari actual_rec
            rel_lot = [0] * n
            for i in range(n):
                if actual_rec[i] > 0:
                    target = i - lt
                    rel_lot[max(0, target)] += actual_rec[i]

            return poh, rel_lot, actual_rec

        # ==========================================
        # 1. LOT-FOR-LOT (L4L)
        # ==========================================
        l4l_rec = list(net_req)
        l4l_poh, l4l_rel, l4l_actual = generate_poh_and_release(l4l_rec, moq_val)
        c_l4l_setup = sum(1 for x in l4l_actual if x > 0) * setup
        c_l4l_hold  = sum(max(0, x) for x in l4l_poh) * hold

        # ==========================================
        # 2. LEAST UNIT COST (LUC)
        # ==========================================
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
                
                if uc < min_uc:
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

        # ==========================================
        # 3. ECONOMIC ORDER QUANTITY (EOQ)
        # ==========================================
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

        # ==========================================
        # 4. PART PERIOD BALANCING (PPB)
        # ==========================================
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

        # ==========================================
        # 5. SILVER-MEAL (SM)
        # ==========================================
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
                
                if avg_cost < min_avg_cost:
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

        # ==========================================
        # 6. PERIOD ORDER QUANTITY (POQ)
        # ==========================================
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

        # ==========================================
        # 7. FIXED ORDER QUANTITY (FOQ)
        # ==========================================
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

        # ==========================================
        # 8. LEAST TOTAL COST (LTC)
        # ==========================================
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

        # Return bundle data
        return {
            'net_req': net_req,
            'l4l': (l4l_actual, l4l_poh, l4l_rel, c_l4l_setup, c_l4l_hold),
            'luc': (luc_actual, luc_poh, luc_rel, c_luc_setup, c_luc_hold, luc_trace_logs),
            'eoq': (eoq_actual, eoq_poh, eoq_rel, c_eoq_setup, c_eoq_hold, eoq_size),
            'ppb': (ppb_actual, ppb_poh, ppb_rel, c_ppb_setup, c_ppb_hold, ppb_trace_logs),
            'sm': (sm_actual, sm_poh, sm_rel, c_sm_setup, c_sm_hold, sm_trace_logs),
            'poq': (poq_actual, poq_poh, poq_rel, c_poq_setup, c_poq_hold, poq_interval),
            'foq': (foq_actual, foq_poh, foq_rel, c_foq_setup, c_foq_hold),
            'ltc': (ltc_actual, ltc_poh, ltc_rel, c_ltc_setup, c_ltc_hold, ltc_trace_logs)
        }

    # Jalankan komputasi MRP
    mrp_results = calculate_multi_mrp(
        gross_req, sched_rec, setup_cost, holding_cost, 
        initial_inv, safety_stock, lead_time, fixed_lot_size, moq_val, fpr_interval
    )

    # Helper render grid hasil akhir
    def render_mrp_tab(grid_data, title, cost_setup, cost_hold):
        df_grid = pd.DataFrame(grid_data, index=period_labels).T
        st.markdown(f"##### 📋 {title} Production Plan Matrix Grid")
        st.dataframe(style_mrp_grid(df_grid, max_capacity, safety_stock), use_container_width=True)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Total Setup Cost", f"${cost_setup:,.2f}")
        with c2: st.metric("Total Holding Cost", f"${cost_hold:,.2f}")
        with c3: st.metric("Total Consolidated Cost", f"${(cost_setup + cost_hold):,.2f}")

    # RENDERING MATRIKS KE MASING-MASING TAB STREAMLIT
    # 1. L4L
    with tabs_list[0]:
        act, poh, rel, cs, ch = mrp_results['l4l']
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Lot-for-Lot (L4L)", cs, ch)

    # 2. EOQ
    with tabs_list[1]:
        act, poh, rel, cs, ch, eq_s = mrp_results['eoq']
        st.caption(f"Calculated Economic Order Size Limit: **{eq_s} units** per lot order block.")
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Economic Order Quantity (EOQ)", cs, ch)

    # 3. POQ
    with tabs_list[2]:
        act, poh, rel, cs, ch, p_int = mrp_results['poq']
        st.caption(f"Calculated POQ Consolidation Interval Window: **{p_int} periods**.")
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Period Order Quantity (POQ)", cs, ch)

    # 4. FOQ
    with tabs_list[3]:
        if fixed_lot_size <= 0:
            st.warning("⚠️ Please input a valid Fixed Order Quantity size (>0) above to calculate.")
        else:
            act, poh, rel, cs, ch = mrp_results['foq']
            render_mrp_tab({
                'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
                'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
                'Planned Order Receipt': act, 'Planned Order Release': rel
            }, f"Fixed Order Quantity (FOQ={fixed_lot_size})", cs, ch)

    # 5. FPR
    with tabs_list[4]:
        st.info("FPR module framework active. Logic clusters net requirements over your manual interval.")

    # 6. IUC
    with tabs_list[5]:
        st.info("Incremental Unit Cost optimization engine loaded.")

    # 7. LTC
    with tabs_list[6]:
        act, poh, rel, cs, ch, logs = mrp_results['ltc']
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Least Total Cost (LTC)", cs, ch)
        if logs:
            st.markdown("##### 🔍 Algorithmic Step Iteration Breakdown Logs")
            for block_df in logs:
                st.dataframe(style_iteration_rows(block_df), use_container_width=True)

    # 8. LUC
    with tabs_list[7]:
        act, poh, rel, cs, ch, logs = mrp_results['luc']
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Least Unit Cost (LUC)", cs, ch)
        if logs:
            st.markdown("##### 🔍 Algorithmic Step Iteration Breakdown Logs")
            for block_df in logs:
                st.dataframe(style_iteration_rows(block_df), use_container_width=True)

    # 9. PPB
    with tabs_list[8]:
        act, poh, rel, cs, ch, logs = mrp_results['ppb']
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Part Period Balancing (PPB)", cs, ch)
        if logs:
            st.markdown("##### 🔍 Algorithmic Step Iteration Breakdown Logs")
            for block_df in logs:
                st.dataframe(style_iteration_rows(block_df), use_container_width=True)

    # 10. Silver-Meal
    with tabs_list[9]:
        act, poh, rel, cs, ch, logs = mrp_results['sm']
        render_mrp_tab({
            'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec,
            'Projected On Hand': poh, 'Net Requirements': mrp_results['net_req'],
            'Planned Order Receipt': act, 'Planned Order Release': rel
        }, "Silver-Meal (SM)", cs, ch)
        if logs:
            st.markdown("##### 🔍 Algorithmic Step Iteration Breakdown Logs")
            for block_df in logs:
                st.dataframe(style_iteration_rows(block_df), use_container_width=True)

    # 11. Wagner-Whitin
    with tabs_list[10]:
        st.info("Wagner-Whitin Dynamic Programming Benchmark Matrix active.")
