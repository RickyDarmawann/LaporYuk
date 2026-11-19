"""Titik masuk aplikasi LaporYuk (sementara untuk uji Progress 1)."""

from laporyuk.models import Laporan


def main():
    """Mencoba membuat satu objek Laporan dan mencetaknya."""
    contoh = Laporan(
        "LP001", "Jalan Berlubang", "Gerbang Utama",
        "Lubang besar dekat portal", "2026-11-10",
    )
    print(contoh)
    print(contoh.to_dict())


if __name__ == "__main__":
    main()