"""Titik masuk aplikasi LaporYuk (sementara untuk uji Progress 2)."""

from laporyuk.validasi import validasi_laporan


def coba(keterangan, **data):
    """Menjalankan validasi dan mencetak hasilnya (valid atau pesan error)."""
    try:
        validasi_laporan(**data)
        print(f"[OK]    {keterangan}")
    except (ValueError, AssertionError) as e:
        print(f"[ERROR] {keterangan} -> {e}")


def main():
    """Mencoba beberapa kasus data valid dan tidak valid."""
    dasar = dict(
        id_laporan="LP001", jenis="Lampu Mati", lokasi="Parkiran Barat",
        deskripsi="Lampu jalan mati sejak seminggu", tanggal="2026-11-10",
        status="Menunggu",
    )

    coba("Data valid", **dasar)
    coba("Lokasi kosong", **{**dasar, "lokasi": ""})
    coba("ID salah format", **{**dasar, "id_laporan": "ABC1"})
    coba("Deskripsi terlalu pendek", **{**dasar, "deskripsi": "rusak"})
    coba("Tanggal salah format", **{**dasar, "tanggal": "10-11-2026"})
    coba("Status tidak dikenal", **{**dasar, "status": "Batal"})
    coba("Jenis bukan teks", **{**dasar, "jenis": 123})


if __name__ == "__main__":
    main()