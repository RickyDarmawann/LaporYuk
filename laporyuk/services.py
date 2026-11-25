"""Modul services: logika pengolahan data laporan (cari, urut, filter, agregat).

Modul ini tidak bergantung pada UI sehingga mudah diuji dengan unittest.
"""

from datetime import date

from laporyuk import storage
from laporyuk.models import Laporan, STATUS_VALID
from laporyuk.validasi import validasi_id, validasi_laporan, validasi_status

# Kolom yang boleh dipakai untuk mencari dan memfilter
KOLOM_CARI = ("id", "jenis", "lokasi", "deskripsi", "tanggal", "status")

# Kamus "kolom -> fungsi pengambil nilai pengurutan" memakai lambda.
# - id: diambil angkanya agar LP2 < LP10 (bukan urut huruf)
# - teks: huruf kecil agar 'a' dan 'A' dianggap sama
# - tanggal: format YYYY-MM-DD sudah urut benar sebagai teks
# - status: urut sesuai alur kerja (Menunggu -> Diproses -> Selesai)
KUNCI_URUT = {
    "id": lambda lap: int(lap.id[2:]),
    "jenis": lambda lap: lap.jenis.lower(),
    "lokasi": lambda lap: lap.lokasi.lower(),
    "tanggal": lambda lap: lap.tanggal,
    "status": lambda lap: STATUS_VALID.index(lap.status),
}

def _periksa_kolom(nama_kolom):
    """Memastikan semua nama kolom dikenal (dipakai cari dan filter).

    Args:
        nama_kolom (iterable[str]): Nama-nama kolom yang diperiksa.

    Raises:
        ValueError: Jika ada nama kolom yang tidak ada di KOLOM_CARI.
    """
    for nama in nama_kolom:
        if nama not in KOLOM_CARI:
            raise ValueError(f"Kolom '{nama}' tidak dikenal")

def cari_linear(daftar, kata_kunci, *kolom):
    """Mencari laporan yang memuat kata kunci (Linear Search).

    Setiap laporan diperiksa satu per satu dari awal sampai akhir.
    Pencarian tidak membedakan huruf besar/kecil dan boleh sebagian kata.

    Args:
        daftar (list[Laporan]): Data yang dicari.
        kata_kunci (str): Kata yang dicari. Jika kosong, semua data cocok.
        *args kolom (str): Nama kolom yang diperiksa. Jika tidak diisi,
            semua kolom diperiksa.

    Returns:
        list[Laporan]: Laporan yang cocok (urutan asli dipertahankan).

    Raises:
        ValueError: Jika ada nama kolom yang tidak dikenal.
    """
    kata = kata_kunci.strip().lower()
    kolom = kolom or KOLOM_CARI  # *args: kosong berarti pakai semua kolom
    _periksa_kolom(kolom)

    hasil = []
    for laporan in daftar:
        for nama in kolom:
            if kata in str(getattr(laporan, nama)).lower():
                hasil.append(laporan)
                break  # sudah cocok, tidak perlu cek kolom lain
    return hasil


def urutkan_merge(daftar, kolom, menurun=False):
    """Mengurutkan laporan berdasarkan satu kolom (Merge Sort).

    Daftar dibelah dua berulang kali sampai tinggal satu elemen, lalu
    potongan yang sudah terurut digabung kembali. Kompleksitas O(n log n).
    Sifatnya stabil: elemen bernilai sama tetap dalam urutan aslinya.
    Data asli tidak diubah; fungsi mengembalikan list baru.

    Args:
        daftar (list[Laporan]): Data yang diurutkan.
        kolom (str): Salah satu kunci di KUNCI_URUT.
        menurun (bool): True untuk urutan besar ke kecil.

    Returns:
        list[Laporan]: Daftar baru yang sudah terurut.

    Raises:
        ValueError: Jika kolom tidak bisa dipakai untuk mengurutkan.
    """
    if kolom not in KUNCI_URUT:
        raise ValueError(f"Kolom '{kolom}' tidak bisa dipakai untuk mengurutkan")
    return _merge_sort(list(daftar), KUNCI_URUT[kolom], menurun)


