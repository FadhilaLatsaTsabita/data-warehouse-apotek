# ============================================================
# DASHBOARD DATA WAREHOUSE
# Studi Kasus Simulasi Jaringan Apotek Ritel Internal Kimia Farma
# ============================================================

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine

# Masukkan Connection String dari Supabase
engine = create_engine(st.secrets["DB_URL"])

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Kimia Farma DW Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>
    .main {
        background-color: #F8FAFC;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    .dashboard-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }

    .dashboard-subtitle {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 1.3rem;
        margin-bottom: 0.7rem;
    }

    .insight-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        margin-top: 0.6rem;
        margin-bottom: 1rem;
        box-shadow: 0px 4px 12px rgba(15, 23, 42, 0.04);
    }

    .insight-title {
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.35rem;
    }

    .insight-text {
        color: #475569;
        font-size: 0.92rem;
        line-height: 1.45;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.45rem;
        font-weight: 800;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #64748B;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

DATA_DIR = "data_warehouse"


def format_rupiah(value):
    """Format angka menjadi Rupiah."""
    try:
        value = float(value)
        return f"Rp{value:,.0f}".replace(",", ".")
    except Exception:
        return "Rp0"


def safe_read_csv(path):
    """Membaca CSV dengan validasi file."""
    if not os.path.exists(path):
        st.error(f"File tidak ditemukan: {path}")
        st.stop()
    return pd.read_csv(path)


def normalize_columns(df):
    """Membersihkan nama kolom dari spasi."""
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def find_col(df, candidates):
    """
    Mencari kolom berdasarkan beberapa kemungkinan nama.
    Berguna kalau nama kolom sedikit berbeda.
    """
    lower_map = {col.lower(): col for col in df.columns}

    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]

    return None


@st.cache_data
def load_data():
    """Load semua tabel fact dan dimension langsung dari Supabase (PostgreSQL)."""
    
    # Menarik semua tabel secara langsung menggunakan Query SQL
    fact_penjualan = pd.read_sql("SELECT * FROM fact_penjualan", engine)
    dim_produk     = pd.read_sql("SELECT * FROM dim_produk", engine)
    dim_apotek     = pd.read_sql("SELECT * FROM dim_apotek", engine)
    dim_pelanggan  = pd.read_sql("SELECT * FROM dim_pelanggan", engine)
    dim_karyawan   = pd.read_sql("SELECT * FROM dim_karyawan", engine)
    dim_supplier   = pd.read_sql("SELECT * FROM dim_supplier", engine)
    dim_waktu      = pd.read_sql("SELECT * FROM dim_waktu", engine)

    # Gabungkan ke dalam satu list
    tables = [
        fact_penjualan,
        dim_produk,
        dim_apotek,
        dim_pelanggan,
        dim_karyawan,
        dim_supplier,
        dim_waktu,
    ]

    # Membersihkan nama kolom (opsional tapi disarankan agar rapi saat di-join)
    tables = [normalize_columns(df) for df in tables]

    return tables


def build_analytical_df(
    fact,
    dim_produk,
    dim_apotek,
    dim_pelanggan,
    dim_karyawan,
    dim_supplier,
    dim_waktu
):
    """Join fact table dengan semua dimension table."""

    df = fact.copy()

    # Join dim produk
    if "ProdukID" in df.columns and "ProdukID" in dim_produk.columns:
        df = df.merge(dim_produk, on="ProdukID", how="left", suffixes=("", "_Produk"))

    # Join dim apotek
    if "ApotekID" in df.columns and "ApotekID" in dim_apotek.columns:
        df = df.merge(dim_apotek, on="ApotekID", how="left", suffixes=("", "_Apotek"))

    # Join dim pelanggan
    if "PelangganID" in df.columns and "PelangganID" in dim_pelanggan.columns:
        df = df.merge(dim_pelanggan, on="PelangganID", how="left", suffixes=("", "_Pelanggan"))

    # Join dim karyawan
    if "KaryawanID" in df.columns and "KaryawanID" in dim_karyawan.columns:
        df = df.merge(dim_karyawan, on="KaryawanID", how="left", suffixes=("", "_Karyawan"))

    # Join dim supplier
    if "SupplierID" in df.columns and "SupplierID" in dim_supplier.columns:
        df = df.merge(dim_supplier, on="SupplierID", how="left", suffixes=("", "_Supplier"))

    # Join dim waktu
    if "WaktuID" in df.columns and "WaktuID" in dim_waktu.columns:
        df = df.merge(dim_waktu, on="WaktuID", how="left", suffixes=("", "_Waktu"))

    return df


def prepare_data_types(df):
    """Menyiapkan tipe data agar aman untuk chart."""

    df = df.copy()

    numeric_candidates = [
        "JumlahTerjual",
        "HargaSatuan",
        "Diskon",
        "TotalPenjualan",
        "Keuntungan",
        "Usia",
        "Tahun",
        "NomorBulan"
    ]

    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Tanggal" in df.columns:
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")

    return df


