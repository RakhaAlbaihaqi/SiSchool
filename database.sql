-- =============================================
-- DATABASE: db_nilai_siswa
-- Sistem Pengolahan Nilai Siswa Berbasis Web
-- =============================================

CREATE DATABASE IF NOT EXISTS db_nilai_siswa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_nilai_siswa;

-- Tabel User
CREATE TABLE IF NOT EXISTS tb_user (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('Admin', 'Guru', 'Siswa') NOT NULL
) ENGINE=InnoDB;

-- Tabel Siswa
CREATE TABLE IF NOT EXISTS tb_siswa (
    nis VARCHAR(20) PRIMARY KEY,
    id_user INT NOT NULL,
    nama_siswa VARCHAR(100) NOT NULL,
    kelas VARCHAR(20) NOT NULL,
    FOREIGN KEY (id_user) REFERENCES tb_user(id_user) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabel Guru
CREATE TABLE IF NOT EXISTS tb_guru (
    id_guru VARCHAR(20) PRIMARY KEY,
    id_user INT NOT NULL,
    nama_guru VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_user) REFERENCES tb_user(id_user) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tabel Mata Pelajaran
CREATE TABLE IF NOT EXISTS tb_mata_pelajaran (
    id_mapel VARCHAR(20) PRIMARY KEY,
    nama_mapel VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- Tabel Nilai
CREATE TABLE IF NOT EXISTS tb_nilai (
    id_nilai INT AUTO_INCREMENT PRIMARY KEY,
    nis VARCHAR(20) NOT NULL,
    id_mapel VARCHAR(20) NOT NULL,
    id_guru VARCHAR(20) NOT NULL,
    nilai_tugas FLOAT NOT NULL,
    nilai_uts FLOAT NOT NULL,
    nilai_uas FLOAT NOT NULL,
    nilai_akhir FLOAT NOT NULL,
    status_lulus VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (nis) REFERENCES tb_siswa(nis) ON DELETE CASCADE,
    FOREIGN KEY (id_mapel) REFERENCES tb_mata_pelajaran(id_mapel),
    FOREIGN KEY (id_guru) REFERENCES tb_guru(id_guru)
) ENGINE=InnoDB;

-- =============================================
-- DATA AWAL (SEED)
-- Password semua akun: admin123 / guru123 / siswa123
-- SHA256 dari "admin123" = a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3 (contoh)
-- Gunakan script Python untuk generate hash yang benar
-- =============================================

-- Admin (password: admin123)
INSERT INTO tb_user (username, password, role) VALUES
('admin', SHA2('admin123', 256), 'Admin');

-- Guru (password: guru123)
INSERT INTO tb_user (username, password, role) VALUES
('guru_budi', SHA2('guru123', 256), 'Guru'),
('guru_sari', SHA2('guru123', 256), 'Guru');

INSERT INTO tb_guru (id_guru, id_user, nama_guru) VALUES
('G001', 2, 'Budi Santoso'),
('G002', 3, 'Sari Dewi');

-- Siswa (password: siswa123)
INSERT INTO tb_user (username, password, role) VALUES
('siswa_andi', SHA2('siswa123', 256), 'Siswa'),
('siswa_bela', SHA2('siswa123', 256), 'Siswa'),
('siswa_ciko', SHA2('siswa123', 256), 'Siswa');

INSERT INTO tb_siswa (nis, id_user, nama_siswa, kelas) VALUES
('2024001', 4, 'Andi Prasetyo', 'X-A'),
('2024002', 5, 'Bela Anggraini', 'X-A'),
('2024003', 6, 'Ciko Ramadan', 'X-B');

-- Mata Pelajaran
INSERT INTO tb_mata_pelajaran VALUES
('MTK', 'Matematika'),
('IPA', 'Ilmu Pengetahuan Alam'),
('IPS', 'Ilmu Pengetahuan Sosial'),
('BIN', 'Bahasa Indonesia'),
('BING', 'Bahasa Inggris');

-- Contoh Nilai
INSERT INTO tb_nilai (nis, id_mapel, id_guru, nilai_tugas, nilai_uts, nilai_uas, nilai_akhir, status_lulus) VALUES
('2024001', 'MTK', 'G001', 80, 75, 85, 80.5, 'Lulus'),
('2024001', 'IPA', 'G002', 70, 65, 60, 64.5, 'Tidak Lulus'),
('2024002', 'MTK', 'G001', 90, 88, 92, 90.2, 'Lulus'),
('2024003', 'BIN', 'G002', 75, 80, 78, 77.7, 'Lulus');