def _merge_sort(data, kunci, menurun):
    """Bagian rekursif Merge Sort: belah dua, urutkan, lalu gabung.

    Args:
        data (list[Laporan]): Potongan data yang diurutkan.
        kunci (callable): Fungsi pengambil nilai pengurutan.
        menurun (bool): Arah urutan.

    Returns:
        list[Laporan]: Potongan data yang sudah terurut.
    """
    if len(data) <= 1:  # basis rekursi: 0 atau 1 elemen sudah terurut
        return data
    tengah = len(data) // 2
    kiri = _merge_sort(data[:tengah], kunci, menurun)
    kanan = _merge_sort(data[tengah:], kunci, menurun)
    return _gabung(kiri, kanan, kunci, menurun)


def _gabung(kiri, kanan, kunci, menurun):
    """Menggabungkan dua list terurut menjadi satu list terurut.

    Args:
        kiri (list[Laporan]): Potongan kiri (terurut).
        kanan (list[Laporan]): Potongan kanan (terurut).
        kunci (callable): Fungsi pengambil nilai pengurutan.
        menurun (bool): Arah urutan.

    Returns:
        list[Laporan]: Gabungan terurut.
    """
    hasil = []
    i = j = 0
    while i < len(kiri) and j < len(kanan):
        a, b = kunci(kiri[i]), kunci(kanan[j])
        # Tanda sama dengan (<=, >=) menjaga kestabilan: yang kiri didahulukan
        ambil_kiri = a >= b if menurun else a <= b
        if ambil_kiri:
            hasil.append(kiri[i])
            i += 1
        else:
            hasil.append(kanan[j])
            j += 1
    hasil.extend(kiri[i:])   # sisa salah satu potongan
    hasil.extend(kanan[j:])
    return hasil

def cari_biner_id(daftar_terurut, id_laporan):
    """Mencari laporan berdasarkan ID persis (Binary Search).

    Syarat: daftar harus sudah terurut menaik berdasarkan angka ID.
    Setiap langkah membuang separuh data, sehingga O(log n).

    Args:
        daftar_terurut (list[Laporan]): Data terurut menurut ID.
        id_laporan (str): ID yang dicari, contoh "LP005".

    Returns:
        Laporan | None: Laporan yang ditemukan, atau None.
    """
    try:
        validasi_id(id_laporan)
    except ValueError:
        return None  # format ID salah pasti tidak ada di data
    target = int(id_laporan[2:])

    kiri, kanan = 0, len(daftar_terurut) - 1
    while kiri <= kanan:
        tengah = (kiri + kanan) // 2
        nilai = int(daftar_terurut[tengah].id[2:])
        if nilai == target:
            return daftar_terurut[tengah]
        if nilai < target:
            kiri = tengah + 1    # buang separuh kiri
        else:
            kanan = tengah - 1   # buang separuh kanan
    return None

def filter_laporan(daftar, **kriteria):
    """Menyaring laporan dengan kriteria yang jumlahnya bebas.

    Contoh: filter_laporan(data, status="Menunggu", jenis="Lampu Mati")
    Semua kriteria harus terpenuhi (logika AND) dan dicocokkan persis.

    Args:
        daftar (list[Laporan]): Data yang disaring.
        **kriteria: Pasangan nama_kolom=nilai.

    Returns:
        list[Laporan]: Laporan yang memenuhi semua kriteria.

    Raises:
        ValueError: Jika ada nama kolom yang tidak dikenal.
    """
    _periksa_kolom(kriteria)  # iterasi dict menghasilkan nama kolomnya

    # lambda dipakai sebagai syarat untuk filter()
    return list(filter(
        lambda lap: all(getattr(lap, n) == v for n, v in kriteria.items()),
        daftar,
    ))


def hitung_status(daftar, *status):
    """Menghitung jumlah laporan per status.

    Args:
        daftar (list[Laporan]): Data yang dihitung.
        *args status (str): Status yang ingin dihitung. Jika kosong,
            semua status di STATUS_VALID dihitung.

    Returns:
        dict: Contoh {"Menunggu": 9, "Diproses": 7}.

    Raises:
        ValueError: Jika ada status yang tidak dikenal.
    """
    target = status or STATUS_VALID
    for s in target:
        validasi_status(s)
    return {s: len([lap for lap in daftar if lap.status == s]) for s in target}


def hitung_total(*kelompok):
    """Menjumlahkan banyak data dari beberapa daftar sekaligus.

    Args:
        *args kelompok (list): Sejumlah daftar laporan (jumlahnya bebas).

    Returns:
        int: Total seluruh elemen di semua daftar.
    """
    return sum(len(k) for k in kelompok)