def insight_box(title, text):
    """Menampilkan kotak insight."""
    st.markdown(
        f"""
        <div class="insight-box">
            <div class="insight-title">{title}</div>
            <div class="insight-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def check_required_columns(df):
    """Validasi kolom minimum dashboard."""
    required = ["TotalPenjualan", "Keuntungan", "JumlahTerjual", "FakturID"]
    missing = [col for col in required if col not in df.columns]

    if missing:
        st.warning(
            "Beberapa kolom utama tidak ditemukan di data hasil join: "
            + ", ".join(missing)
            + ". Pastikan output ETL sudah sesuai."
        )


# ============================================================
# LOAD DATA
# ============================================================

fact_penjualan, dim_produk, dim_apotek, dim_pelanggan, dim_karyawan, dim_supplier, dim_waktu = load_data()

df = build_analytical_df(
    fact_penjualan,
    dim_produk,
    dim_apotek,
    dim_pelanggan,
    dim_karyawan,
    dim_supplier,
    dim_waktu
)

df = prepare_data_types(df)
check_required_columns(df)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("💊 Kimia Farma DW")
st.sidebar.caption("Dashboard BI berbasis Star Schema")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Pilih Halaman",
    [
        "Overview",
        "Analisis Produk",
        "Analisis Cabang & Wilayah",
        "Analisis Waktu",
        "Analisis Pelanggan",
        "Analisis Supplier",
        "Analisis Karyawan",
        "Analisis OLAP",
        "Data Preview"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filter Data")

filtered_df = df.copy()

# Filter Tahun
if "Tahun" in filtered_df.columns:
    tahun_options = sorted(filtered_df["Tahun"].dropna().astype(int).unique().tolist())
    selected_tahun = st.sidebar.multiselect(
        "Tahun",
        options=tahun_options,
        default=tahun_options
    )
    if selected_tahun:
        filtered_df = filtered_df[filtered_df["Tahun"].astype(int).isin(selected_tahun)]

# Filter Bulan
if "Bulan" in filtered_df.columns:
    bulan_options = filtered_df["Bulan"].dropna().unique().tolist()
    selected_bulan = st.sidebar.multiselect(
        "Bulan",
        options=bulan_options,
        default=bulan_options
    )
    if selected_bulan:
        filtered_df = filtered_df[filtered_df["Bulan"].isin(selected_bulan)]

# Filter Kota Apotek
kota_col = find_col(filtered_df, ["Kota", "Kota_Apotek"])
if kota_col:
    kota_options = sorted(filtered_df[kota_col].dropna().unique().tolist())
    selected_kota = st.sidebar.multiselect(
        "Kota Apotek",
        options=kota_options,
        default=kota_options
    )
    if selected_kota:
        filtered_df = filtered_df[filtered_df[kota_col].isin(selected_kota)]

# Filter Kategori Produk
kategori_col = find_col(filtered_df, ["KategoriProduk", "Kategori_Produk"])
if kategori_col:
    kategori_options = sorted(filtered_df[kategori_col].dropna().unique().tolist())
    selected_kategori = st.sidebar.multiselect(
        "Kategori Produk",
        options=kategori_options,
        default=kategori_options
    )
    if selected_kategori:
        filtered_df = filtered_df[filtered_df[kategori_col].isin(selected_kategori)]

st.sidebar.markdown("---")
st.sidebar.caption("Dataset bersifat sintetis untuk simulasi Data Warehouse.")


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="dashboard-title">Dashboard Data Warehouse Kimia Farma</div>
    <div class="dashboard-subtitle">
        Studi kasus simulasi jaringan apotek ritel internal Kimia Farma berbasis Star Schema.
        Data yang digunakan merupakan dataset sintetis, bukan data asli perusahaan.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# GLOBAL EMPTY CHECK
# ============================================================

if filtered_df.empty:
    st.warning("Data kosong setelah filter diterapkan. Silakan ubah filter di sidebar.")
    st.stop()


# ============================================================
# COMMON KPI
# ============================================================

def render_kpi(data):
    total_penjualan = data["TotalPenjualan"].sum() if "TotalPenjualan" in data.columns else 0
    total_keuntungan = data["Keuntungan"].sum() if "Keuntungan" in data.columns else 0
    jumlah_transaksi = data["FakturID"].nunique() if "FakturID" in data.columns else len(data)
    total_produk_terjual = data["JumlahTerjual"].sum() if "JumlahTerjual" in data.columns else 0
    avg_transaksi = total_penjualan / jumlah_transaksi if jumlah_transaksi > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Penjualan", format_rupiah(total_penjualan))
    col2.metric("Total Keuntungan", format_rupiah(total_keuntungan))
    col3.metric("Jumlah Transaksi", f"{jumlah_transaksi:,}".replace(",", "."))
    col4.metric("Produk Terjual", f"{int(total_produk_terjual):,}".replace(",", "."))
    col5.metric("Rata-rata Transaksi", format_rupiah(avg_transaksi))


# ============================================================
# PAGE: OVERVIEW
# ============================================================

if page == "Overview":
    st.markdown('<div class="section-title">Overview Penjualan</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    st.markdown('<div class="section-title">Ringkasan Visual</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if kategori_col and "TotalPenjualan" in filtered_df.columns:
            kategori_sales = (
                filtered_df
                .groupby(kategori_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
            )

            fig = px.bar(
                kategori_sales,
                x=kategori_col,
                y="TotalPenjualan",
                title="Total Penjualan per Kategori Produk",
                text_auto=".2s"
            )
            fig.update_layout(xaxis_title="Kategori Produk", yaxis_title="Total Penjualan")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if kota_col and "TotalPenjualan" in filtered_df.columns:
            kota_sales = (
                filtered_df
                .groupby(kota_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                kota_sales,
                x=kota_col,
                y="TotalPenjualan",
                title="Top 10 Kota Berdasarkan Penjualan",
                text_auto=".2s"
            )
            fig.update_layout(xaxis_title="Kota", yaxis_title="Total Penjualan")
            st.plotly_chart(fig, use_container_width=True)

    if kota_col and "TotalPenjualan" in filtered_df.columns:
        top_kota = (
            filtered_df
            .groupby(kota_col)["TotalPenjualan"]
            .sum()
            .sort_values(ascending=False)
        )

        if not top_kota.empty:
            insight_box(
                "Insight Overview",
                f"Berdasarkan dataset simulasi, kota dengan kontribusi penjualan tertinggi adalah "
                f"<b>{top_kota.index[0]}</b> dengan total penjualan sebesar "
                f"<b>{format_rupiah(top_kota.iloc[0])}</b>. "
                f"Manajemen dapat mempertimbangkan peningkatan stok dan promosi lokal pada kota dengan performa tinggi."
            )


# ============================================================
# PAGE: ANALISIS PRODUK
# ============================================================

elif page == "Analisis Produk":
    st.markdown('<div class="section-title">Analisis Produk</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    nama_produk_col = find_col(filtered_df, ["NamaProduk", "Nama_Produk"])
    brand_col = find_col(filtered_df, ["Brand"])

    col1, col2 = st.columns(2)

    with col1:
        if nama_produk_col and "JumlahTerjual" in filtered_df.columns:
            top_produk_qty = (
                filtered_df
                .groupby(nama_produk_col, as_index=False)
                .agg(JumlahTerjual=("JumlahTerjual", "sum"))
                .sort_values("JumlahTerjual", ascending=False)
                .head(10)
            )

            fig = px.bar(
                top_produk_qty,
                x="JumlahTerjual",
                y=nama_produk_col,
                orientation="h",
                title="Top 10 Produk Paling Laris",
                text_auto=True
            )
            fig.update_layout(yaxis_title="Produk", xaxis_title="Jumlah Terjual")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if nama_produk_col and "TotalPenjualan" in filtered_df.columns:
            top_produk_sales = (
                filtered_df
                .groupby(nama_produk_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                top_produk_sales,
                x="TotalPenjualan",
                y=nama_produk_col,
                orientation="h",
                title="Top 10 Produk Berdasarkan Revenue",
                text_auto=".2s"
            )
            fig.update_layout(yaxis_title="Produk", xaxis_title="Total Penjualan")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if kategori_col and "Keuntungan" in filtered_df.columns:
            kategori_profit = (
                filtered_df
                .groupby(kategori_col, as_index=False)
                .agg(Keuntungan=("Keuntungan", "sum"))
                .sort_values("Keuntungan", ascending=False)
            )

            fig = px.pie(
                kategori_profit,
                names=kategori_col,
                values="Keuntungan",
                title="Proporsi Keuntungan per Kategori Produk"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if brand_col and "TotalPenjualan" in filtered_df.columns:
            brand_sales = (
                filtered_df
                .groupby(brand_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                brand_sales,
                x=brand_col,
                y="TotalPenjualan",
                title="Top Brand Berdasarkan Penjualan",
                text_auto=".2s"
            )
            fig.update_layout(xaxis_title="Brand", yaxis_title="Total Penjualan")
            st.plotly_chart(fig, use_container_width=True)

    if nama_produk_col and "TotalPenjualan" in filtered_df.columns:
        top_product = (
            filtered_df
            .groupby(nama_produk_col)["TotalPenjualan"]
            .sum()
            .sort_values(ascending=False)
        )

        if not top_product.empty:
            insight_box(
                "Insight Produk",
                f"Produk dengan kontribusi penjualan tertinggi adalah <b>{top_product.index[0]}</b> "
                f"dengan total penjualan sebesar <b>{format_rupiah(top_product.iloc[0])}</b>. "
                f"Keputusan yang dapat diambil adalah menjaga ketersediaan stok produk tersebut, "
                f"menjadikannya prioritas promosi, atau membuat bundling dengan produk yang penjualannya lebih rendah."
            )


# ============================================================
# PAGE: ANALISIS CABANG & WILAYAH
# ============================================================

elif page == "Analisis Cabang & Wilayah":
    st.markdown('<div class="section-title">Analisis Cabang, Kota, dan Wilayah</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    nama_apotek_col = find_col(filtered_df, ["NamaApotek", "Nama_Apotek"])
    wilayah_col = find_col(filtered_df, ["Wilayah"])
    provinsi_col = find_col(filtered_df, ["Provinsi", "Provinsi_Apotek"])

    col1, col2 = st.columns(2)

    with col1:
        if nama_apotek_col and "TotalPenjualan" in filtered_df.columns:
            top_apotek = (
                filtered_df
                .groupby(nama_apotek_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                top_apotek,
                x="TotalPenjualan",
                y=nama_apotek_col,
                orientation="h",
                title="Top 10 Cabang Apotek Berdasarkan Penjualan",
                text_auto=".2s"
            )
            fig.update_layout(yaxis_title="Cabang Apotek", xaxis_title="Total Penjualan")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if kota_col and "TotalPenjualan" in filtered_df.columns:
            kota_sales = (
                filtered_df
                .groupby(kota_col, as_index=False)
                .agg(
                    TotalPenjualan=("TotalPenjualan", "sum"),
                    Keuntungan=("Keuntungan", "sum"),
                    JumlahTransaksi=("FakturID", "count")
                )
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                kota_sales,
                x=kota_col,
                y="TotalPenjualan",
                title="Top 10 Kota Berdasarkan Total Penjualan",
                text_auto=".2s"
            )
            fig.update_layout(xaxis_title="Kota", yaxis_title="Total Penjualan")
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if wilayah_col and "TotalPenjualan" in filtered_df.columns:
            wilayah_sales = (
                filtered_df
                .groupby(wilayah_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
            )

            fig = px.pie(
                wilayah_sales,
                names=wilayah_col,
                values="TotalPenjualan",
                title="Proporsi Penjualan per Wilayah"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if provinsi_col and "Keuntungan" in filtered_df.columns:
            provinsi_profit = (
                filtered_df
                .groupby(provinsi_col, as_index=False)
                .agg(Keuntungan=("Keuntungan", "sum"))
                .sort_values("Keuntungan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                provinsi_profit,
                x=provinsi_col,
                y="Keuntungan",
                title="Top 10 Provinsi Berdasarkan Keuntungan",
                text_auto=".2s"
            )
            fig.update_layout(xaxis_title="Provinsi", yaxis_title="Keuntungan")
            st.plotly_chart(fig, use_container_width=True)

    # --- TAMBAHAN INSIGHT 2: MALL VS KLINIK (JAWA BARAT) ---
    st.markdown('<div class="section-title">Fokus Geografis: Profitabilitas Tipe Apotek di Jawa Barat</div>', unsafe_allow_html=True)
    
    prov_col = find_col(filtered_df, ["Provinsi", "Provinsi_Apotek"])
    tipe_apt_col = find_col(filtered_df, ["TipeCabang", "Tipe_Apotek"])
    profit_col = find_col(filtered_df, ["Keuntungan", "keuntungan"])

    if prov_col and tipe_apt_col and profit_col:
        filter_jabar_tipe = filtered_df[
            (filtered_df[prov_col].astype(str).str.contains("Jawa Barat", case=False, na=False)) &
            (filtered_df[tipe_apt_col].astype(str).str.contains("Mall|Klinik", case=False, na=False))
        ]
        
        if not filter_jabar_tipe.empty:
            insight_cabang_jabar = (
                filter_jabar_tipe
                .groupby(tipe_apt_col, as_index=False)
                .agg(Total_Keuntungan=(profit_col, "sum"))
                .sort_values("Total_Keuntungan", ascending=False)
            )
            
            fig_jabar = px.bar(
                insight_cabang_jabar,
                x=tipe_apt_col,
                y="Total_Keuntungan",
                title="Perbandingan Margin Keuntungan Cabang Mall/Commercial vs Klinik Terintegrasi di Jawa Barat",
                text_auto=".2s",
                color=tipe_apt_col
            )
            fig_jabar.update_layout(xaxis_title="Tipe Apotek", yaxis_title="Total Keuntungan")
            st.plotly_chart(fig_jabar, use_container_width=True)
        else:
            st.info("Tidak ada data untuk tipe apotek Mall/Klinik di Jawa Barat pada filter saat ini.")

    if kota_col and "TotalPenjualan" in filtered_df.columns:
        city_rank = (
            filtered_df
            .groupby(kota_col)["TotalPenjualan"]
            .sum()
            .sort_values(ascending=False)
        )

        if not city_rank.empty:
            insight_box(
                "Insight Cabang & Wilayah",
                f"Kota dengan penjualan tertinggi adalah <b>{city_rank.index[0]}</b> "
                f"dengan total penjualan <b>{format_rupiah(city_rank.iloc[0])}</b>. "
                f"Keputusan yang dapat diambil adalah memperkuat distribusi produk, "
                f"menambah stok produk prioritas, dan menjalankan promosi lokal pada kota tersebut. "
                f"Untuk kota dengan performa rendah, manajemen dapat mengevaluasi lokasi, promosi, dan pelayanan cabang."
            )


# ============================================================
# PAGE: ANALISIS WAKTU
# ============================================================

elif page == "Analisis Waktu":
    st.markdown('<div class="section-title">Analisis Tren Waktu</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    col1, col2 = st.columns(2)

    with col1:
        if "Tahun" in filtered_df.columns and "NomorBulan" in filtered_df.columns and "Bulan" in filtered_df.columns:
            tren_bulanan = (
                filtered_df
                .groupby(["Tahun", "NomorBulan", "Bulan"], as_index=False)
                .agg(
                    TotalPenjualan=("TotalPenjualan", "sum"),
                    Keuntungan=("Keuntungan", "sum"),
                    JumlahTransaksi=("FakturID", "count")
                )
                .sort_values(["Tahun", "NomorBulan"])
            )

            tren_bulanan["Periode"] = (
                tren_bulanan["Bulan"].astype(str) + " " + tren_bulanan["Tahun"].astype(int).astype(str)
            )

            fig = px.line(
                tren_bulanan,
                x="Periode",
                y="TotalPenjualan",
                markers=True,
                title="Tren Penjualan Bulanan"
            )
            fig.update_layout(xaxis_title="Periode", yaxis_title="Total Penjualan")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "Tahun" in filtered_df.columns and "NomorBulan" in filtered_df.columns and "Bulan" in filtered_df.columns:
            fig = px.line(
                tren_bulanan,
                x="Periode",
                y="Keuntungan",
                markers=True,
                title="Tren Keuntungan Bulanan"
            )
            fig.update_layout(xaxis_title="Periode", yaxis_title="Keuntungan")
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if "Kuartal" in filtered_df.columns:
            kuartal_sales = (
                filtered_df
                .groupby("Kuartal", as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("Kuartal")
            )

            fig = px.bar(
                kuartal_sales,
                x="Kuartal",
                y="TotalPenjualan",
                title="Total Penjualan per Kuartal",
                text_auto=".2s"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if "Hari" in filtered_df.columns:
            hari_sales = (
                filtered_df
                .groupby("Hari", as_index=False)
                .agg(JumlahTransaksi=("FakturID", "count"))
                .sort_values("JumlahTransaksi", ascending=False)
            )

            fig = px.bar(
                hari_sales,
                x="Hari",
                y="JumlahTransaksi",
                title="Jumlah Transaksi Berdasarkan Hari",
                text_auto=True
            )
            st.plotly_chart(fig, use_container_width=True)

    if "Tahun" in filtered_df.columns and "NomorBulan" in filtered_df.columns and "Bulan" in filtered_df.columns:
        if not tren_bulanan.empty:
            peak = tren_bulanan.sort_values("TotalPenjualan", ascending=False).iloc[0]
            insight_box(
                "Insight Waktu",
                f"Periode dengan total penjualan tertinggi adalah <b>{peak['Bulan']} {int(peak['Tahun'])}</b> "
                f"dengan total penjualan <b>{format_rupiah(peak['TotalPenjualan'])}</b>. "
                f"Manajemen dapat menggunakan pola ini untuk merencanakan stok, promosi, dan kebutuhan operasional "
                f"pada periode dengan permintaan tinggi."
            )


# ============================================================
# PAGE: ANALISIS PELANGGAN
# ============================================================

elif page == "Analisis Pelanggan":
    st.markdown('<div class="section-title">Analisis Pelanggan</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    gender_col = find_col(filtered_df, ["JenisKelamin", "Gender"])
    kelompok_usia_col = find_col(filtered_df, ["KelompokUsia", "Kelompok_Usia"])
    nama_pelanggan_col = find_col(filtered_df, ["NamaPelanggan", "Nama_Pelanggan"])
    kota_pelanggan_col = find_col(filtered_df, ["Kota_Pelanggan"])

    col1, col2 = st.columns(2)

    with col1:
        if kelompok_usia_col and "TotalPenjualan" in filtered_df.columns:
            usia_sales = (
                filtered_df
                .groupby(kelompok_usia_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
            )

            fig = px.bar(
                usia_sales,
                x=kelompok_usia_col,
                y="TotalPenjualan",
                title="Total Penjualan Berdasarkan Kelompok Usia",
                text_auto=".2s"
            )
            fig.update_layout(xaxis_title="Kelompok Usia", yaxis_title="Total Penjualan")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if gender_col and "TotalPenjualan" in filtered_df.columns:
            gender_sales = (
                filtered_df
                .groupby(gender_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
            )

            fig = px.pie(
                gender_sales,
                names=gender_col,
                values="TotalPenjualan",
                title="Proporsi Penjualan Berdasarkan Jenis Kelamin"
            )
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if nama_pelanggan_col and "TotalPenjualan" in filtered_df.columns:
            top_customer = (
                filtered_df
                .groupby(nama_pelanggan_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                top_customer,
                x="TotalPenjualan",
                y=nama_pelanggan_col,
                orientation="h",
                title="Top 10 Pelanggan Berdasarkan Nilai Transaksi",
                text_auto=".2s"
            )
            fig.update_layout(yaxis_title="Pelanggan", xaxis_title="Total Penjualan")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if kota_pelanggan_col and "TotalPenjualan" in filtered_df.columns:
            city_customer = (
                filtered_df
                .groupby(kota_pelanggan_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                city_customer,
                x=kota_pelanggan_col,
                y="TotalPenjualan",
                title="Top Kota Pelanggan Berdasarkan Penjualan",
                text_auto=".2s"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # --- TAMBAHAN INSIGHT 1: PREFERENSI LANSIA (BPJS) ---
    st.markdown('<div class="section-title">Fokus Segmen: Kategori Produk Paling Banyak Dibeli Lansia (>55 Tahun) Menggunakan BPJS</div>', unsafe_allow_html=True)
    
    usia_col = find_col(filtered_df, ["KelompokUsia", "Kelompok_Usia"])
    tipe_plg_col = find_col(filtered_df, ["TipePelanggan", "Tipe_Pelanggan"])
    kategori_col = find_col(filtered_df, ["KategoriProduk", "Kategori_Produk"])
    sales_col = find_col(filtered_df, ["TotalPenjualan", "Total_Penjualan"])

    if usia_col and tipe_plg_col and kategori_col and sales_col:
        filter_lansia_bpjs = filtered_df[
            (filtered_df[usia_col].astype(str).str.contains("55", na=False)) & 
            (filtered_df[tipe_plg_col].astype(str).str.contains("BPJS|Asuransi", na=False, case=False))
        ]
        
        if not filter_lansia_bpjs.empty:
            insight_demografi_produk = (
                filter_lansia_bpjs
                .groupby(kategori_col, as_index=False)
                .agg(Total_Penjualan=(sales_col, "sum"))
                .sort_values("Total_Penjualan", ascending=False)
            )
            
            fig_lansia = px.bar(
                insight_demografi_produk,
                x=kategori_col,
                y="Total_Penjualan",
                title="Produk Favorit Segmen Lansia (Asuransi/BPJS)",
                text_auto=".2s"
            )
            fig_lansia.update_layout(xaxis_title="Kategori Produk", yaxis_title="Total Penjualan")
            st.plotly_chart(fig_lansia, use_container_width=True)
        else:
            st.info("Tidak ada transaksi dari segmen lansia pengguna BPJS pada filter saat ini.")

    # 2. PROSES RANKING USIA KESELURUHAN
    if kelompok_usia_col and "TotalPenjualan" in filtered_df.columns:
        age_rank = (
            filtered_df
            .groupby(kelompok_usia_col)["TotalPenjualan"]
            .sum()
            .sort_values(ascending=False)
        )

        if not age_rank.empty:
            insight_box(
                "Insight Pelanggan",
                f"Segmen pelanggan dengan kontribusi penjualan tertinggi adalah kelompok usia "
                f"<b>{age_rank.index[0]}</b>. "
                f"Keputusan yang dapat diambil adalah membuat strategi promosi dan komunikasi pemasaran "
                f"yang lebih sesuai dengan karakteristik segmen tersebut, misalnya program loyalitas atau promosi produk relevan."
            )


# ============================================================
# PAGE: ANALISIS SUPPLIER
# ============================================================

elif page == "Analisis Supplier":
    st.markdown('<div class="section-title">Analisis Supplier</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    nama_supplier_col = find_col(filtered_df, ["NamaSupplier", "Nama_Supplier"])
    kota_supplier_col = find_col(filtered_df, ["KotaSupplier", "Kota_Supplier"])

    col1, col2 = st.columns(2)

    with col1:
        if nama_supplier_col and "TotalPenjualan" in filtered_df.columns:
            supplier_sales = (
                filtered_df
                .groupby(nama_supplier_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                supplier_sales,
                x="TotalPenjualan",
                y=nama_supplier_col,
                orientation="h",
                title="Top 10 Supplier Berdasarkan Penjualan",
                text_auto=".2s"
            )
            fig.update_layout(yaxis_title="Supplier", xaxis_title="Total Penjualan")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if nama_supplier_col and "Keuntungan" in filtered_df.columns:
            supplier_profit = (
                filtered_df
                .groupby(nama_supplier_col, as_index=False)
                .agg(Keuntungan=("Keuntungan", "sum"))
                .sort_values("Keuntungan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                supplier_profit,
                x="Keuntungan",
                y=nama_supplier_col,
                orientation="h",
                title="Top 10 Supplier Berdasarkan Keuntungan",
                text_auto=".2s"
            )
            fig.update_layout(yaxis_title="Supplier", xaxis_title="Keuntungan")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    if kota_supplier_col and "TotalPenjualan" in filtered_df.columns:
        supplier_city = (
            filtered_df
            .groupby(kota_supplier_col, as_index=False)
            .agg(TotalPenjualan=("TotalPenjualan", "sum"))
            .sort_values("TotalPenjualan", ascending=False)
            .head(10)
        )

        fig = px.bar(
            supplier_city,
            x=kota_supplier_col,
            y="TotalPenjualan",
            title="Kontribusi Penjualan Berdasarkan Kota Supplier",
            text_auto=".2s"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- TAMBAHAN INSIGHT 3: PERFORMA SUPPLIER Q3 TAHUN INI ---
    st.markdown('<div class="section-title">Evaluasi Rantai Pasok: Performa Margin Q3 Tahun 2026</div>', unsafe_allow_html=True)
    
    sup_col = find_col(filtered_df, ["NamaSupplier", "Nama_Supplier"])
    q_col = find_col(filtered_df, ["Kuartal", "kuartal"])
    year_col = find_col(filtered_df, ["Tahun", "tahun"])
    profit_col = find_col(filtered_df, ["Keuntungan", "keuntungan"])

    if sup_col and q_col and year_col and profit_col:
        tahun_terbaru = pd.to_numeric(filtered_df[year_col], errors='coerce').max()
        
        # Filter data hanya untuk Q3 pada tahun terbaru (tahun ini)
        filter_q3_tahun_ini = filtered_df[
            (filtered_df[q_col].astype(str).str.contains("Q3", case=False, na=False)) & 
            (pd.to_numeric(filtered_df[year_col], errors='coerce') == tahun_terbaru)
        ]
        
        if not filter_q3_tahun_ini.empty:
            insight_supplier_q3 = (
                filter_q3_tahun_ini
                .groupby(sup_col, as_index=False)
                .agg(Total_Keuntungan=(profit_col, "sum"))
                .sort_values("Total_Keuntungan", ascending=False)
                .head(5)
            )
            
            fig_q3 = px.bar(
                insight_supplier_q3,
                x="Total_Keuntungan",
                y=sup_col,
                orientation="h",
                title=f"Top 5 Supplier Penyumbang Margin Terbesar (Q3 {int(tahun_terbaru)})",
                text_auto="Rp .2s" 
            )
            fig_q3.update_layout(yaxis_title="Nama Supplier", xaxis_title="Total Keuntungan (Rp)")
            fig_q3.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig_q3, use_container_width=True)
        else:
            st.info(f"Tidak ada data transaksi untuk Q3 pada tahun {int(tahun_terbaru)}.")

    if nama_supplier_col and "TotalPenjualan" in filtered_df.columns:
        supplier_rank = (
            filtered_df
            .groupby(nama_supplier_col)["TotalPenjualan"]
            .sum()
            .sort_values(ascending=False)
        )

        if not supplier_rank.empty:
            insight_box(
                "Insight Supplier",
                f"Supplier dengan kontribusi penjualan tertinggi adalah <b>{supplier_rank.index[0]}</b> "
                f"dengan total penjualan <b>{format_rupiah(supplier_rank.iloc[0])}</b>. "
                f"Keputusan yang dapat diambil adalah memprioritaskan kerja sama dengan supplier berperforma tinggi, "
                f"mengevaluasi supplier dengan kontribusi rendah, dan mengatur strategi pengadaan produk."
            )


# ============================================================
# PAGE: ANALISIS KARYAWAN
# ============================================================

elif page == "Analisis Karyawan":
    st.markdown('<div class="section-title">Analisis Karyawan</div>', unsafe_allow_html=True)
    render_kpi(filtered_df)

    nama_karyawan_col = find_col(filtered_df, ["NamaKaryawan", "Nama_Karyawan"])
    jabatan_col = find_col(filtered_df, ["Jabatan"])
    departemen_col = find_col(filtered_df, ["Departemen"])

    col1, col2 = st.columns(2)

    with col1:
        if nama_karyawan_col and "TotalPenjualan" in filtered_df.columns:
            employee_sales = (
                filtered_df
                .groupby(nama_karyawan_col, as_index=False)
                .agg(
                    TotalPenjualan=("TotalPenjualan", "sum"),
                    JumlahTransaksi=("FakturID", "count")
                )
                .sort_values("TotalPenjualan", ascending=False)
                .head(10)
            )

            fig = px.bar(
                employee_sales,
                x="TotalPenjualan",
                y=nama_karyawan_col,
                orientation="h",
                title="Top 10 Karyawan Berdasarkan Penjualan",
                text_auto=".2s"
            )
            fig.update_layout(yaxis_title="Karyawan", xaxis_title="Total Penjualan")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if nama_karyawan_col and "FakturID" in filtered_df.columns:
            employee_transaction = (
                filtered_df
                .groupby(nama_karyawan_col, as_index=False)
                .agg(JumlahTransaksi=("FakturID", "count"))
                .sort_values("JumlahTransaksi", ascending=False)
                .head(10)
            )

            fig = px.bar(
                employee_transaction,
                x="JumlahTransaksi",
                y=nama_karyawan_col,
                orientation="h",
                title="Top 10 Karyawan Berdasarkan Jumlah Transaksi",
                text_auto=True
            )
            fig.update_layout(yaxis_title="Karyawan", xaxis_title="Jumlah Transaksi")
            fig.update_yaxes(categoryorder="total ascending")
            st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if jabatan_col and "TotalPenjualan" in filtered_df.columns:
            jabatan_sales = (
                filtered_df
                .groupby(jabatan_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
            )

            fig = px.bar(
                jabatan_sales,
                x=jabatan_col,
                y="TotalPenjualan",
                title="Total Penjualan Berdasarkan Jabatan",
                text_auto=".2s"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col4:
        if departemen_col and "TotalPenjualan" in filtered_df.columns:
            dept_sales = (
                filtered_df
                .groupby(departemen_col, as_index=False)
                .agg(TotalPenjualan=("TotalPenjualan", "sum"))
                .sort_values("TotalPenjualan", ascending=False)
            )

            fig = px.pie(
                dept_sales,
                names=departemen_col,
                values="TotalPenjualan",
                title="Proporsi Penjualan Berdasarkan Departemen"
            )
            st.plotly_chart(fig, use_container_width=True)

    if nama_karyawan_col and "TotalPenjualan" in filtered_df.columns:
        employee_rank = (
            filtered_df
            .groupby(nama_karyawan_col)["TotalPenjualan"]
            .sum()
            .sort_values(ascending=False)
        )

        if not employee_rank.empty:
            insight_box(
                "Insight Karyawan",
                f"Karyawan dengan kontribusi penjualan tertinggi adalah <b>{employee_rank.index[0]}</b>. "
                f"Keputusan yang dapat diambil adalah memberikan apresiasi atau reward, menjadikan karyawan tersebut sebagai benchmark layanan, "
                f"serta mengevaluasi kebutuhan pelatihan untuk karyawan lain."
            )

elif page == "Analisis OLAP":
    st.markdown('<div class="section-title">🗄️ Analisis Multidimensi (OLAP SQL CUBE)</div>', unsafe_allow_html=True)
    
    # Query SQL OLAP
    olap_sql_query = """
    SELECT 
        a."Wilayah",
        a."TipeCabang",
        w."Kuartal",
        SUM(f."TotalPenjualan") AS "Total_Penjualan",
        COUNT(f."FakturID") AS "Jumlah_Transaksi"
    FROM fact_penjualan f
    LEFT JOIN dim_apotek a ON f."ApotekID" = a."ApotekID"
    LEFT JOIN dim_waktu w ON f."WaktuID" = w."WaktuID"
    GROUP BY CUBE (a."Wilayah", a."TipeCabang", w."Kuartal")
    ORDER BY 
        a."Wilayah" NULLS LAST, 
        a."TipeCabang" NULLS LAST, 
        w."Kuartal" NULLS LAST;
    """

    try:
        # Menjalankan query
        df_olap_sql = pd.read_sql(olap_sql_query, con=engine)

        # Mengisi nilai NULL/None hasil operasi CUBE dengan label 'ALL'
        df_olap_sql["Wilayah"] = df_olap_sql["Wilayah"].fillna("ALL WILAYAH")
        df_olap_sql["TipeCabang"] = df_olap_sql["TipeCabang"].fillna("ALL TIPE")
        df_olap_sql["Kuartal"] = df_olap_sql["Kuartal"].fillna("ALL KUARTAL")

        # Menampilkan header/penjelasan
        st.write("Berikut adalah hasil agregasi kubus data (Data Cube) dari database:")

        # Tampilkan DataFrame dengan format yang rapi
        # Kita gunakan .style.format untuk mata uang agar lebih interaktif di Streamlit
        st.dataframe(
            df_olap_sql.style.format({
                "Total_Penjualan": "Rp {:,.0f}"
            }), 
            use_container_width=True
        )

        # Opsional: Tampilkan Query di expander agar tidak memakan tempat
        with st.expander("Lihat Query SQL"):
            st.code(olap_sql_query, language="sql")

    except Exception as e:
        st.error("Gagal menjalankan query OLAP. Pastikan tabel di database sudah terisi.")
        st.error(f"Error detail: {e}")

# ============================================================
# PAGE: DATA PREVIEW
# ============================================================

elif page == "Data Preview":
    st.markdown('<div class="section-title">Data Preview</div>', unsafe_allow_html=True)

    st.subheader("Fact Penjualan")
    st.dataframe(fact_penjualan.head(100), use_container_width=True)

    st.subheader("Dim Produk")
    st.dataframe(dim_produk.head(100), use_container_width=True)

    st.subheader("Dim Apotek")
    st.dataframe(dim_apotek.head(100), use_container_width=True)

    st.subheader("Dim Pelanggan")
    st.dataframe(dim_pelanggan.head(100), use_container_width=True)

    st.subheader("Dim Karyawan")
    st.dataframe(dim_karyawan.head(100), use_container_width=True)

    st.subheader("Dim Supplier")
    st.dataframe(dim_supplier.head(100), use_container_width=True)

    st.subheader("Dim Waktu")
    st.dataframe(dim_waktu.head(100), use_container_width=True)

    st.subheader("Data Analitik Hasil Join")
    st.dataframe(filtered_df.head(200), use_container_width=True)

    st.markdown("### Ringkasan Data")
    summary = pd.DataFrame({
        "Tabel": [
            "Fact Penjualan",
            "Dim Produk",
            "Dim Apotek",
            "Dim Pelanggan",
            "Dim Karyawan",
            "Dim Supplier",
            "Dim Waktu",
            "Analytical Data"
        ],
        "Jumlah Baris": [
            len(fact_penjualan),
            len(dim_produk),
            len(dim_apotek),
            len(dim_pelanggan),
            len(dim_karyawan),
            len(dim_supplier),
            len(dim_waktu),
            len(df)
        ],
        "Jumlah Kolom": [
            fact_penjualan.shape[1],
            dim_produk.shape[1],
            dim_apotek.shape[1],
            dim_pelanggan.shape[1],
            dim_karyawan.shape[1],
            dim_supplier.shape[1],
            dim_waktu.shape[1],
            df.shape[1]
        ]
    })

    st.dataframe(summary, use_container_width=True)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption(
    "Dashboard ini menggunakan dataset sintetis untuk simulasi Data Warehouse dan Business Intelligence "
    "pada jaringan apotek ritel internal Kimia Farma. Hasil analisis tidak merepresentasikan data asli perusahaan."
)