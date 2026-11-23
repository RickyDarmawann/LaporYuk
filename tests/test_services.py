"""Unit test untuk logika LaporYuk (tanpa UI).

Yang diuji: pencarian, pengurutan, filter, agregat, validasi, service,
dan pembacaan file. Jalankan dari folder root proyek:
    python -m unittest discover -v
"""

import os
import tempfile
import unittest

from laporyuk.models import Laporan
from laporyuk.services import (
    LaporanService, cari_linear, filter_laporan,
    hitung_status, hitung_total, urutkan_bubble,
)
from laporyuk.storage import muat_laporan
from laporyuk.validasi import validasi_laporan


def buat_data_uji():
    """Membuat 4 laporan kecil untuk bahan pengujian.

    Returns:
        list[Laporan]: Data uji (urutan awal: LP001, LP002, LP010, LP003).
    """
    return [
        Laporan("LP001", "Lampu Mati", "Parkiran Barat",
                "Lampu jalan mati total", "2026-11-03", "Menunggu"),
        Laporan("LP002", "Jalan Berlubang", "Gerbang Utama",
                "Lubang besar dekat portal", "2026-11-01", "Selesai"),
        Laporan("LP010", "Keran Bocor", "Kantin Pusat",
                "Keran wastafel bocor terus", "2026-11-05", "Diproses"),
        Laporan("LP003", "Lampu Mati", "Kantin Pusat",
                "Lampu kantin padam sejak kemarin", "2026-11-02", "Menunggu"),
    ]


def ambil_id(daftar):
    """Mengambil daftar ID saja dari list Laporan (agar assert ringkas)."""
    return [lap.id for lap in daftar]


class TestPencarian(unittest.TestCase):
    """Menguji fungsi cari_linear."""

    def setUp(self):
        """Dijalankan sebelum setiap tes: siapkan data baru."""
        self.data = buat_data_uji()

    def test_cari_semua_kolom(self):
        """Tanpa *kolom, semua kolom diperiksa dan urutan asli terjaga."""
        hasil = cari_linear(self.data, "lampu")
        self.assertEqual(ambil_id(hasil), ["LP001", "LP003"])

    def test_cari_kolom_tertentu_tidak_peduli_huruf(self):
        """Pencarian di satu kolom dan tidak membedakan huruf besar/kecil."""
        hasil = cari_linear(self.data, "KANTIN", "lokasi")
        self.assertEqual(ambil_id(hasil), ["LP010", "LP003"])

    def test_cari_tidak_ketemu_dan_kolom_salah(self):
        """Kata tidak ada -> list kosong; kolom tidak dikenal -> ValueError."""
        self.assertEqual(cari_linear(self.data, "xyz"), [])
        with self.assertRaises(ValueError):
            cari_linear(self.data, "lampu", "warna")


class TestPengurutan(unittest.TestCase):
    """Menguji fungsi urutkan_bubble."""

    def setUp(self):
        """Siapkan data uji baru."""
        self.data = buat_data_uji()

    def test_urut_tanggal_naik_dan_turun(self):
        """Tanggal terlama dulu (naik), lalu terbaru dulu (turun)."""
        naik = urutkan_bubble(self.data, "tanggal")
        turun = urutkan_bubble(self.data, "tanggal", menurun=True)
        self.assertEqual(ambil_id(naik), ["LP002", "LP003", "LP001", "LP010"])
        self.assertEqual(ambil_id(turun), ["LP010", "LP001", "LP003", "LP002"])

    def test_urut_status_sesuai_alur_kerja(self):
        """Status urut Menunggu -> Diproses -> Selesai, bukan urut abjad."""
        hasil = urutkan_bubble(self.data, "status")
        self.assertEqual(ambil_id(hasil), ["LP001", "LP003", "LP010", "LP002"])

    def test_urut_tidak_mengubah_data_asli(self):
        """Fungsi mengembalikan salinan; list asli tetap sama."""
        sebelum = ambil_id(self.data)
        urutkan_bubble(self.data, "tanggal")
        self.assertEqual(ambil_id(self.data), sebelum)

    def test_urut_kolom_salah(self):
        """Kolom yang tidak bisa diurutkan memicu ValueError."""
        with self.assertRaises(ValueError):
            urutkan_bubble(self.data, "deskripsi")


