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
holding_cost = st.sidebar.number_input("Holding Cost (per unit/period)", min_value=0.0, value=1.0, step=0.5)

st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.subheader("🗂️ Inventory Profiles")
initial_inv = st.sidebar.number_input("Initial Inventory", min_value=0, value=20, step=5)
safety_stock = st.sidebar.number_input("Safety Stock", min_value=0, value=5, step=1)
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
# UTILITY HELPERS
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
    
    default_gr = [35, 30, 40, 0, 10, 40, 30, 0, 30, 55]
    if num_periods_input > len(default_gr):
        default_gr += [0] * (num_periods_input - len(default_gr))
    else:
        default_gr = default_gr[:num_periods_input]
        
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

    n = len(gross_req)
    
    # ----------------------------------------------------
    # PRE-CALCULATE UNIVERSAL NET REQUIREMENTS BASE VECTOR
    # ----------------------------------------------------
    net_req = []
    prev_inv = initial_inv
    for i in range(n):
        available_stock = prev_inv + sched_rec[i]
        net_val = gross_req[i] + safety_stock - available_stock
        if net_val > 0:
            net_req.append(net_val)
            prev_inv = safety_stock
        else:
            net_req.append(0)
            prev_inv = available_stock - gross_req[i]

    # HELPER FULFILLMENT CLOSURE ENGINE (Dengan Penerapan MOQ Pasca-Proses Jika Aktif)
    def generate_poh_and_release(rec_lot, moq_c=0):
        actual_rec = []
        for i in range(n):
            raw = rec_lot[i]
            actual = max(raw, moq_c) if (moq_c > 0 and raw > 0) else raw
            actual_rec.append(actual)

        poh = []
        r_inv = initial_inv
        for i in range(n):
            r_inv += sched_rec[i] + actual_rec[i] - gross_req[i]
            poh.append(r_inv)

        rel_lot = [0] * n
        for i in range(n):
            if actual_rec[i] > 0:
                target = i - lead_time
                if target < 0:
                    rel_lot[0] += actual_rec[i]
                else:
                    rel_lot[target] += actual_rec[i]

        return poh, rel_lot, actual_rec

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
            min_value=1, max_value=n, value=3, step=1,
            help="Determines how many periods are grouped into a single ordering window."
        )

    # Dictionary to collect results for comparison
    comp_summary = {}

    # ==========================================
    # Tab 1: LOT-FOR-LOT (L4L)
    # ==========================================
    with tabs_list[0]:
        l4l_rec = list(net_req)
        l4l_poh, l4l_rel, l4l_actual = generate_poh_and_release(l4l_rec, moq_val)
        
        df_l4l = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': l4l_actual,
            'Projected On Hand': l4l_poh,
            'Planned Releases': l4l_rel
        }, index=period_labels).T
        
        st.markdown("##### 📊 Lot-for-Lot (L4L) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_l4l, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in l4l_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in l4l_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['L4L'] = (sum(l4l_actual), sum(1 for x in l4l_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")

    # ==========================================
    # Tab 2: ECONOMIC ORDER QUANTITY (EOQ)
    # ==========================================
    with tabs_list[1]:
        avg_demand_gross = np.mean(gross_req)
        eoq_raw_size = math.sqrt((2 * avg_demand_gross * setup_cost) / holding_cost) if holding_cost > 0 else 0
        eoq_size = math.ceil(eoq_raw_size)
        
        eoq_rec = [0] * n
        rem_stok = 0
        if holding_cost > 0:
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
        
        df_eoq = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': eoq_actual,
            'Projected On Hand': eoq_poh,
            'Planned Releases': eoq_rel
        }, index=period_labels).T
        
        st.markdown("##### 🎯 Economic Order Quantity (EOQ) Material Requirements Planning Grid:")
        st.markdown(f"**Calculated Static EOQ Target Lot Size:** `{eoq_size}` units (derived from average horizon demand)")
        st.dataframe(style_mrp_grid(df_eoq, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in eoq_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in eoq_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['EOQ'] = (sum(eoq_actual), sum(1 for x in eoq_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")

    # ==========================================
    # Tab 3: PERIOD ORDER QUANTITY (POQ)
    # ==========================================
    with tabs_list[2]:
        poq_raw_interval = eoq_size / avg_demand_gross if avg_demand_gross > 0 and eoq_size > 0 else 1
        poq_interval = max(1, round(poq_raw_interval))
        
        poq_rec = [0] * n
        i = 0
        while i < n:
            if i < n and net_req[i] == 0:
                i += 1
                continue
            window_end = min(i + poq_interval, n)
            total_window_net = sum(net_req[i:window_end])
            if total_window_net > 0:
                poq_rec[i] = total_window_net
            i = window_end
            
        poq_poh, poq_rel, poq_actual = generate_poh_and_release(poq_rec, moq_val)
        
        df_poq = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': poq_actual,
            'Projected On Hand': poq_poh,
            'Planned Releases': poq_rel
        }, index=period_labels).T
        
        st.markdown("##### ⏱️ Period Order Quantity (POQ) Material Requirements Planning Grid:")
        st.markdown(f"**Calculated Mathematical POQ Target Interval:** `{poq_interval}` periods")
        st.dataframe(style_mrp_grid(df_poq, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in poq_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in poq_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['POQ'] = (sum(poq_actual), sum(1 for x in poq_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")

    # ==========================================
    # Tab 4: FIXED ORDER QUANTITY (FOQ)
    # ==========================================
    with tabs_list[3]:
        foq_rec = [0] * n
        if fixed_lot_size > 0:
            rem_foq_stok = 0
            for i in range(n):
                if net_req[i] > 0:
                    if rem_foq_stok < net_req[i]:
                        needed = net_req[i] - rem_foq_stok
                        multipliers = math.ceil(needed / fixed_lot_size)
                        foq_rec[i] = multipliers * fixed_lot_size
                        rem_foq_stok = (foq_rec[i] + rem_foq_stok) - net_req[i]
                    else:
                        rem_foq_stok -= net_req[i]
                        
        foq_poh, foq_rel, foq_actual = generate_poh_and_release(foq_rec, moq_val)
        
        df_foq = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': foq_actual,
            'Projected On Hand': foq_poh,
            'Planned Releases': foq_rel
        }, index=period_labels).T
        
        st.markdown("##### 🔒 Fixed Order Quantity (FOQ) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_foq, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in foq_actual if x > 0) * setup_cost if fixed_lot_size > 0 else 0
        c_hold = sum(max(0, x) for x in foq_poh) * holding_cost if fixed_lot_size > 0 else 0
        tc = c_setup + c_hold
        comp_summary['FOQ'] = (sum(foq_actual), sum(1 for x in foq_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")

    # ==========================================
    # Tab 5: FIXED PERIOD REQUIREMENTS (FPR)
    # ==========================================
    with tabs_list[4]:
        fpr_rec = [0] * n
        i = 0
        while i < n:
            if i < n and net_req[i] == 0:
                i += 1
                continue
            window_end = min(i + fpr_interval, n)
            total_window_net = sum(net_req[i:window_end])
            if total_window_net > 0:
                fpr_rec[i] = total_window_net
            i = window_end
            
        fpr_poh, fpr_rel, fpr_actual = generate_poh_and_release(fpr_rec, moq_val)
        
        df_fpr = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': fpr_actual,
            'Projected On Hand': fpr_poh,
            'Planned Releases': fpr_rel
        }, index=period_labels).T
        
        st.markdown("##### 📅 Fixed Period Requirements (FPR) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_fpr, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in fpr_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in fpr_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['FPR'] = (sum(fpr_actual), sum(1 for x in fpr_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")

    # ==========================================
    # Tab 6: INCREMENTAL UNIT COST (IUC)
    # ==========================================
    with tabs_list[5]:
        iuc_rec = [0] * n
        iuc_trace_logs = []
        idx = 0
        while idx < n:
            if net_req[idx] == 0:
                idx += 1
                continue
            best_k = idx
            t_log = []
            prev_margin_cost = -1
            
            for k in range(idx, n):
                added_units = net_req[k]
                added_holding = net_req[k] * holding_cost * (k - idx)
                margin_cost = added_holding / added_units if added_units > 0 else 0
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if prev_margin_cost == -1 or margin_cost >= prev_margin_cost:
                    best_k = k
                    prev_margin_cost = margin_cost
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Incremental Units': added_units,
                        'Incremental Holding': added_holding, 'Marginal Cost/Unit': margin_cost,
                        'Status': 'Feasible'
                    })
                else:
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Incremental Units': added_units,
                        'Incremental Holding': added_holding, 'Marginal Cost/Unit': margin_cost,
                        'Status': 'Stop ⚠️ (Cost Decreased)'
                    })
                    break
                    
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
        
        df_iuc = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': iuc_actual,
            'Projected On Hand': iuc_poh,
            'Planned Releases': iuc_rel
        }, index=period_labels).T
        
        st.markdown("##### 💰 Incremental Unit Cost (IUC) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_iuc, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in iuc_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in iuc_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['IUC'] = (sum(iuc_actual), sum(1 for x in iuc_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")
        
        st.markdown("###### 🔍 Incremental Unit Cost (IUC) Algorithmic Step-by-Step Optimization Iterations:")
        for step_idx, df_step in enumerate(iuc_trace_logs):
            st.text(f"Consolidation Phase Order Cluster #{step_idx + 1}:")
            st.dataframe(df_step.style.apply(style_iteration_rows, axis=None), use_container_width=True, hide_index=True)

