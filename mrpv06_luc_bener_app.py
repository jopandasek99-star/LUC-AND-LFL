import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="MRP MCP + LUC Final", layout="wide")
st.title("MRP App – MCP & LUC Final")

# Sidebar parameters
st.sidebar.header("Parameters")
setup_cost = st.sidebar.number_input("Setup Cost per Order (S)", value=500)
holding_cost = st.sidebar.number_input("Holding Cost per Unit (H)", value=5)
initial_inventory = st.sidebar.number_input("Initial Inventory", value=30)
lead_time = st.sidebar.number_input("Lead Time (periods)", value=1)
safety_stock = st.sidebar.number_input("Safety Stock", value=0)

# Create tabs
tabs = st.tabs(["MCP Cumulative", "Least Unit Cost (LUC)"])

# ---------------- MCP Tab ----------------
with tabs[0]:
    st.subheader("MCP Cumulative Iteration")
    uploaded_csv = st.file_uploader("Upload CSV (Period, GR, Scheduled_Receipts) for MCP", type=["csv"], key="mcp_tab")
    if uploaded_csv:
        df_input = pd.read_csv(uploaded_csv)
        periods = len(df_input)
        periods_label = [f"P{i+1}" for i in range(periods)]
        gross_req = df_input['GR'].tolist()
        scheduled_rec = df_input['Scheduled_Receipts'].tolist()

        all_iterations = []
        optimal_combinations = []
        i = 0
        current_inventory = initial_inventory
        prev_cost_per_period = None

        while i < periods:
            best_combo = None
            combos_tried = []

            for j in range(i, periods):
                # NR per periode
                temp_inventory = current_inventory
                nr_list = []
                for k in range(i, j+1):
                    nr = max(0, gross_req[k] + safety_stock - (temp_inventory + scheduled_rec[k]))
                    nr_list.append(nr)
                    temp_inventory += nr + scheduled_rec[k] - gross_req[k]

                net_demand = sum(nr_list)
                planned_receipt = [0]*(j-i+1)
                planned_receipt[0] = net_demand

                # Holding Cost per periode
                temp_inv2 = current_inventory
                cumulative_holding = 0
                for k, nr in zip(range(j-i+1), nr_list):
                    temp_inv2 += planned_receipt[k] + scheduled_rec[i+k] - gross_req[i+k]
                    cumulative_holding += max(temp_inv2,0)
                    temp_inv2 -= gross_req[i+k]

                total_cost = setup_cost + holding_cost * cumulative_holding
                cost_per_period = total_cost / (j-i+1)

                combos_tried.append({
                    "Period Combination": f"{periods_label[i]}-{periods_label[j]}" if i!=j else periods_label[i],
                    "Net Requirement": net_demand,
                    "Lot Size": net_demand,
                    "Total Cost": total_cost,
                    "Cost per Period": cost_per_period
                })

                # Stop iterasi jika Cost per Period naik
                if prev_cost_per_period is not None and cost_per_period > prev_cost_per_period:
                    break
                else:
                    best_combo = (i,j,net_demand,total_cost,cost_per_period)
                    prev_cost_per_period = cost_per_period

            if best_combo is None:
                best_combo = (i,i,nr_list[0], setup_cost + holding_cost*nr_list[0], setup_cost + holding_cost*nr_list[0])

            all_iterations.extend(combos_tried)
            start,end,lot_size,total_cost,cost_per_period = best_combo
            optimal_combinations.append({
                "Period Combination": f"{periods_label[start]}-{periods_label[end]}" if start!=end else periods_label[start],
                "Lot Size": lot_size,
                "Total Cost": total_cost,
                "Cost per Period": cost_per_period
            })

            # Update inventory
            for k in range(start,end+1):
                current_inventory += lot_size if k==start else 0
                current_inventory += scheduled_rec[k] - gross_req[k]

            i = end+1

        st.markdown("### All Iterations Tested (MCP)")
        st.dataframe(pd.DataFrame(all_iterations))
        st.markdown("### Optimal Combination per Step (MCP)")
        st.dataframe(pd.DataFrame(optimal_combinations))

        csv_buffer = BytesIO()
        combined = pd.concat([pd.DataFrame(all_iterations), pd.DataFrame(optimal_combinations)],
                             keys=["All Iterations","Optimal"])
        combined.to_csv(csv_buffer)
        st.download_button("Download MCP CSV", data=csv_buffer,
                           file_name="mcp_final_multitab.csv", mime="text/csv")

