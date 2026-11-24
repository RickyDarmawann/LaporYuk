"""Titik masuk aplikasi LaporYuk. Jalankan dengan: python main.py"""

from laporyuk.services import LaporanService
from laporyuk.ui import AplikasiLaporYuk


def main():
    """Memuat data dari CSV lalu menjalankan jendela utama aplikasi."""
    service = LaporanService()
    service.muat()
    aplikasi = AplikasiLaporYuk(service)
    aplikasi.mainloop()


if __name__ == "__main__":
    main()