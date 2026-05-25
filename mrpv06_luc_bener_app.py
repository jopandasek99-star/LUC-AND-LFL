import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from io import BytesIO

# ==========================================
# 1. KONFIGURASI HALAMAN & STYLE
# ==========================================
st.set_page_config(page_title="MRP Calculator - Multi-Metode Premium DSS", layout="wide")
st.title("📦 Aplikasi Perencanaan Kebutuhan Material (MRP) - Multi-Metode")
st.caption("Edisi DSS Lengkap: Perbandingan L4L, LUC (Versi Master), EOQ, dan Part Period Balancing (PPB)")
st.markdown("---")

# ==========================================
# 2. SIDEBAR - INPUT PARAMETER
# ==========================================
st.sidebar.header("🛠️ Parameter Input")
setup_cost = st.sidebar.number_input("Ordering / Setup Cost (S) (Rp)", min_value=0.0, value=100000.0, step=5000.0)
holding_cost = st.sidebar.number_input("Holding Cost (H) (Rp / unit / periode)", min_value=0.0, value=2000.0, step=500.0)
initial_inventory = st.sidebar.number_input("Persediaan Awal (Initial Inventory)", min_value=0, value=30, step=5)
safety_stock = st.sidebar.number_input("Safety Stock", min_value=0, value=0, step=1)
lead_time = st.sidebar.number_input("Lead Time (Periode)", min_value=0, value=1, step=1)

st.sidebar.markdown("---")
st.sidebar.header("🏬 Batasan Operasional")
max_capacity = st.sidebar.number_input("Kapasitas Maksimum Gudang (Unit)", min_value=1, value=100, step=10)

# ==========================================
# HELPER FUNCTIONS & STYLING
# ==========================================
def dapatkan_kolom_cocok(columns, targets):
    for col in columns:
        col_clean = str(col).strip().lower().replace("_", "").replace(" ", "")
        if col_clean in targets:
            return col
    return None

def highlight_cost_increase(row):
    if row['Is_Higher']:
        return ['background-color: #ffcccc; color: #cc0000; font-weight: bold'] * len(row)
    return [''] * len(row)

def get_styled_mrp_table(df_mrp_transposed, max_cap):
    def highlight_row_capacity(row):
        if row.name == 'Projected On Hand':
            return ['background-color: #ffe6cc; color: #cc6600; font-weight: bold;' if val > max_cap else '' for val in row]
        return [''] * len(row)
    return df_mrp_transposed.style.apply(highlight_row_capacity, axis=1)

def highlight_stop(row):
    return ['background-color: #ffcccc; color: black; font-weight: bold;' if row['Status'] == 'Stop! Biaya Naik' or row['Status'] == 'Stop! Melebihi Batas' else '' for _ in row]

# Fungsi Pre-Kalkulasi Net Requirements Global (Sesuai Logika Base Master)
def calculate_net_requirements(gross_req, sched_rec, init_inv, ss):
    periods = len(gross_req)
    net_req_list = []
    projected_inv = init_inv
    for k in range(periods):
        nr = max(0, gross_req[k] + ss - (projected_inv + sched_rec[k]))
        net_req_list.append(nr)
        projected_inv = projected_inv + nr + sched_rec[k] - gross_req[k]
    return net_req_list

# Helper POH & Release untuk metode standar teman
def generate_poh_and_release(rec_lot, demands, s_receipts, init_inv, lt):
    n = len(demands)
    poh = []
    r_inv = init_inv
    for i in range(n):
        r_inv += s_receipts[i] + rec_lot[i] - demands[i]
        poh.append(r_inv)
    
    rel_lot = [0] * n
    for i in range(n):
        if rec_lot[i] > 0:
            target = i - lt
            rel_lot[max(0, target)] += rec_lot[i]
    return poh, rel_lot

# ==========================================
# 3. AREA DATA INPUT
# ==========================================
st.subheader("📊 Data Kebutuhan Kotor & Penerimaan Terjadwal")
input_method = st.radio(
    "Pilih Metode Input Data:", 
    ["Upload File (Excel / CSV)", "Input Manual Langsung di Aplikasi", "Gunakan Data Contoh (Template)"]
)

df_kerja = None

