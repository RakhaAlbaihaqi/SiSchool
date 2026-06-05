# SiSchool — Sistem Pengolahan Nilai Siswa Berbasis Web
**Python (Flask) + MySQL**  
Dibuat untuk keperluan LSP Skema Programmer

---

## Cara Menjalankan

### 1. Prasyarat
- Python 3.8+
- MySQL Server (XAMPP / WAMP / MySQL standalone)
- pip

### 2. Install Dependensi
```bash
pip install -r requirements.txt
```

### 3. Setup Database
Buka MySQL (phpMyAdmin atau terminal), lalu jalankan:
```sql
source database.sql
```
Atau salin-tempel isi file `database.sql` ke phpMyAdmin Query tab.

### 4. Konfigurasi Koneksi Database
Buka `app.py`, ubah bagian ini sesuai MySQL Anda:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',       # Username MySQL Anda
    'password': '',       # Password MySQL Anda
    'database': 'db_nilai_siswa'
}
```

### 5. Jalankan Aplikasi
```bash
python app.py
```
Akses di browser: **http://localhost:5000**

---

## Akun Default

| Role  | Username    | Password  |
|-------|-------------|-----------|
| Admin | admin       | admin123  |
| Guru  | guru_budi   | guru123   |
| Guru  | guru_sari   | guru123   |
| Siswa | siswa_andi  | siswa123  |
| Siswa | siswa_bela  | siswa123  |
| Siswa | siswa_ciko  | siswa123  |

---

## Fitur Sistem

### Admin
- Dashboard statistik (total siswa, guru, nilai, kelulusan)
- CRUD Data Siswa (beserta akun login)
- CRUD Data Guru (beserta akun login)
- Kelola Mata Pelajaran
- Lihat semua data nilai
- Laporan dengan filter kelas & mata pelajaran

### Guru
- Input nilai siswa (Tugas, UTS, UAS)
- Preview nilai akhir otomatis sebelum disimpan
- Rekap nilai yang sudah diinput

### Siswa
- Lihat nilai pribadi (read-only)
- Melihat status kelulusan per mata pelajaran

---

## Rumus Nilai Akhir
```
Nilai Akhir = (30% × Tugas) + (30% × UTS) + (40% × UAS)
Status      = "Lulus" jika Nilai Akhir ≥ 70, "Tidak Lulus" jika < 70
```

---

## Struktur File
```
nilai_siswa/
├── app.py              ← Aplikasi utama Flask
├── database.sql        ← Schema + data awal MySQL
├── requirements.txt    ← Dependensi Python
├── README.md           ← Panduan ini
└── templates/
    ├── base.html       ← Layout utama (sidebar, navbar)
    ├── login.html      ← Halaman login
    ├── dashboard.html  ← Dashboard (berbeda per role)
    ├── laporan.html    ← Halaman laporan
    ├── siswa/
    │   ├── list.html   ← Daftar siswa
    │   └── form.html   ← Form tambah/ubah siswa
    ├── guru/
    │   ├── list.html
    │   └── form.html
    ├── nilai/
    │   ├── input.html  ← Form input nilai dengan preview
    │   └── list.html
    └── mapel/
        ├── list.html
        └── form.html
```
