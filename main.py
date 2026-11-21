"""Titik masuk aplikasi LaporYuk (sementara untuk uji Progress 3)."""

import os
import tempfile

from laporyuk.models import Laporan
from laporyuk.storage import muat_laporan, simpan_laporan, tambah_laporan


def main():
    """Menguji muat data awal, file hilang, file rusak, simpan, dan tambah."""
    print("== 1. Muat data awal ==")
    data, peringatan = muat_laporan()
    print(f"Jumlah laporan: {len(data)}")
    for laporan in data[:3]:
        print(laporan)
    print(f"Jumlah peringatan: {len(peringatan)}")

    print("\n== 2. File tidak ditemukan ==")
    data, peringatan = muat_laporan("data/tidak_ada.csv")
    print(f"Jumlah laporan: {len(data)}")
    print(peringatan[0])

    # Folder sementara agar file uji tidak mengotori data asli
    with tempfile.TemporaryDirectory() as folder:
        print("\n== 3. File berisi baris rusak ==")
        path_rusak = os.path.join(folder, "rusak.csv")
        with open(path_rusak, "w", encoding="utf-8") as f:
            f.write("id,jenis,lokasi,deskripsi,tanggal,status\n")
            f.write("LP001,Lampu Mati,Parkiran,Lampu jalan mati total,2026-11-10,Menunggu\n")
            f.write("LP002,Lampu Mati,Parkiran,Lampu jalan mati total,2026-11-10,Batal\n")
            f.write("LP003,Lampu Mati,Parkiran,Lampu jalan mati total,10-11-2026,Menunggu\n")
        data, peringatan = muat_laporan(path_rusak)
        print(f"Berhasil dimuat: {len(data)}")
        for p in peringatan:
            print(p)

        print("\n== 4. Simpan dan tambah ==")
        path_baru = os.path.join(folder, "baru.csv")
        satu = Laporan("LP001", "Keran Bocor", "Toilet A",
                       "Keran bocor terus menerus", "2026-11-20")
        dua = Laporan("LP002", "AC Rusak", "Ruang B1",
                      "AC tidak dingin sama sekali", "2026-11-21")
        simpan_laporan([satu], path_baru)
        tambah_laporan(dua, path_baru)
        data, _ = muat_laporan(path_baru)
        print(f"Setelah simpan + tambah: {len(data)} laporan")
        for laporan in data:
            print(laporan)


if __name__ == "__main__":
    main()