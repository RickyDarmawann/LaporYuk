"""Modul validasi: memeriksa kebenaran input sebelum data laporan disimpan.

Semua fungsi di modul ini akan melempar ValueError (lewat raise) atau
AssertionError (lewat assert) jika data tidak valid, dan tidak mengembalikan
apa-apa jika data sudah benar.
"""

from datetime import datetime

from laporyuk.models import STATUS_VALID

# Panjang minimal deskripsi agar laporan cukup jelas
MIN_DESKRIPSI = 10


def validasi_wajib_isi(**kwargs):
    """Memastikan semua field yang diberikan terisi (tidak kosong).

    Menggunakan **kwargs sehingga jumlah field yang dicek bisa bebas,
    contoh: validasi_wajib_isi(jenis="Lampu Mati", lokasi="")

    Args:
        **kwargs: Pasangan nama_field=nilai (nilai harus berupa string).

    Raises:
        AssertionError: Jika nilai bukan string.
        ValueError: Jika nilai kosong atau hanya berisi spasi.
    """
    for nama, nilai in kwargs.items():
        # assert: pengecekan tipe data (kesalahan programmer, bukan user)
        assert isinstance(nilai, str), f"Field '{nama}' harus berupa teks"
        if not nilai.strip():
            raise ValueError(f"Field '{nama}' wajib diisi")


def validasi_id(id_laporan):
    """Memeriksa format ID laporan, yaitu 'LP' diikuti angka (contoh LP001).

    Args:
        id_laporan (str): ID yang akan diperiksa.

    Raises:
        ValueError: Jika format ID tidak sesuai.
    """
    if not (id_laporan.startswith("LP") and id_laporan[2:].isdigit()):
        raise ValueError("ID harus berformat 'LP' diikuti angka, contoh: LP001")


def validasi_tanggal(tanggal):
    """Memeriksa format tanggal harus YYYY-MM-DD dan benar-benar ada.

    Args:
        tanggal (str): Tanggal yang akan diperiksa.

    Raises:
        ValueError: Jika format salah atau tanggal tidak ada di kalender.
    """
    try:
        datetime.strptime(tanggal, "%Y-%m-%d")
    except ValueError:
        # Diubah menjadi pesan yang lebih jelas untuk pengguna
        raise ValueError("Tanggal harus berformat YYYY-MM-DD, contoh: 2026-11-10")


def validasi_status(status):
    """Memeriksa status harus salah satu dari STATUS_VALID.

    Args:
        status (str): Status yang akan diperiksa.

    Raises:
        ValueError: Jika status tidak dikenal.
    """
    if status not in STATUS_VALID:
        raise ValueError(f"Status harus salah satu dari: {', '.join(STATUS_VALID)}")


def validasi_deskripsi(deskripsi):
    """Memeriksa deskripsi minimal MIN_DESKRIPSI karakter.

    Args:
        deskripsi (str): Deskripsi yang akan diperiksa.

    Raises:
        ValueError: Jika deskripsi terlalu pendek.
    """
    if len(deskripsi.strip()) < MIN_DESKRIPSI:
        raise ValueError(f"Deskripsi minimal {MIN_DESKRIPSI} karakter")


def validasi_laporan(id_laporan, jenis, lokasi, deskripsi, tanggal, status):
    """Menjalankan semua validasi untuk satu laporan sekaligus.

    Args:
        id_laporan (str): ID laporan.
        jenis (str): Jenis kerusakan.
        lokasi (str): Lokasi kerusakan.
        deskripsi (str): Deskripsi masalah.
        tanggal (str): Tanggal lapor (YYYY-MM-DD).
        status (str): Status laporan.

    Raises:
        ValueError: Jika salah satu field tidak valid.
        AssertionError: Jika ada field yang bukan string.
    """
    validasi_wajib_isi(
        id=id_laporan, jenis=jenis, lokasi=lokasi,
        deskripsi=deskripsi, tanggal=tanggal, status=status,
    )
    validasi_id(id_laporan)
    validasi_deskripsi(deskripsi)
    validasi_tanggal(tanggal)
    validasi_status(status)