class LaporanService:
    """Mengelola kumpulan laporan di memori sekaligus menyimpannya ke file.

    Class ini menjadi penghubung antara storage (file) dan UI.

    Attributes:
        path (str | Path): Lokasi file CSV.
        daftar (list[Laporan]): Laporan yang sedang dimuat.
        peringatan (list[str]): Masalah yang ditemukan saat memuat file.
    """

    def __init__(self, path=storage.DEFAULT_PATH):
        """Membuat service kosong; panggil muat() untuk mengisi data.

        Args:
            path (str | Path): Lokasi file CSV.
        """
        self.path = path
        self.daftar = []
        self.peringatan = []

    def muat(self):
        """Memuat data dari file CSV, lalu mengurutkannya menurut ID.

        Data harus terurut agar cari_id() bisa memakai Binary Search.
        """
        daftar, self.peringatan = storage.muat_laporan(self.path)
        self.daftar = urutkan_merge(daftar, "id")

    def buat_id_baru(self):
        """Membuat ID berikutnya, contoh LP021 jika terbesar saat ini LP020.

        Returns:
            str: ID baru yang belum dipakai.
        """
        if not self.daftar:
            return "LP001"
        terbesar = max(int(lap.id[2:]) for lap in self.daftar)
        return f"LP{terbesar + 1:03d}"

    def cari_id(self, id_laporan):
        """Mencari satu laporan berdasarkan ID persis (Binary Search).

        ID baru selalu lebih besar dari yang ada, jadi daftar tetap terurut
        setelah tambah(), ubah_status(), dan hapus().

        Returns:
            Laporan | None: Laporan yang ditemukan, atau None.
        """
        return cari_biner_id(self.daftar, id_laporan) 

    def tambah(self, jenis, lokasi, deskripsi, tanggal=None):
        """Membuat laporan baru (status awal Menunggu) dan menyimpannya.

        Args:
            jenis (str): Jenis kerusakan.
            lokasi (str): Lokasi kerusakan.
            deskripsi (str): Deskripsi masalah.
            tanggal (str | None): YYYY-MM-DD, default hari ini.

        Returns:
            Laporan: Laporan yang baru dibuat.

        Raises:
            ValueError: Jika data tidak lolos validasi.
        """
        tanggal = tanggal or date.today().isoformat()
        id_baru = self.buat_id_baru()
        validasi_laporan(id_baru, jenis, lokasi, deskripsi, tanggal, "Menunggu")

        laporan = Laporan(id_baru, jenis, lokasi, deskripsi, tanggal, "Menunggu")
        self.daftar.append(laporan)
        storage.tambah_laporan(laporan, self.path)
        return laporan

    def ubah_status(self, id_laporan, status_baru):
        """Mengubah status laporan (dipakai petugas) lalu menyimpan ke file.

        Raises:
            ValueError: Jika ID tidak ada atau status tidak valid.
        """
        validasi_status(status_baru)
        laporan = self.cari_id(id_laporan)
        if laporan is None:
            raise ValueError(f"Laporan {id_laporan} tidak ditemukan")
        laporan.status = status_baru
        storage.simpan_laporan(self.daftar, self.path)

    def hapus(self, id_laporan):
        """Menghapus laporan berdasarkan ID lalu menyimpan ke file.

        Raises:
            ValueError: Jika ID tidak ada.
        """
        laporan = self.cari_id(id_laporan)
        if laporan is None:
            raise ValueError(f"Laporan {id_laporan} tidak ditemukan")
        self.daftar.remove(laporan)
        storage.simpan_laporan(self.daftar, self.path)

    def cari(self, kata_kunci, *kolom):
        """Pembungkus cari_linear() untuk data milik service ini."""
        return cari_linear(self.daftar, kata_kunci, *kolom)

    def urutkan(self, kolom, menurun=False):
        """Pembungkus urutkan_merge() untuk data milik service ini."""
        return urutkan_merge(self.daftar, kolom, menurun)

    def filter(self, **kriteria):
        """Pembungkus filter_laporan() untuk data milik service ini."""
        return filter_laporan(self.daftar, **kriteria)

    def ringkasan(self, *status):
        """Pembungkus hitung_status() untuk data milik service ini."""
        return hitung_status(self.daftar, *status)