# ---------------- LUC Tab (Revised) ----------------
with tabs[1]:
    st.subheader("Least Unit Cost (LUC) Iteration - Corrected Logic")
    uploaded_csv = st.file_uploader("Upload CSV", type=["csv"], key="luc_tab_rev")
    
    if uploaded_csv:
        df_input = pd.read_csv(uploaded_csv)
        periods = len(df_input)
        gross_req = df_input['GR'].tolist()
        scheduled_rec = df_input['Scheduled_Receipts'].tolist()
        
        # --- LANGKAH 1: Hitung Net Requirement (NR) Global ---
        # Ini penting agar iterasi lot-sizing punya dasar angka yang tetap
        net_req_list = []
        projected_inv = initial_inventory
        for k in range(periods):
            # NR = Kebutuhan - (Stok di tangan + Jadwal Penerimaan) + Safety Stock
            nr = max(0, gross_req[k] + safety_stock - (projected_inv + scheduled_rec[k]))
            net_req_list.append(nr)
            # Update stok untuk periode berikutnya
            projected_inv = projected_inv + nr + scheduled_rec[k] - gross_req[k]

        # --- LANGKAH 2: Algoritma LUC ---
        all_iterations = []
        optimal_lots = []
        i = 0
        
        while i < periods:
            if net_req_list[i] <= 0: # Skip jika tidak ada kebutuhan
                i += 1
                continue
                
            best_unit_cost = float('inf')
            best_lot = None
            
            # Coba gabungkan periode i dengan periode-periode setelahnya
            for j in range(i, periods):
                current_lot_size = sum(net_req_list[i:j+1])
                
                # HITUNG BIAYA SIMPAN (LOGIKA BARU)
                # Hanya unit yang "ditarik" ke depan yang kena biaya simpan
                holding_costs = 0
                for k in range(i, j+1):
                    duration = k - i # Periode penyimpanan
                    holding_costs += net_req_list[k] * duration * holding_cost
                
                total_cost = setup_cost + holding_costs
                unit_cost = total_cost / current_lot_size if current_lot_size > 0 else float('inf')
                
                iter_data = {
                    "Step": f"Start P{i+1}",
                    "Try Combination": f"P{i+1}-P{j+1}",
                    "Lot Size": current_lot_size,
                    "Total Cost": total_cost,
                    "Unit Cost": round(unit_cost, 2)
                }
                all_iterations.append(iter_data)

                # Cek apakah Unit Cost masih turun
                if unit_cost <= best_unit_cost:
                    best_unit_cost = unit_cost
                    best_lot = {
                        "Receipt_Period": i + 1,
                        "Release_Period": (i + 1) - lead_time, # IMPLEMENTASI LEAD TIME
                        "Lot Size": current_lot_size,
                        "Total Cost": total_cost,
                        "Unit Cost": round(unit_cost, 2),
                        "Last_Period_Covered": j
                    }
                else:
                    break # Berhenti jika unit cost mulai naik
            
            if best_lot:
                optimal_lots.append(best_lot)
                i = best_lot["Last_Period_Covered"] + 1
            else:
                i += 1

        # --- TAMPILKAN HASIL ---
        st.write("### Iterasi Perhitungan LUC")
        st.dataframe(pd.DataFrame(all_iterations))

        st.write("### Hasil Akhir (Planned Order Release)")
        df_final = pd.DataFrame(optimal_lots)
        # Menangani Lead Time yang menghasilkan periode negatif
        df_final['Release_Status'] = df_final['Release_Period'].apply(lambda x: "Past Due" if x <= 0 else f"P{x}")
        st.dataframe(df_final[['Receipt_Period', 'Release_Status', 'Lot Size', 'Unit Cost']])
