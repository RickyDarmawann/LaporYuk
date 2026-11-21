"""Modul storage: membaca dan menulis data laporan ke file CSV.

Semua operasi file memakai context manager `with open()` sehingga file
otomatis ditutup, walaupun terjadi error di tengah proses.
"""

import csv
from pathlib import Path

from laporyuk.models import Laporan
from laporyuk.validasi import validasi_laporan

# Nama kolom CSV, urutannya harus sama dengan header file
KOLOM = ["id", "jenis", "lokasi", "deskripsi", "tanggal", "status"]

# Lokasi default file data: <root proyek>/data/laporan.csv
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "laporan.csv"


def muat_laporan(path=DEFAULT_PATH):
    """Membaca file CSV dan mengubahnya menjadi daftar objek Laporan.

    Fungsi ini tidak akan membuat aplikasi crash. Jika file hilang atau
    ada baris rusak, masalahnya dicatat di daftar peringatan.

    Args:
        path (str | Path): Lokasi file CSV.

    Returns:
        tuple: (daftar_laporan, peringatan)
            daftar_laporan (list[Laporan]): Laporan yang valid.
            peringatan (list[str]): Pesan masalah yang ditemukan saat membaca.
    """
    daftar = []
    peringatan = []

    try:
        # Mode 'r': baca saja. newline="" wajib untuk modul csv.
        with open(path, "r", newline="", encoding="utf-8") as f:
            pembaca = csv.DictReader(f)
            # start=2 karena baris 1 adalah header
            for no_baris, baris in enumerate(pembaca, start=2):
                try:
                    validasi_laporan(
                        baris["id"], baris["jenis"], baris["lokasi"],
                        baris["deskripsi"], baris["tanggal"], baris["status"],
                    )
                    daftar.append(Laporan.from_dict(baris))
                except KeyError as e:
                    peringatan.append(f"Baris {no_baris} dilewati: kolom {e} tidak ada")
                except (ValueError, AssertionError) as e:
                    peringatan.append(f"Baris {no_baris} dilewati: {e}")
    except FileNotFoundError:
        peringatan.append(f"File '{path}' tidak ditemukan, memakai data kosong")
    except (csv.Error, UnicodeDecodeError) as e:
        # UnicodeDecodeError adalah turunan ValueError (file bukan teks valid)
        peringatan.append(f"File '{path}' rusak dan tidak bisa dibaca: {e}")

    return daftar, peringatan


def simpan_laporan(daftar, path=DEFAULT_PATH):
    """Menyimpan seluruh daftar laporan ke CSV (menimpa isi file lama).

    Args:
        daftar (list[Laporan]): Laporan yang akan disimpan.
        path (str | Path): Lokasi file CSV.
    """
    # Mode 'w': tulis ulang dari awal (file dibuat jika belum ada)
    with open(path, "w", newline="", encoding="utf-8") as f:
        penulis = csv.DictWriter(f, fieldnames=KOLOM)
        penulis.writeheader()
        for laporan in daftar:
            penulis.writerow(laporan.to_dict())


def tambah_laporan(laporan, path=DEFAULT_PATH):
    """Menambahkan satu laporan di akhir file tanpa menimpa data lama.

    Jika file belum ada, file dibuat baru lengkap dengan header.

    Args:
        laporan (Laporan): Laporan yang akan ditambahkan.
        path (str | Path): Lokasi file CSV.
    """
    if not Path(path).exists():
        simpan_laporan([laporan], path)
        return

    # Mode 'a': tambah di akhir file
    with open(path, "a", newline="", encoding="utf-8") as f:
        penulis = csv.DictWriter(f, fieldnames=KOLOM)
        penulis.writerow(laporan.to_dict())


def buat_file_baru(path=DEFAULT_PATH):
    """Membuat file CSV kosong (hanya header) jika belum ada.

    Returns:
        bool: True jika file berhasil dibuat, False jika sudah ada.
    """
    try:
        # Mode 'x': buat file baru, gagal jika file sudah ada
        with open(path, "x", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=KOLOM).writeheader()
        return True
    except FileExistsError:
        return False