if input_method == "Upload File (Excel / CSV)":
    uploaded_file = st.file_uploader("Upload file Anda di sini (Format file didukung: .xlsx, .xls, .csv)", type=["csv", "xlsx", "xls"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
            else:
                df_raw = pd.read_excel(uploaded_file)
                
            col_periode = dapatkan_kolom_cocok(df_raw.columns, ['periode', 'mingguke', 'p', 'minggu'])
            col_gr = dapatkan_kolom_cocok(df_raw.columns, ['gr', 'grossrequirement', 'grossrequirements', 'kebutuhankotor'])
            col_sr = dapatkan_kolom_cocok(df_raw.columns, ['sr', 'scheduledreceipt', 'scheduledreceipts', 'penerimaanterjadwal'])
            
            df_kerja = pd.DataFrame()
            if col_periode and col_periode in df_raw.columns:
                df_kerja['Periode'] = df_raw[col_periode].astype(str)
            else:
                df_kerja['Periode'] = [f"P{i+1}" for i in range(len(df_raw))]
                
            if col_gr and col_gr in df_raw.columns:
                df_kerja['Gross Requirements'] = df_raw[col_gr].fillna(0).astype(int)
            else:
                st.error("❌ Kolom Kebutuhan Kotor (GR) tidak terdeteksi otomatis.")
                
            if col_sr and col_sr in df_raw.columns:
                df_kerja['Scheduled Receipts'] = df_raw[col_sr].fillna(0).astype(int)
            else:
                df_kerja['Scheduled Receipts'] = 0
        except Exception as e:
            st.error(f"Gagal membaca file. Error: {e}")
            
elif input_method == "Input Manual Langsung di Aplikasi":
    num_periods_input = st.number_input("Tentukan Jumlah Periode Perencanaan:", min_value=1, max_value=52, value=8, step=1)
    init_data = {
        'Periode': [f"P{i+1}" for i in range(num_periods_input)],
        'Gross Requirements': [0] * num_periods_input,
        'Scheduled Receipts': [0] * num_periods_input
    }
    df_empty = pd.DataFrame(init_data)
    df_kerja = st.data_editor(df_empty, use_container_width=True, hide_index=True)

else:
    default_data = {
        'Periode': [f"P{i}" for i in range(1, 9)],
        'Gross Requirements': [30, 40, 20, 70, 40, 10, 30, 60],
        'Scheduled Receipts': [0, 10, 0, 0, 20, 0, 0, 0]
    }
    df_kerja = pd.DataFrame(default_data)

if df_kerja is not None and not df_kerja.empty:
    gross_req = df_kerja['Gross Requirements'].fillna(0).astype(int).tolist()
    sched_rec = df_kerja['Scheduled Receipts'].fillna(0).astype(int).tolist()
    period_labels = df_kerja['Periode'].astype(str).tolist()
    
    st.markdown("##### 🔍 Preview Ringkasan Data Input Aktif")
    df_preview_transposed = pd.DataFrame({
        'Gross Requirements': gross_req,
        'Scheduled Receipts': sched_rec
    }, index=period_labels).T
    
    df_edited_preview = st.data_editor(df_preview_transposed, use_container_width=True)
    gross_req = df_edited_preview.loc['Gross Requirements'].astype(int).tolist()
    sched_rec = df_edited_preview.loc['Scheduled Receipts'].astype(int).tolist()
    num_periods = len(gross_req)

    # Hitung Kebutuhan Bersih Dasar (Standardized Across Methods)
    net_req = calculate_net_requirements(gross_req, sched_rec, initial_inventory, safety_stock)

    # ==========================================
    # CORE ALGORITHM INTEGRATION
    # ==========================================
    
    # 1. LOT-FOR-LOT (L4L)
    l4l_rec = list(net_req)
    l4l_poh, l4l_rel = generate_poh_and_release(l4l_rec, gross_req, sched_rec, initial_inventory, lead_time)
    c_l4l_setup = sum(1 for x in l4l_rec if x > 0) * setup_cost
    c_l4l_hold = sum(l4l_poh) * holding_cost
    total_l4l = c_l4l_setup + c_l4l_hold

    # 2. LEAST UNIT COST (LUC) - LOGIKA MURNI MILIK MASTER
    luc_rec = [0] * num_periods
    all_luc_iterations = []
    final_luc_solution = []
    i = 0
    while i < num_periods:
        if net_req[i] <= 0:
            i += 1
            continue
        best_val = float('inf')
        best_lot = None
        prev_crit_val = None
        
        for j in range(i, num_periods):
            current_lot_size = sum(net_req[i:j+1])
            holding_costs = sum(net_req[k] * (k - i) * holding_cost for k in range(i, j+1))
            total_cost = setup_cost + holding_costs
            crit_val = total_cost / current_lot_size if current_lot_size > 0 else float('inf')
            
            is_higher = False
            if prev_crit_val is not None and crit_val > prev_crit_val:
                is_higher = True
            
            range_str = ", ".join([f"P{k+1}" for k in range(i, j+1)])
            all_luc_iterations.append({
                "Range": f"⚠️ {range_str}" if is_higher else range_str,
                "Lot Size": current_lot_size,
                "Total Cost": total_cost,
                "Unit Cost": round(crit_val, 2),
                "Is_Higher": is_higher
            })
            
            if not is_higher:
                best_val = crit_val
                best_lot = {
                    "Periods Covered": range_str,
                    "Release Period": (i + 1) - lead_time,
                    "Order Period": i + 1,
                    "Lot Size": current_lot_size,
                    "Total Cost": total_cost,
                    "End_Idx": j
                }
                prev_crit_val = crit_val
            else:
                break
        if best_lot:
            final_luc_solution.append(best_lot)
            luc_rec[i] = best_lot["Lot Size"]
            i = best_lot["End_Idx"] + 1
        else:
            i += 1
    luc_poh, luc_rel = generate_poh_and_release(luc_rec, gross_req, sched_rec, initial_inventory, lead_time)
    c_luc_setup = sum(1 for x in luc_rec if x > 0) * setup_cost
    c_luc_hold = sum(luc_poh) * holding_cost
    total_luc = c_luc_setup + c_luc_hold

    # 3. ECONOMIC ORDER QUANTITY (EOQ)
    avg_demand = np.mean(net_req)
    eoq_size = math.ceil(math.sqrt((2 * avg_demand * setup_cost) / holding_cost)) if holding_cost > 0 else 0
    eoq_rec = [0] * num_periods
    rem_stok = 0
    for idx_e in range(num_periods):
        if net_req[idx_e] > 0:
            if rem_stok < net_req[idx_e]:
                needed = net_req[idx_e] - rem_stok
                lots_to_order = math.ceil(needed / eoq_size) if eoq_size > 0 else 1
                eoq_rec[idx_e] = lots_to_order * eoq_size
                rem_stok = (eoq_rec[idx_e] + rem_stok) - net_req[idx_e]
            else:
                rem_stok -= net_req[idx_e]
    eoq_poh, eoq_rel = generate_poh_and_release(eoq_rec, gross_req, sched_rec, initial_inventory, lead_time)
    c_eoq_setup = sum(1 for x in eoq_rec if x > 0) * setup_cost
    c_eoq_hold = sum(eoq_poh) * holding_cost
    total_eoq = c_eoq_setup + c_eoq_hold

    # 4. PART PERIOD BALANCING (PPB)
    ppb_rec = [0] * num_periods
    ppb_iters = []
    idx_p = 0
    while idx_p < num_periods:
        if net_req[idx_p] == 0:
            idx_p += 1
            continue
        best_k = idx_p
        min_diff = float('inf')
        acc_d, acc_h = 0, 0
        t_log = []
        for k in range(idx_p, num_periods):
            acc_d += net_req[k]
            acc_h += net_req[k] * holding_cost * (k - idx_p)
            diff = abs(setup_cost - acc_h)
            
            if acc_h <= setup_cost:
                best_k = k
                status = "Mendekati Imbang"
                t_log.append({'Iterasi Dari': f"P{idx_p+1}", 'Hingga': f"P{k+1}", 'Total Unit': acc_d, 'Biaya Pesan': setup_cost, 'Biaya Simpan': acc_h, 'Selisih |S-H|': diff, 'Status': status})
            else:
                status = "Stop! Melebihi Batas"
                t_log.append({'Iterasi Dari': f"P{idx_p+1}", 'Hingga': f"P{k+1}", 'Total Unit': acc_d, 'Biaya Pesan': setup_cost, 'Biaya Simpan': acc_h, 'Selisih |S-H|': diff, 'Status': status})
                break
        ppb_iters.append(pd.DataFrame(t_log))
        ppb_rec[idx_p] = sum(net_req[idx_p:best_k+1])
        idx_p = best_k + 1
    ppb_poh, ppb_rel = generate_poh_and_release(ppb_rec, gross_req, sched_rec, initial_inventory, lead_time)
    c_ppb_setup = sum(1 for x in ppb_rec if x > 0) * setup_cost
    c_ppb_hold = sum(ppb_poh) * holding_cost
    total_ppb = c_ppb_setup + c_ppb_hold

    # ==========================================
    # 4. DASHBOARD RESULTS COMPILATION
    # ==========================================
    st.markdown("---")
    st.header("🏁 Hasil Komparasi Performa Multi-Metode")
    
    biaya_dict = {
        'Lot-for-Lot (L4L)': total_l4l, 
        'Least Unit Cost (LUC)': total_luc, 
        'Economic Order Quantity (EOQ)': total_eoq, 
        'Part Period Balancing (PPB)': total_ppb
    }
    best_method = min(biaya_dict, key=biaya_dict.get)
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        diff_l4l = total_l4l - biaya_dict[best_method]
        sub = f"<div style='color: #d9534f; font-size:14px; font-weight:bold;'>↓ Rp {diff_l4l:,.0f} Lebih Boros</div>" if diff_l4l > 0 else "<div style='color: #5cb85c; font-size:14px; font-weight:bold;'>🏆 Paling Optimal</div>"
        st.markdown(f"<div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 5px solid #FF6B6B;'><b>Total Biaya L4L</b><br><span style='font-size: 22px; font-weight:bold;'>Rp {total_l4l:,.0f}</span>{sub}</div>", unsafe_allow_html=True)
    with m2:
        diff_luc = total_luc - biaya_dict[best_method]
        sub = f"<div style='color: #d9534f; font-size:14px; font-weight:bold;'>↓ Rp {diff_luc:,.0f} Lebih Boros</div>" if diff_luc > 0 else "<div style='color: #5cb85c; font-size:14px; font-weight:bold;'>🏆 Paling Optimal</div>"
        st.markdown(f"<div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 5px solid #4D96FF;'><b>Total Biaya LUC</b><br><span style='font-size: 22px; font-weight:bold;'>Rp {total_luc:,.0f}</span>{sub}</div>", unsafe_allow_html=True)
    with m3:
        diff_eoq = total_eoq - biaya_dict[best_method]
        sub = f"<div style='color: #d9534f; font-size:14px; font-weight:bold;'>↓ Rp {diff_eoq:,.0f} Lebih Boros</div>" if diff_eoq > 0 else "<div style='color: #5cb85c; font-size:14px; font-weight:bold;'>🏆 Paling Optimal</div>"
        st.markdown(f"<div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 5px solid #6BCB77;'><b>Total Biaya EOQ</b><br><span style='font-size: 22px; font-weight:bold;'>Rp {total_eoq:,.0f}</span>{sub}</div>", unsafe_allow_html=True)
    with m4:
        diff_ppb = total_ppb - biaya_dict[best_method]
        sub = f"<div style='color: #d9534f; font-size:14px; font-weight:bold;'>↓ Rp {diff_ppb:,.0f} Lebih Boros</div>" if diff_ppb > 0 else "<div style='color: #5cb85c; font-size:14px; font-weight:bold;'>🏆 Paling Optimal</div>"
        st.markdown(f"<div style='background-color: #f8f9fa; padding: 16px; border-radius: 8px; border-left: 5px solid #f9d949;'><b>Total Biaya PPB</b><br><span style='font-size: 22px; font-weight:bold;'>Rp {total_ppb:,.0f}</span>{sub}</div>", unsafe_allow_html=True)

    st.success(f"🏆 **Rekomendasi Keputusan:** Metode **{best_method}** menghasilkan efisiensi biaya paling tinggi.")

    # ==========================================
    # 5. TABS RENDER MANAGEMENT
    # ==========================================
    tab_grafik, t_l4l, t_luc, t_eoq, t_ppb = st.tabs(["📉 Grafik & Komparasi", "📋 Lot-for-Lot (L4L)", "🔍 Least Unit Cost (LUC)", "🎯 Economic Order Quantity (EOQ)", "⚖️ Part Period Balancing (PPB)"])

    # REUSABLE MRP TABLE RENDERER
    def tampilkan_tabel_mrp(nama_metode, data_poh, data_rec, data_rel, max_cap):
        df_mrp = pd.DataFrame({
            'Gross Requirements': gross_req,
            'Scheduled Receipts': sched_rec,
            'Projected On Hand': data_poh,
            'Net Requirements': net_req,
            'Planned Order Receipts': data_rec,
            'Planned Order Releases': data_rel
        }, index=[f"P{i+1}" for i in range(num_periods)]).T
        st.dataframe(get_styled_mrp_table(df_mrp, max_cap), use_container_width=True)
        if max(data_poh) > max_cap:
            st.error(f"⚠️ **Kapasitas Gudang Terlampaui:** Akumulasi stok pada {nama_metode} melebihi limit limit gudang ({max_cap} unit).")

    # TAB GRAFIK KOMPARASI
    with tab_grafik:
        cg1, cg2 = st.columns(2)
        with cg1:
            st.markdown("### Komparasi Total Biaya (Rp)")
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(biaya_dict.keys(), biaya_dict.values(), color=['#FF6B6B', '#4D96FF', '#6BCB77', '#f9d949'])
            plt.xticks(rotation=20, ha='right')
            ax.grid(axis='y', linestyle='--', alpha=0.5)
            st.pyplot(fig)
        with cg2:
            st.markdown("### Analisis Sensitivitas Perubahan Demand")
            scale_factors = np.arange(0.70, 1.35, 0.05)
            s_l4l, s_luc, s_eoq, s_ppb, labels_pct = [], [], [], [], []
            for f in scale_factors:
                sim_demand = [max(1, int(d * f)) for d in gross_req]
                # Simulasi Simpel Sensitivitas
                sim_net = calculate_net_requirements(sim_demand, sched_rec, initial_inventory, safety_stock)
                s_l4l.append(sum(1 for x in sim_net if x > 0) * setup_cost)
                s_luc.append(total_luc * f) # Estimasi Linear Sensitivitas
                s_eoq.append(total_eoq * f)
                s_ppb.append(total_ppb * f)
                labels_pct.append(f"{int(round((f-1)*100)):+}%")
            
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            ax2.plot(labels_pct, s_l4l, marker='o', label='L4L', color='#FF6B6B')
            ax2.plot(labels_pct, s_luc, marker='s', label='LUC', color='#4D96FF')
            ax2.plot(labels_pct, s_eoq, marker='^', label='EOQ', color='#6BCB77')
            ax2.plot(labels_pct, s_ppb, marker='x', label='PPB', color='#f9d949')
            ax2.set_ylabel('Total Biaya (Rp)')
            ax2.grid(True, linestyle=':', alpha=0.6)
            ax2.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig2)

    # TAB L4L
    with t_l4l:
        st.subheader("Tabel Hasil Analisis MRP - Lot-for-Lot")
        tampilkan_tabel_mrp("L4L", l4l_poh, l4l_rec, l4l_rel, max_capacity)

    # TAB LUC - INTEGRASI KELAS EMAS (LOGIKA MASTER)
    with t_luc:
        st.subheader("Tabel Analisis MRP - Least Unit Cost")
        
        # 1. Tampilkan tabel iterasi dengan styling siluman ala Master
        st.markdown("### All Iterations Tested")
        st.write("> **Note:** Baris berwarna merah (⚠️) menunjukkan kombinasi yang mulai tidak ekonomis.")
        df_iter = pd.DataFrame(all_luc_iterations)
        styled_iter = df_iter.style.apply(highlight_cost_increase, axis=1)
        st.dataframe(
            styled_iter.hide(axis="index").set_properties(**{'text-align': 'left'}), 
            use_container_width=True,
            column_order=("Range", "Lot Size", "Total Cost", "Unit Cost")
        )
        
        # 2. Tampilkan Rangkuman Solusi Urutan Kronologis Master
        st.markdown("---")
        st.markdown("### Optimal Strategy Summary")
        df_res = pd.DataFrame(final_luc_solution)
        if not df_res.empty:
            df_res['Release At'] = df_res['Release Period'].apply(lambda x: f"P{x}" if x > 0 else "PAST DUE")
            df_res['Order At'] = df_res['Order Period'].apply(lambda x: f"P{x}")
            
            display_cols = ['Periods Covered', 'Release At', 'Order At', 'Lot Size', 'Total Cost']
            st.table(df_res[display_cols])
            st.metric("Grand Total Cost (LUC)", f"Rp {total_luc:,.2f}")
            
        # 3. Tampilkan Matrix MRP Utama Horisontal di bawahnya
        st.markdown("---")
        st.markdown("### Grid Matrix View MRP (LUC)")
        tampilkan_tabel_mrp("LUC", luc_poh, luc_rec, luc_rel, max_capacity)

    # TAB EOQ
    with t_eoq:
        st.subheader("Tabel Hasil Analisis MRP - Economic Order Quantity")
        with st.expander("🔬 KLIK DI SINI UNTUK MELIHAT LOG PERHITUNGAN RUMUS DETAIL (EOQ)"):
            total_net_req = sum(net_req)
            avg_demand_calc = total_net_req / num_periods
            st.markdown(f"""
            * Total Kebutuhan Bersih ($\sum$ Net Req) = `{total_net_req}` unit
            * Rata-rata Kebutuhan per Periode ($D$) = `{avg_demand_calc:.4f}` unit/periode
            """)
            st.markdown(f"$$EOQ = \\sqrt{{\\frac{{2 \\times {avg_demand_calc:.4f} \\times {setup_cost:,.2f}}}{{{holding_cost:,.2f}}}}}$$")
            st.markdown(f"* Ukuran Lot Statis Dibulatkan Keatas (Ceil) = **`{eoq_size}` unit**.")
            
        st.info(f"💡 **Informasi Ukuran Lot Fixed:** Ukuran lot tetap untuk metode EOQ dikunci bernilai **{eoq_size} unit** per pesanan.")
        tampilkan_tabel_mrp("EOQ", eoq_poh, eoq_rec, eoq_rel, max_capacity)

    # TAB PPB
    with t_ppb:
        st.subheader("Proses & Tabel Analisis MRP - Part Period Balancing")
        with st.expander("🔬 KLIK DI SINI UNTUK MELIHAT LOG ITERASI KESEIMBANGAN PART PERIOD (PPB)"):
            format_ppb = {'Biaya Pesan': '{:.2f}', 'Biaya Simpan': '{:.2f}', 'Selisih |S-H|': '{:.2f}'}
            for idx_block, df_iter_ppb in enumerate(ppb_iters):
                st.markdown(f"**Langkah Pembentukan Lot Ke-{idx_block+1}:**")
                styled_df = df_iter_ppb.style.apply(highlight_stop, axis=1).format(format_ppb)
                st.dataframe(styled_df, hide_index=True, use_container_width=True)
                st.markdown("---")
        tampilkan_tabel_mrp("PPB", ppb_poh, ppb_rec, ppb_rel, max_capacity)

    # ==========================================
    # 6. EXPORT LAPORAN EXCEL MULTI-METODE
    # ==========================================
    st.markdown("---")
    st.subheader("💾 Ekspor Laporan Multi-Metode")
    
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        pd.DataFrame({'Gross Requirements': gross_req, 'Scheduled Receipts': sched_rec, 'Net Requirements': net_req}, index=[f"P{i+1}" for i in range(num_periods)]).T.to_excel(writer, sheet_name="Data Kebutuhan Dasar")
        pd.DataFrame({'Projected On Hand': l4l_poh, 'Planned Order Receipts': l4l_rec, 'Planned Order Releases': l4l_rel}, index=[f"P{i+1}" for i in range(num_periods)]).T.to_excel(writer, sheet_name="Metode L4L")
        pd.DataFrame({'Projected On Hand': luc_poh, 'Planned Order Receipts': luc_rec, 'Planned Order Releases': luc_rel}, index=[f"P{i+1}" for i in range(num_periods)]).T.to_excel(writer, sheet_name="Metode LUC")
        pd.DataFrame({'Projected On Hand': eoq_poh, 'Planned Order Receipts': eoq_rec, 'Planned Order Releases': eoq_rel}, index=[f"P{i+1}" for i in range(num_periods)]).T.to_excel(writer, sheet_name="Metode EOQ")
        pd.DataFrame({'Projected On Hand': ppb_poh, 'Planned Order Receipts': ppb_rec, 'Planned Order Releases': ppb_rel}, index=[f"P{i+1}" for i in range(num_periods)]).T.to_excel(writer, sheet_name="Metode PPB")
    
    st.download_button(
        label="📥 Download Hasil Perhitungan 4 Metode (Excel)", 
        data=excel_buffer.getvalue(), 
        file_name="Laporan_MRP_MultiMetode_Final.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("💡 Hubungkan atau masukkan data kebutuhan di atas terlebih dahulu untuk memulai perhitungan otomasi MRP.")
