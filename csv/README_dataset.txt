Dataset sintetis untuk project Data Warehouse jaringan apotek ritel internal Kimia Farma.
Data ini bukan data asli PT Kimia Farma dan hanya digunakan untuk simulasi akademik.

File dan jumlah baris data:
- produk.csv: 120 baris data
- apotek.csv: 100 baris data
- pelanggan.csv: 150 baris data
- karyawan.csv: 120 baris data
- supplier.csv: 100 baris data
- penjualan.csv: 1000 baris data

Relasi utama:
- penjualan.ProdukID -> produk.ProdukID
- penjualan.ApotekID -> apotek.ApotekID
- penjualan.PelangganID -> pelanggan.PelangganID
- penjualan.KaryawanID -> karyawan.KaryawanID
- penjualan.SupplierID -> supplier.SupplierID
- produk.SupplierID -> supplier.SupplierID
- karyawan.ApotekID -> apotek.ApotekID
