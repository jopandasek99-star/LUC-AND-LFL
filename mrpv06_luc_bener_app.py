import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="APP PERHITUNGAN LFL dan LUC", layout="wide")
st.title("APP PERHITUNGAN LFL dan LUC- by Jo and Sam ELITE")

# Sidebar parameters
st.sidebar.header("Parameters")
setup_cost = st.sidebar.number_input("Setup Cost per Order (S)", value=500)
holding_cost = st.sidebar.number_input("Holding Cost per Unit/Period (H)", value=5)
initial_inventory = st.sidebar.number_input("Initial Inventory", value=30)
lead_time = st.sidebar.number_input("Lead Time (periods)", value=1)
safety_stock = st.sidebar.number_input("Safety Stock", value=0)

# Fungsi Helper untuk menghitung Net Requirement Global
def calculate_net_requirements(df, init_inv, ss):
    periods = len(df)
    gross_req = df['GR'].tolist()
    sch_rec = df['Scheduled_Receipts'].tolist()
    
    net_req_list = []
    projected_inv = init_inv
    
    for k in range(periods):
        # NR = Kebutuhan - (Stok + Penerimaan Terjadwal) + Safety Stock
        nr = max(0, gross_req[k] + ss - (projected_inv + sch_rec[k]))
        net_req_list.append(nr)
        # Update stok untuk periode berikutnya (Stok + NR + SR - GR)
        projected_inv = projected_inv + nr + sch_rec[k] - gross_req[k]
    
    return net_req_list

tabs = st.tabs(["MCP Cumulative", "Least Unit Cost (LUC)"])

# ---------------- Tab Logic (Universal for MCP & LUC) ----------------
for idx, tab_name in enumerate(["MCP", "LUC"]):
    with tabs[idx]:
        st.subheader(f"Metode {tab_name} - Iteration & Lead Time")
        uploaded_csv = st.file_uploader(f"Upload CSV for {tab_name}", type=["csv"], key=f"upload_{tab_name}")
        
        if uploaded_csv:
            df_input = pd.read_csv(uploaded_csv)
            periods = len(df_input)
            net_req_list = calculate_net_requirements(df_input, initial_inventory, safety_stock)
            
            all_iterations = []
            optimal_lots = []
            i = 0
            
            while i < periods:
                if net_req_list[i] <= 0:
                    i += 1
                    continue
                
                best_val = float('inf')
                best_lot = None
                
                for j in range(i, periods):
                    current_lot_size = sum(net_req_list[i:j+1])
                    
                    # 1. PERBAIKAN TEORI BIAYA SIMPAN
                    # Unit periode k ditarik ke periode i, maka disimpan selama (k-i) periode
                    holding_costs = sum(net_req_list[k] * (k - i) * holding_cost for k in range(i, j+1))
                    total_cost = setup_cost + holding_costs
                    
                    # 2. PEMILIHAN KRITERIA (MCP vs LUC)
                    if tab_name == "MCP":
                        criterion_val = total_cost / (j - i + 1) # Cost Per Period
                        label_crit = "Cost per Period"
                    else:
                        criterion_val = total_cost / current_lot_size if current_lot_size > 0 else float('inf') # Unit Cost
                        label_crit = "Unit Cost"
                    
                    iter_data = {
                        "Step": f"Start P{i+1}",
                        "Range": f"P{i+1}-P{j+1}",
                        "Lot Size": current_lot_size,
                        "Total Cost": total_cost,
                        label_crit: round(criterion_val, 2)
                    }
                    all_iterations.append(iter_data)

                    # Logic: Berhenti jika nilai kriteria mulai naik
                    if criterion_val <= best_val:
                        best_val = criterion_val
                        best_lot = {
                            "Receipt_Period": i + 1,
                            "Release_Period": (i + 1) - lead_time,
                            "Lot Size": current_lot_size,
                            "Total Cost": total_cost,
                            label_crit: round(criterion_val, 2),
                            "End_Idx": j
                        }
                    else:
                        break
                
                if best_lot:
                    optimal_lots.append(best_lot)
                    i = best_lot["End_Idx"] + 1
                else:
                    i += 1

            # --- DISPLAY ---
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("### Iteration Table")
                st.dataframe(pd.DataFrame(all_iterations), use_container_width=True)
            
            with col2:
                st.write("### Optimal Lots & Lead Time")
                df_opt = pd.DataFrame(optimal_lots)
                if not df_opt.empty:
                    # Logika Lead Time untuk kolom Release
                    df_opt['Release'] = df_opt['Release_Period'].apply(lambda x: f"P{x}" if x > 0 else "PAST DUE")
                    st.table(df_opt[['Receipt_Period', 'Release', 'Lot Size', label_crit]])

            # Download Result
            csv_buffer = BytesIO()
            df_opt.to_csv(csv_buffer, index=False)
            st.download_button(f"Download {tab_name} Result", data=csv_buffer.getvalue(), 
                               file_name=f"{tab_name}_mrp_result.csv", mime="text/csv")
