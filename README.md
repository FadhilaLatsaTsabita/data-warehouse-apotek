# Dashboard Data Warehouse - PT Kimia Farma Tbk

Proyek ini merupakan implementasi *Data Warehouse* menggunakan skema **Star Schema** untuk mensimulasikan data transaksi pada jaringan apotek PT Kimia Farma Apotek. Proyek ini mencakup alur lengkap mulai dari ETL hingga visualisasi di dashboard.

## Arsitektur Proyek
1. **Proses ETL (`.ipynb`):** Notebook ini berfungsi untuk melakukan ekstraksi data mentah, melakukan transformasi (seperti *cleaning*, *handling missing values*, dan *joining* tabel), serta memuatnya (*loading*) ke dalam basis data.
2. **Data Warehouse:** Data yang telah diproses disimpan dengan skema **Star Schema** untuk optimalisasi *query* OLAP.
3. **Visualisasi (`app.py`):** Dashboard **Streamlit** untuk menampilkan *insight* bisnis dan analisis multidimensi.

## Fitur Utama
* **Pipeline ETL Otomatis:** Pembersihan dan penggabungan data dari berbagai sumber (Produk, Apotek, Pelanggan, dll).
* **Analisis Multidimensi (OLAP):** Menggunakan fungsi SQL `CUBE` untuk agregasi data tingkat tinggi (Wilayah, Tipe Cabang, Kuartal).
* **Star Schema Integration:** Mengelola enam tabel dimensi dan satu tabel fakta (`Fact_Penjualan`).

## Struktur Proyek
- `datware_kimiafarma.ipynb`: Notebook berisi kode proses **ETL** (Extract, Transform, Load).
- `app.py`: File utama aplikasi dashboard **Streamlit**.
- `csv/`: Folder berisi dataset sintetis.
- `requirements.txt`: Daftar pustaka yang dibutuhkan.

## Cara Menjalankan
1. **Proses Data (ETL):** Jalankan notebook `datware_kimiafarma.ipynb` terlebih dahulu untuk menyiapkan data di database.
2. **Dashboard:**
   - Install library: `pip install -r requirements.txt`
   - Jalankan dashboard: `streamlit run app.py`

## Teknologi yang Digunakan
- **ETL:** Python, Pandas, Jupyter Notebook
- **Database:** PostgreSQL (via SQLAlchemy)
- **Frontend:** Streamlit
- **Visualization:** Plotly