# ==========================================
# Tab 7: LEAST TOTAL COST (LTC)
# ==========================================
    with tabs_list[6]:
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
                acc_h += net_req[k] * holding_cost * (k - idx)
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if acc_h < setup_cost:
                    best_k = k
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Setup Cost': setup_cost, 'Holding Cost': acc_h, 'Status': 'Feasible'
                    })
                    if holding_cost == 0:
                        break
                else:
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Setup Cost': setup_cost, 'Holding Cost': acc_h, 'Status': 'Stop ⚠️ (Holding ≥ Setup)'
                    })
                    break
                    
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
        
        df_ltc = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': ltc_actual,
            'Projected On Hand': ltc_poh,
            'Planned Releases': ltc_rel
        }, index=period_labels).T
        
        st.markdown("##### 💸 Least Total Cost (LTC) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_ltc, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in ltc_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in ltc_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['LTC'] = (sum(ltc_actual), sum(1 for x in ltc_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")
        
        st.markdown("###### 🔍 Least Total Cost (LTC) Algorithmic Step-by-Step Optimization Iterations:")
        for step_idx, df_step in enumerate(ltc_trace_logs):
            st.text(f"Consolidation Phase Order Cluster #{step_idx + 1}:")
            st.dataframe(df_step.style.apply(style_iteration_rows, axis=None), use_container_width=True, hide_index=True)

    # ==========================================
    # Tab 8: LEAST UNIT COST (LUC)
    # ==========================================
    with tabs_list[7]:
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
                acc_h += net_req[k] * holding_cost * (k - idx)
                t_cost = setup_cost + acc_h
                uc = t_cost / acc_d if acc_d > 0 else float('inf')
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if uc < min_uc:
                    min_uc, best_k = uc, k
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Setup Cost': setup_cost, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                        'Unit Cost': uc, 'Status': 'Feasible'
                    })
                else:
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Setup Cost': setup_cost, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                        'Unit Cost': uc, 'Status': 'Stop ⚠️ (Limit Exceeded)'
                    })
                    break
                    
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
        
        df_luc = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': luc_actual,
            'Projected On Hand': luc_poh,
            'Planned Releases': luc_rel
        }, index=period_labels).T
        
        st.markdown("##### 🔍 Least Unit Cost (LUC) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_luc, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in luc_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in luc_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['LUC'] = (sum(luc_actual), sum(1 for x in luc_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")
        
        st.markdown("###### 🔍 Least Unit Cost (LUC) Algorithmic Step-by-Step Optimization Iterations:")
        for step_idx, df_step in enumerate(luc_trace_logs):
            st.text(f"Consolidation Phase Order Cluster #{step_idx + 1}:")
            st.dataframe(df_step.style.apply(style_iteration_rows, axis=None), use_container_width=True, hide_index=True)

    # ==========================================
    # Tab 9: PART PERIOD BALANCING (PPB)
    # ==========================================
    with tabs_list[8]:
        ppb_rec = [0] * n
        ppb_trace_logs = []
        epp_limit = setup_cost / holding_cost if holding_cost > 0 else float('inf')
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
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Target EPP': epp_limit, 'Accumulated Part-Period': cum_part_period,
                        'Status': 'Feasible'
                    })
                else:
                    dist_before = abs(cum_part_period - epp_limit)
                    dist_after = abs(new_cum_part_period - epp_limit)
                    if dist_after < dist_before:
                        acc_d += net_req[k]
                        cum_part_period = new_cum_part_period
                        best_k = k
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                            'Target EPP': epp_limit, 'Accumulated Part-Period': cum_part_period,
                            'Status': 'Feasible (Closer Beyond Limit)'
                        })
                    else:
                        t_log.append({
                            'Periods Covered': covered_periods_str, 'Total Units': acc_d + net_req[k],
                            'Target EPP': epp_limit, 'Accumulated Part-Period': new_cum_part_period,
                            'Status': 'Stop ⚠️ (Limit Exceeded)'
                        })
                    break
                    
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
        
        df_ppb = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': ppb_actual,
            'Projected On Hand': ppb_poh,
            'Planned Releases': ppb_rel
        }, index=period_labels).T
        
        st.markdown("##### ⚖️ Part Period Balancing (PPB) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_ppb, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in ppb_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in ppb_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['PPB'] = (sum(ppb_actual), sum(1 for x in ppb_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")
        
        st.markdown("###### 🔍 Part Period Balancing (PPB) Algorithmic Step-by-Step Optimization Iterations:")
        for step_idx, df_step in enumerate(ppb_trace_logs):
            st.text(f"Consolidation Phase Order Cluster #{step_idx + 1}:")
            st.dataframe(df_step.style.apply(style_iteration_rows, axis=None), use_container_width=True, hide_index=True)

    # ==========================================
    # Tab 10: SILVER-MEAL (SM)
    # ==========================================
    with tabs_list[9]:
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
                acc_h += net_req[k] * holding_cost * (k - idx)
                t_cost = setup_cost + acc_h
                n_periods_covered = k - idx + 1
                avg_cost = t_cost / n_periods_covered
                covered_periods_str = ", ".join([period_labels[m] for m in range(idx, k+1)])
                
                if avg_cost < min_avg_cost:
                    min_avg_cost = avg_cost
                    best_k = k
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Setup Cost': setup_cost, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                        'Average Cost/Period': avg_cost, 'Status': 'Feasible'
                    })
                else:
                    t_log.append({
                        'Periods Covered': covered_periods_str, 'Total Units': acc_d,
                        'Setup Cost': setup_cost, 'Holding Cost': acc_h, 'Total Cost': t_cost,
                        'Average Cost/Period': avg_cost, 'Status': 'Stop ⚠️ (Limit Exceeded)'
                    })
                    break
                    
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
        
        df_sm = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': sm_actual,
            'Projected On Hand': sm_poh,
            'Planned Releases': sm_rel
        }, index=period_labels).T
        
        st.markdown("##### 🚀 Silver-Meal (SM) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_sm, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in sm_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in sm_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['SM'] = (sum(sm_actual), sum(1 for x in sm_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")
        
        st.markdown("###### 🔍 Silver-Meal (SM) Algorithmic Step-by-Step Optimization Iterations:")
        for step_idx, df_step in enumerate(sm_trace_logs):
            st.text(f"Consolidation Phase Order Cluster #{step_idx + 1}:")
            st.dataframe(df_step.style.apply(style_iteration_rows, axis=None), use_container_width=True, hide_index=True)

    # ==========================================
    # Tab 11: WAGNER-WHITIN (WW)
    # ==========================================
    with tabs_list[10]:
        f = [0.0] * (n + 1)
        parent = [-1] * (n + 1)
        f[0] = 0.0
        
        for j in range(1, n + 1):
            min_val = float('inf')
            best_i = -1
            for i in range(1, j + 1):
                h_cost = 0.0
                for t in range(i, j + 1):
                    h_cost += net_req[t-1] * holding_cost * (t - i)
                curr_cost = f[i-1] + setup_cost + h_cost
                if curr_cost < min_val:
                    min_val = curr_cost
                    best_i = i
            f[j] = min_val
            parent[j] = best_i
            
        ww_rec = [0] * n
        curr = n
        while curr > 0:
            p_start = parent[curr]
            tot_net = sum(net_req[p_start-1:curr])
            ww_rec[p_start-1] = tot_net
            curr = p_start - 1
            
        ww_poh, ww_rel, ww_actual = generate_poh_and_release(ww_rec, moq_val)
        
        df_ww = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Planned Receipts': ww_actual,
            'Projected On Hand': ww_poh,
            'Planned Releases': ww_rel
        }, index=period_labels).T
        
        st.markdown("##### 🔬 Wagner-Whitin (WW) Material Requirements Planning Grid:")
        st.dataframe(style_mrp_grid(df_ww, max_capacity, safety_stock), use_container_width=True)
        
        c_setup = sum(1 for x in ww_actual if x > 0) * setup_cost
        c_hold = sum(max(0, x) for x in ww_poh) * holding_cost
        tc = c_setup + c_hold
        comp_summary['WW'] = (sum(ww_actual), sum(1 for x in ww_actual if x > 0), c_setup, c_hold, tc)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Setup Cost", f"${c_setup:,.2f}")
        c2.metric("Total Holding Cost", f"${c_hold:,.2f}")
        c3.metric("Combined Operational Cost", f"${tc:,.2f}")
        
        st.markdown("###### 🔍 Wagner-Whitin Horizon Forward Cost Matrix Vector $f(j)$:")
        df_ww_vector = pd.DataFrame([f[1:]], columns=period_labels, index=["Min Cumulative Cost"])
        st.dataframe(df_ww_vector, use_container_width=True)

    # ==========================================
    # 5. CROSS-STRATEGY COMPARISON ENGINE
    # ==========================================
    st.markdown("---")
    st.subheader("🏁 Multi-Strategy Performance Benchmarking Matrix")

    comp_summary_data = []
    for m_name, metrics in comp_summary.items():
        comp_summary_data.append({
            'Strategy Method': m_name,
            'Total Units Ordered': metrics[0],
            'Frequency (Orders)': metrics[1],
            'Total Setup Cost': metrics[2],
            'Total Holding Cost': metrics[3],
            'Grand Total Cost': metrics[4]
        })

    df_comparison = pd.DataFrame(comp_summary_data)
    df_comparison_styled = df_comparison.style.highlight_min(
        subset=['Total Setup Cost', 'Total Holding Cost', 'Grand Total Cost'], 
        color='#e8f5e9'
    ).highlight_max(
        subset=['Grand Total Cost'], 
        color='#ffebee'
    )
    
    st.dataframe(df_comparison_styled, use_container_width=True, hide_index=True)

    # ==========================================
    # 6. ANALYTICAL VISUALIZATION CHART
    # ==========================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Financial Trade-offs Comparison Data Chart")

    fig, ax = plt.subplots(figsize=(12, 5))
    methods_list = df_comparison['Strategy Method'].tolist()
    setup_vector = df_comparison['Total Setup Cost'].tolist()
    holding_vector = df_comparison['Total Holding Cost'].tolist()

    x_indexes = np.arange(len(methods_list))
    bar_width = 0.4

    ax.bar(x_indexes - bar_width/2, setup_vector, bar_width, label='Total Setup Cost', color='#6a0708')
    ax.bar(x_indexes + bar_width/2, holding_vector, bar_width, label='Total Holding Cost', color='#e0dbcd')

    ax.set_ylabel('Financial Cost ($)', fontsize=11, fontweight='bold', color='#111111')
    ax.set_title('Financial Cost Dynamics: Setup Cost vs Holding Cost Framework', fontsize=12, fontweight='bold', color='#6a0708')
    ax.set_xticks(x_indexes)
    ax.set_xticklabels(methods_list, fontweight='bold')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#e0dbcd')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    fig.patch.set_facecolor('#faf8f2')
    ax.set_facecolor('#ffffff')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e0dbcd')
    ax.spines['bottom'].set_color('#e0dbcd')

    st.pyplot(fig)
