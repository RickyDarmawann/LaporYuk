"""Membandingkan algoritma lama (Bubble Sort, Linear Search) dengan baru.

Jalankan: python benchmark.py
Fungsi lama disalin ke sini hanya sebagai pembanding.
"""

import random
import time

from laporyuk.models import Laporan
from laporyuk.services import KUNCI_URUT, cari_biner_id, urutkan_merge


def urutkan_bubble_lama(daftar, kolom, menurun=False):
    """Versi lama (Progress 4): Bubble Sort O(n^2)."""
    kunci = KUNCI_URUT[kolom]
    hasil = list(daftar)
    n = len(hasil)
    for i in range(n - 1):
        ada_tukar = False
        for j in range(n - 1 - i):
            kiri, kanan = kunci(hasil[j]), kunci(hasil[j + 1])
            if (kiri < kanan) if menurun else (kiri > kanan):
                hasil[j], hasil[j + 1] = hasil[j + 1], hasil[j]
                ada_tukar = True
        if not ada_tukar:
            break
    return hasil


def cari_linear_id_lama(daftar, id_laporan):
    """Versi lama: cari ID dengan memeriksa satu per satu O(n)."""
    for laporan in daftar:
        if laporan.id == id_laporan:
            return laporan
    return None


def buat_data(n):
    """Membuat n laporan acak (tanggal acak) untuk bahan uji kecepatan."""
    return [
        Laporan(f"LP{i:05d}", "Lampu Mati", "Gerbang", "Deskripsi uji laporan",
                f"2026-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}")
        for i in range(1, n + 1)
    ]


def ukur(fungsi, *args):
    """Mengukur waktu jalan fungsi (detik) beserta hasilnya."""
    mulai = time.perf_counter()
    hasil = fungsi(*args)
    return time.perf_counter() - mulai, hasil


def main():
    """Mencetak perbandingan waktu pengurutan dan pencarian ID."""
    print("== Pengurutan berdasarkan tanggal ==")
    print(f"{'Jumlah':>8} {'Bubble (s)':>12} {'Merge (s)':>12}")
    for n in (500, 1000, 2000):
        data = buat_data(n)
        t_bubble, h_bubble = ukur(urutkan_bubble_lama, data, "tanggal")
        t_merge, h_merge = ukur(urutkan_merge, data, "tanggal")
        # Keduanya stabil, jadi hasilnya harus identik
        assert [x.id for x in h_bubble] == [x.id for x in h_merge]
        print(f"{n:>8} {t_bubble:>12.4f} {t_merge:>12.4f}")

    print("\n== Cari ID terakhir, 1000 kali, 20000 data ==")
    data = buat_data(20000)
    target = data[-1].id
    t_linear, _ = ukur(lambda: [cari_linear_id_lama(data, target) for _ in range(1000)])
    t_biner, _ = ukur(lambda: [cari_biner_id(data, target) for _ in range(1000)])
    print(f"Linear search : {t_linear:.4f} detik")
    print(f"Binary search : {t_biner:.4f} detik")


if __name__ == "__main__":
    main()