class TestOlahData(unittest.TestCase):
    """Menguji filter (**kwargs), agregat (*args), dan validasi."""

    def setUp(self):
        """Siapkan data uji baru."""
        self.data = buat_data_uji()

    def test_filter_satu_dan_banyak_kriteria(self):
        """Kriteria bebas: makin banyak kriteria, hasil makin sempit (AND)."""
        satu = filter_laporan(self.data, status="Menunggu")
        dua = filter_laporan(self.data, status="Menunggu", lokasi="Kantin Pusat")
        self.assertEqual(ambil_id(satu), ["LP001", "LP003"])
        self.assertEqual(ambil_id(dua), ["LP003"])

    def test_filter_kolom_salah(self):
        """Nama kolom tidak dikenal memicu ValueError."""
        with self.assertRaises(ValueError):
            filter_laporan(self.data, warna="merah")

    def test_hitung_status_dan_total(self):
        """*status memilih status yang dihitung; *kelompok menjumlah banyak list."""
        self.assertEqual(
            hitung_status(self.data),
            {"Menunggu": 2, "Diproses": 1, "Selesai": 1},
        )
        self.assertEqual(hitung_status(self.data, "Selesai"), {"Selesai": 1})
        self.assertEqual(hitung_total(self.data, self.data[:2]), 6)

    def test_validasi_laporan(self):
        """Data valid lolos; lokasi kosong dan status salah ditolak."""
        validasi_laporan("LP001", "Lampu Mati", "Parkiran",
                         "Lampu jalan mati total", "2026-11-10", "Menunggu")
        with self.assertRaises(ValueError):
            validasi_laporan("LP001", "Lampu Mati", "",
                             "Lampu jalan mati total", "2026-11-10", "Menunggu")
        with self.assertRaises(ValueError):
            validasi_laporan("LP001", "Lampu Mati", "Parkiran",
                             "Lampu jalan mati total", "2026-11-10", "Batal")


class TestServiceDanStorage(unittest.TestCase):
    """Menguji LaporanService dan pembacaan file memakai folder sementara."""

    def setUp(self):
        """Buat folder sementara; otomatis dihapus setelah tes selesai."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "uji.csv")

    def muat_ulang(self):
        """Membuat service baru yang membaca file (membuktikan data tersimpan)."""
        service = LaporanService(self.path)
        service.muat()
        return service

    def test_tambah_membuat_id_berurutan_dan_tersimpan(self):
        """ID naik otomatis dan data bertahan setelah dimuat ulang dari file."""
        service = LaporanService(self.path)
        satu = service.tambah("Lampu Mati", "Gerbang", "Lampu gerbang padam", "2026-11-22")
        dua = service.tambah("AC Rusak", "Ruang B1", "AC tidak dingin sama sekali", "2026-11-22")
        self.assertEqual((satu.id, dua.id), ("LP001", "LP002"))
        self.assertEqual(len(self.muat_ulang().daftar), 2)

    def test_tambah_data_tidak_valid_ditolak(self):
        """Lokasi kosong ditolak dan tidak ada yang masuk ke daftar."""
        service = LaporanService(self.path)
        with self.assertRaises(ValueError):
            service.tambah("Lampu Mati", "", "Lampu gerbang padam", "2026-11-22")
        self.assertEqual(service.daftar, [])

    def test_ubah_status_dan_hapus(self):
        """Perubahan status dan penghapusan tersimpan ke file."""
        service = LaporanService(self.path)
        service.tambah("Lampu Mati", "Gerbang", "Lampu gerbang padam", "2026-11-22")
        service.tambah("AC Rusak", "Ruang B1", "AC tidak dingin sama sekali", "2026-11-22")

        service.ubah_status("LP001", "Selesai")
        self.assertEqual(self.muat_ulang().cari_id("LP001").status, "Selesai")

        service.hapus("LP001")
        self.assertEqual(ambil_id(self.muat_ulang().daftar), ["LP002"])

        with self.assertRaises(ValueError):
            service.hapus("LP999")

    def test_muat_file_hilang_tidak_crash(self):
        """File tidak ada -> data kosong + 1 peringatan, bukan exception."""
        data, peringatan = muat_laporan(self.path)
        self.assertEqual(data, [])
        self.assertEqual(len(peringatan), 1)

    def test_muat_baris_rusak_dilewati(self):
        """Baris dengan status salah dilewati, baris valid tetap dimuat."""
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("id,jenis,lokasi,deskripsi,tanggal,status\n")
            f.write("LP001,Lampu Mati,Parkiran,Lampu jalan mati total,2026-11-10,Menunggu\n")
            f.write("LP002,Lampu Mati,Parkiran,Lampu jalan mati total,2026-11-10,Batal\n")
        data, peringatan = muat_laporan(self.path)
        self.assertEqual(ambil_id(data), ["LP001"])
        self.assertEqual(len(peringatan), 1)


if __name__ == "__main__":
    unittest.main()