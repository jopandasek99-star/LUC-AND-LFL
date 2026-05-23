import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="MRP App - MCP & LUC Final", layout="wide")
st.title("MRP App – Optimized MCP & LUC")

# Sidebar parameters
st.sidebar.header("Parameters")
setup_cost = st.sidebar.number_input("Setup Cost per Order (S)", value=500)
holding_cost = st.sidebar.number_input("Holding Cost per Unit/Period (H)", value=5)
initial_inventory = st.sidebar.number_input("Initial Inventory", value=30)
lead_time = st.sidebar.number_input("Lead Time (periods)", value=1)
safety_stock = st.sidebar.number_input("Safety Stock", value=0)

def calculate_net_requirements(df, init_inv, ss):
    periods = len(df)
    gross_req = df['GR'].tolist()
    sch_rec = df['Scheduled_Receipts'].tolist()
    net_req_list = []
    projected_inv = init_inv
    for k in range(periods):
        nr = max(0, gross_req[k] + ss - (projected_inv + sch_rec[k]))
        net_req_list.append(nr)
        projected_inv = projected_inv + nr + sch_rec[k] - gross_req[k]
    return net_req_list

tabs = st.tabs(["MCP Cumulative", "Least Unit Cost (LUC)"])

for idx, method in enumerate(["MCP", "LUC"]):
    with tabs[idx]:
        st.subheader(f"Metode {method}")
        uploaded_csv = st.file_uploader(f"Upload CSV for {method}", type=["csv"], key=f"upload_{method}")
        
        if uploaded_csv:
            df_input = pd.read_csv(uploaded_csv)
            periods = len(df_input)
            net_req_list = calculate_net_requirements(df_input, initial_inventory, safety_stock)
            
            all_iterations = []
            final_solution = []
            i = 0
            
            while i < periods:
                if net_req_list[i] <= 0:
                    i += 1
                    continue
                
                best_val = float('inf')
                best_lot = None
                
                for j in range(i, periods):
                    current_lot_size = sum(net_req_list[i:j+1])
                    holding_costs = sum(net_req_list[k] * (k - i) * holding_cost for k in range(i, j+1))
                    total_cost = setup_cost + holding_costs
                    
                    # Penentuan Kriteria
                    if method == "MCP":
                        crit_val = total_cost / (j - i + 1)
                        label_crit = "Cost per Period"
                    else:
                        crit_val = total_cost / current_lot_size if current_lot_size > 0 else float('inf')
                        label_crit = "Unit Cost"
                    
                    # Format Range: P1, P2, P3...
                    range_labels = [f"P{k+1}" for k in range(i, j+1)]
                    range_str = ", ".join(range_labels)
                    
                    all_iterations.append({
                        "Range": range_str,
                        "Lot Size": current_lot_size,
                        "Total Cost": total_cost,
                        label_crit: round(crit_val, 2)
                    })

                    if crit_val <= best_val:
                        best_val = crit_val
                        best_lot = {
                            "Order Period": i + 1,
                            "Release Period": (i + 1) - lead_time,
                            "Periods Covered": range_str,
                            "Lot Size": current_lot_size,
                            "Total Cost": total_cost,
                            "End_Idx": j
                        }
                    else:
                        break
                
                if best_lot:
                    final_solution.append(best_lot)
                    i = best_lot["End_Idx"] + 1
                else:
                    i += 1

            # 1. Tabel Iterasi
            st.markdown("### All Iterations Tested")
            st.dataframe(pd.DataFrame(all_iterations), use_container_width=True)
            
            # 2. Tabel Rangkuman Solusi Terbaik (Urutan Kolom Sesuai Instruksi)
            st.markdown("### Optimal Strategy Summary")
            df_res = pd.DataFrame(final_solution)
            if not df_res.empty:
                # Format tampilan periode
                df_res['Release At'] = df_res['Release Period'].apply(lambda x: f"P{x}" if x > 0 else "PAST DUE")
                df_res['Order At'] = df_res['Order Period'].apply(lambda x: f"P{x}")
                
                # Urutan kolom: Periods Covered -> Release At -> Order At
                display_cols = ['Periods Covered', 'Release At', 'Order At', 'Lot Size', 'Total Cost']
                st.table(df_res[display_cols])
                
                # 3. Total Cost Akhir
                grand_total = df_res['Total Cost'].sum()
                st.metric("Grand Total Cost for this Solution", f"{grand_total:,.2f}")
            
            # Download
            csv_buffer = BytesIO()
            df_res.to_csv(csv_buffer, index=False)
            st.download_button(f"Download {method} Solution", data=csv_buffer.getvalue(), file_name=f"{method}_solution.csv")
