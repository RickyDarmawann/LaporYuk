"""Modul models: berisi class yang merepresentasikan data utama aplikasi."""

# Daftar status yang diizinkan untuk sebuah laporan
STATUS_VALID = ("Menunggu", "Diproses", "Selesai")


class Laporan:
    """Merepresentasikan satu laporan kerusakan fasilitas kampus.

    Attributes:
        id (str): Kode unik laporan, contoh "LP001".
        jenis (str): Jenis kerusakan, contoh "Lampu Mati".
        lokasi (str): Lokasi kerusakan di area kampus.
        deskripsi (str): Penjelasan singkat masalah.
        tanggal (str): Tanggal lapor, format "YYYY-MM-DD".
        status (str): Salah satu dari STATUS_VALID.
    """

    def __init__(self, id, jenis, lokasi, deskripsi, tanggal, status="Menunggu"):
        """Membuat objek Laporan baru.

        Args:
            id (str): Kode unik laporan.
            jenis (str): Jenis kerusakan.
            lokasi (str): Lokasi kerusakan.
            deskripsi (str): Deskripsi masalah.
            tanggal (str): Tanggal lapor (YYYY-MM-DD).
            status (str): Status awal, default "Menunggu".
        """
        self.id = id
        self.jenis = jenis
        self.lokasi = lokasi
        self.deskripsi = deskripsi
        self.tanggal = tanggal
        self.status = status

    def to_dict(self):
        """Mengubah objek menjadi dictionary (berguna untuk simpan ke CSV).

        Returns:
            dict: Data laporan dengan kunci sesuai nama kolom.
        """
        return {
            "id": self.id,
            "jenis": self.jenis,
            "lokasi": self.lokasi,
            "deskripsi": self.deskripsi,
            "tanggal": self.tanggal,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Membuat objek Laporan dari dictionary (misal hasil baca CSV).

        Args:
            data (dict): Dictionary dengan kunci id, jenis, lokasi,
                deskripsi, tanggal, status.

        Returns:
            Laporan: Objek laporan baru.
        """
        return cls(
            data["id"],
            data["jenis"],
            data["lokasi"],
            data["deskripsi"],
            data["tanggal"],
            data["status"],
        )

    def __str__(self):
        """Representasi teks laporan agar mudah dicetak/di-debug."""
        return f"[{self.id}] {self.jenis} - {self.lokasi} ({self.status})"