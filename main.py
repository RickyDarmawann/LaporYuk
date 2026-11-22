"""Titik masuk aplikasi LaporYuk (sementara untuk uji Progress 4)."""

import os
import shutil
import tempfile

from laporyuk.services import (
    LaporanService, cari_linear, filter_laporan,
    hitung_status, hitung_total, urutkan_bubble,
)
from laporyuk.storage import muat_laporan


def tampil(daftar, maks=3):
    """Mencetak maksimal `maks` laporan pertama dari daftar."""
    for laporan in daftar[:maks]:
        print(laporan)


def main():
    """Menguji searching, sorting, filter, agregat, dan LaporanService."""
    data, _ = muat_laporan()

    print("== 1. Searching ==")
    print(f"Cari 'lampu' (semua kolom): {len(cari_linear(data, 'lampu'))} hasil")
    print(f"Cari 'kantin' (kolom lokasi): "
          f"{len(cari_linear(data, 'kantin', 'lokasi'))} hasil")
    print(f"Cari 'xyz': {len(cari_linear(data, 'xyz'))} hasil")

    print("\n== 2. Sorting ==")
    print("Tanggal terbaru dulu:")
    tampil(urutkan_bubble(data, "tanggal", menurun=True))
    print("Jenis A-Z:")
    tampil(urutkan_bubble(data, "jenis"))

    print("\n== 3. Filter (**kwargs) ==")
    menunggu = filter_laporan(data, status="Menunggu")
    print(f"Status Menunggu: {len(menunggu)} laporan")
    print(f"Menunggu + Lampu Mati: "
          f"{len(filter_laporan(data, status='Menunggu', jenis='Lampu Mati'))} laporan")
    try:
        filter_laporan(data, warna="merah")
    except ValueError as e:
        print(f"ERROR: {e}")

    print("\n== 4. Agregat (*args) ==")
    print(hitung_status(data))
    print(hitung_status(data, "Selesai"))
    diproses = filter_laporan(data, status="Diproses")
    selesai = filter_laporan(data, status="Selesai")
    print(f"Total gabungan: {hitung_total(menunggu, diproses, selesai)}")

    print("\n== 5. Class LaporanService ==")
    with tempfile.TemporaryDirectory() as folder:
        # Pakai salinan CSV agar data asli tidak berubah saat uji
        salinan = os.path.join(folder, "salinan.csv")
        shutil.copy("data/laporan.csv", salinan)

        service = LaporanService(salinan)
        service.muat()
        print(f"Setelah muat: {len(service.daftar)}")

        baru = service.tambah("Lampu Mati", "Gerbang Utama",
                              "Lampu gerbang padam total", "2026-11-22")
        print(f"Laporan baru: {baru}")
        print(f"Setelah tambah: {len(service.daftar)}")

        service.ubah_status("LP021", "Diproses")
        print(f"Status LP021 sekarang: {service.cari_id('LP021').status}")

        service.hapus("LP001")
        print(f"Setelah hapus LP001: {len(service.daftar)}")

        try:
            service.ubah_status("LP999", "Selesai")
        except ValueError as e:
            print(f"ERROR: {e}")

        ulang = LaporanService(salinan)
        ulang.muat()
        print(f"Muat ulang dari file: {len(ulang.daftar)}")


if __name__ == "__main__":
    main()