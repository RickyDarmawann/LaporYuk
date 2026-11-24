"""Modul ui: tampilan GUI LaporYuk memakai Tkinter.

Berisi dua class:
- FormLaporan: jendela kecil untuk menambah laporan baru.
- AplikasiLaporYuk: jendela utama (menu, pencarian, tabel, aksi, ringkasan).

Semua logika data ada di services.py; modul ini hanya mengatur tampilan.
"""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from laporyuk.models import STATUS_VALID
from laporyuk.services import (
    KOLOM_CARI, KUNCI_URUT, cari_linear, filter_laporan, urutkan_bubble,
)

# Pilihan jenis kerusakan yang umum (pengguna tetap boleh mengetik sendiri)
JENIS_UMUM = (
    "Jalan Berlubang", "Lampu Mati", "Tempat Sampah Rusak", "Keran Bocor",
    "AC Rusak", "Kursi Rusak", "Pintu Rusak", "Atap Bocor", "Wi-Fi Mati",
)

# Judul dan lebar tiap kolom tabel
JUDUL_KOLOM = {
    "id": "ID", "jenis": "Jenis", "lokasi": "Lokasi",
    "deskripsi": "Deskripsi", "tanggal": "Tanggal", "status": "Status",
}
LEBAR_KOLOM = {
    "id": 70, "jenis": 150, "lokasi": 170,
    "deskripsi": 320, "tanggal": 90, "status": 90,
}

# Warna latar baris tabel dan warna batang grafik per status
WARNA_BARIS = {"Menunggu": "#FFF3CD", "Diproses": "#CCE5FF", "Selesai": "#D4EDDA"}
WARNA_BATANG = {"Menunggu": "#F0AD4E", "Diproses": "#337AB7", "Selesai": "#5CB85C"}


class FormLaporan(tk.Toplevel):
    """Jendela form untuk menambah laporan kerusakan baru.

    Attributes:
        service (LaporanService): Penyimpan dan pengelola data.
        setelah_simpan (callable): Fungsi yang dipanggil setelah berhasil
            menyimpan (dipakai untuk menyegarkan tabel).
    """

    def __init__(self, induk, service, setelah_simpan):
        """Membangun form dan menampilkannya sebagai jendela modal.

        Args:
            induk (tk.Tk): Jendela utama.
            service (LaporanService): Service tempat laporan disimpan.
            setelah_simpan (callable): Callback setelah simpan berhasil.
        """
        super().__init__(induk)
        self.title("Tambah Laporan Baru")
        self.resizable(False, False)
        self.service = service
        self.setelah_simpan = setelah_simpan

        isi = ttk.Frame(self, padding=15)
        isi.grid()

        ttk.Label(isi, text="Jenis kerusakan").grid(row=0, column=0, sticky="w", pady=4)
        self.var_jenis = tk.StringVar()
        ttk.Combobox(isi, textvariable=self.var_jenis, values=JENIS_UMUM,
                     width=38).grid(row=0, column=1, pady=4)

        ttk.Label(isi, text="Lokasi").grid(row=1, column=0, sticky="w", pady=4)
        self.var_lokasi = tk.StringVar()
        ttk.Entry(isi, textvariable=self.var_lokasi, width=40).grid(row=1, column=1, pady=4)

        ttk.Label(isi, text="Deskripsi").grid(row=2, column=0, sticky="nw", pady=4)
        self.teks_deskripsi = tk.Text(isi, width=40, height=5)
        self.teks_deskripsi.grid(row=2, column=1, pady=4)

        ttk.Label(isi, text="Tanggal (YYYY-MM-DD)").grid(row=3, column=0, sticky="w", pady=4)
        self.var_tanggal = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(isi, textvariable=self.var_tanggal, width=40).grid(row=3, column=1, pady=4)

        tombol = ttk.Frame(isi)
        tombol.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(tombol, text="Batal", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(tombol, text="Simpan", command=self.simpan).pack(side="right")

        # Modal: pengguna harus menutup form dulu sebelum memakai jendela utama
        self.transient(induk)
        self.grab_set()

    def simpan(self):
        """Mengambil isian form, menyimpan lewat service, dan menutup form.

        Jika validasi gagal, pesan error ditampilkan dan form tetap terbuka
        agar pengguna bisa memperbaiki isiannya.
        """
        try:
            baru = self.service.tambah(
                self.var_jenis.get().strip(),
                self.var_lokasi.get().strip(),
                self.teks_deskripsi.get("1.0", "end").strip(),
                self.var_tanggal.get().strip(),
            )
        except (ValueError, AssertionError, OSError) as e:
            messagebox.showerror("Gagal menyimpan", str(e), parent=self)
            return
        messagebox.showinfo("Berhasil", f"Laporan {baru.id} berhasil disimpan.",
                            parent=self)
        self.setelah_simpan()
        self.destroy()


class AplikasiLaporYuk(tk.Tk):
    """Jendela utama aplikasi LaporYuk.

    Attributes:
        service (LaporanService): Sumber data dan logika.
        kolom_urut (str): Kolom yang sedang dipakai untuk mengurutkan.
        menurun (bool): True jika urutan sedang besar ke kecil.
    """

    def __init__(self, service):
        """Membangun seluruh komponen tampilan lalu mengisi tabel.

        Args:
            service (LaporanService): Service yang sudah memuat data.
        """
        super().__init__()
        self.service = service
        self.kolom_urut = "id"
        self.menurun = False

        self.title("LaporYuk - Pelaporan Kerusakan Fasilitas Kampus")
        self.geometry("1020x640")
        self.minsize(880, 560)

        # Variabel yang terhubung ke widget input
        self.var_cari = tk.StringVar()
        self.var_kolom_cari = tk.StringVar(value="Semua")
        self.var_filter = tk.StringVar(value="Semua")
        self.var_status_baru = tk.StringVar(value=STATUS_VALID[1])

        # Urutan pack penting: bagian bawah dibuat sebelum tabel
        self._buat_menu()
        self._buat_pencarian()
        self._buat_statusbar()
        self._buat_aksi()
        self._buat_tabel()

        # Pencarian "langsung": tabel disegarkan setiap kali teks berubah
        self.var_cari.trace_add("write", lambda *_: self.segarkan())

        self.segarkan()
        if self.service.peringatan:
            self.after(200, self._tampilkan_peringatan)

    # ---------- Pembuatan komponen ----------

    def _buat_menu(self):
        """Membuat menu bar: File, Laporan, Bantuan."""
        bar = tk.Menu(self)

        menu_file = tk.Menu(bar, tearoff=False)
        menu_file.add_command(label="Muat ulang data", command=self.muat_ulang)
        menu_file.add_separator()
        menu_file.add_command(label="Keluar", command=self.destroy)
        bar.add_cascade(label="File", menu=menu_file)

        menu_laporan = tk.Menu(bar, tearoff=False)
        menu_laporan.add_command(label="Tambah laporan", command=self.tambah)
        menu_laporan.add_command(label="Ubah status terpilih", command=self.ubah_status)
        menu_laporan.add_command(label="Hapus terpilih", command=self.hapus)
        bar.add_cascade(label="Laporan", menu=menu_laporan)

        menu_bantuan = tk.Menu(bar, tearoff=False)
        menu_bantuan.add_command(label="Tentang", command=self.tentang)
        bar.add_cascade(label="Bantuan", menu=menu_bantuan)

        self.config(menu=bar)

    def _buat_pencarian(self):
        """Membuat baris atas: kotak cari, pilihan kolom, dan filter status."""
        bingkai = ttk.Frame(self, padding=(10, 10, 10, 5))
        bingkai.pack(side="top", fill="x")

        ttk.Label(bingkai, text="Cari:").pack(side="left")
        ttk.Entry(bingkai, textvariable=self.var_cari, width=28).pack(side="left", padx=5)

        ttk.Label(bingkai, text="di kolom:").pack(side="left", padx=(10, 0))
        kolom = ttk.Combobox(bingkai, textvariable=self.var_kolom_cari,
                             values=("Semua",) + KOLOM_CARI, state="readonly", width=11)
        kolom.pack(side="left", padx=5)
        kolom.bind("<<ComboboxSelected>>", lambda e: self.segarkan())

        ttk.Label(bingkai, text="Status:").pack(side="left", padx=(15, 0))
        filter_status = ttk.Combobox(bingkai, textvariable=self.var_filter,
                                     values=("Semua",) + STATUS_VALID,
                                     state="readonly", width=11)
        filter_status.pack(side="left", padx=5)
        filter_status.bind("<<ComboboxSelected>>", lambda e: self.segarkan())

    def _buat_statusbar(self):
        """Membuat baris paling bawah yang menampilkan jumlah data."""
        self.label_status = ttk.Label(self, anchor="w", padding=(10, 3))
        self.label_status.pack(side="bottom", fill="x")

    def _buat_aksi(self):
        """Membuat panel aksi (tombol) dan panel grafik ringkasan status."""
        bingkai = ttk.Frame(self, padding=(10, 5))
        bingkai.pack(side="bottom", fill="x")

        aksi = ttk.LabelFrame(bingkai, text="Aksi", padding=8)
        aksi.pack(side="left", fill="y")
        ttk.Button(aksi, text="+ Tambah Laporan", command=self.tambah).grid(
            row=0, column=0, padx=3, pady=3)
        ttk.Button(aksi, text="Hapus Terpilih", command=self.hapus).grid(
            row=0, column=1, padx=3, pady=3)
        ttk.Button(aksi, text="Muat Ulang", command=self.muat_ulang).grid(
            row=0, column=2, padx=3, pady=3)

        ttk.Label(aksi, text="Ubah status terpilih ke:").grid(
            row=1, column=0, padx=3, pady=3, sticky="w")
        ttk.Combobox(aksi, textvariable=self.var_status_baru, values=STATUS_VALID,
                     state="readonly", width=10).grid(row=1, column=1, padx=3, pady=3)
        ttk.Button(aksi, text="Terapkan", command=self.ubah_status).grid(
            row=1, column=2, padx=3, pady=3)

        ringkasan = ttk.LabelFrame(bingkai, text="Ringkasan Status", padding=8)
        ringkasan.pack(side="right")
        self.canvas = tk.Canvas(ringkasan, width=320, height=100,
                                bg="white", highlightthickness=0)
        self.canvas.pack()

    def _buat_tabel(self):
        """Membuat tabel Treeview lengkap dengan scrollbar dan warna status."""
        bingkai = ttk.Frame(self, padding=(10, 5))
        bingkai.pack(side="top", fill="both", expand=True)

        self.tree = ttk.Treeview(bingkai, columns=KOLOM_CARI, show="headings",
                                 selectmode="browse")
        for kolom in KOLOM_CARI:
            # **opsi: hanya kolom yang bisa diurutkan yang diberi perintah klik
            opsi = {}
            if kolom in KUNCI_URUT:
                opsi["command"] = lambda k=kolom: self.urut_kolom(k)
            self.tree.heading(kolom, text=JUDUL_KOLOM[kolom], **opsi)
            self.tree.column(kolom, width=LEBAR_KOLOM[kolom],
                             stretch=(kolom == "deskripsi"))

        for status, warna in WARNA_BARIS.items():
            self.tree.tag_configure(status, background=warna, foreground="black")

        gulir = ttk.Scrollbar(bingkai, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=gulir.set)
        self.tree.pack(side="left", fill="both", expand=True)
        gulir.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.lihat_detail())

    # ---------- Pengolahan tampilan ----------

    def _ambil_tampilan(self):
        """Menghitung data yang tampil: filter status -> cari -> urutkan.

        Returns:
            list[Laporan]: Data yang akan ditampilkan di tabel.
        """
        data = self.service.daftar

        if self.var_filter.get() != "Semua":
            data = filter_laporan(data, status=self.var_filter.get())

        kolom = self.var_kolom_cari.get()
        if kolom == "Semua":
            data = cari_linear(data, self.var_cari.get())
        else:
            data = cari_linear(data, self.var_cari.get(), kolom)

        return urutkan_bubble(data, self.kolom_urut, self.menurun)

    def segarkan(self):
        """Mengisi ulang tabel, judul kolom, status bar, dan grafik."""
        tampil = self._ambil_tampilan()

        self.tree.delete(*self.tree.get_children())
        for lap in tampil:
            self.tree.insert(
                "", "end", iid=lap.id, tags=(lap.status,),
                values=(lap.id, lap.jenis, lap.lokasi,
                        lap.deskripsi, lap.tanggal, lap.status),
            )

        self._perbarui_judul_kolom()
        self.label_status.config(
            text=f"Menampilkan {len(tampil)} dari {len(self.service.daftar)} laporan")
        self._gambar_ringkasan()

    def _perbarui_judul_kolom(self):
        """Menambah tanda panah ▲/▼ pada judul kolom yang sedang diurutkan."""
        for kolom in KOLOM_CARI:
            judul = JUDUL_KOLOM[kolom]
            if kolom == self.kolom_urut:
                judul += " ▼" if self.menurun else " ▲"
            self.tree.heading(kolom, text=judul)

    def _gambar_ringkasan(self):
        """Menggambar grafik batang jumlah laporan per status di Canvas."""
        c = self.canvas
        c.delete("all")
        ringkas = self.service.ringkasan()
        maks = max(ringkas.values()) or 1  # hindari pembagian dengan nol

        for i, (status, jumlah) in enumerate(ringkas.items()):
            y = 10 + i * 30
            panjang = 180 * jumlah / maks
            c.create_text(5, y + 10, text=status, anchor="w", fill="black")
            c.create_rectangle(75, y, 75 + panjang, y + 20,
                               fill=WARNA_BATANG[status], outline="")
            c.create_text(75 + panjang + 6, y + 10, text=str(jumlah),
                          anchor="w", fill="black")

    def urut_kolom(self, kolom):
        """Dipanggil saat judul kolom diklik: ganti kolom atau balik arah."""
        if kolom == self.kolom_urut:
            self.menurun = not self.menurun
        else:
            self.kolom_urut, self.menurun = kolom, False
        self.segarkan()

    # ---------- Aksi pengguna ----------

    def _id_terpilih(self):
        """Mengambil ID baris yang dipilih.

        Returns:
            str | None: ID laporan, atau None (disertai pesan) jika belum memilih.
        """
        pilihan = self.tree.selection()
        if not pilihan:
            messagebox.showinfo("Pilih laporan", "Klik salah satu baris laporan dulu.")
            return None
        return pilihan[0]

    def tambah(self):
        """Membuka form tambah laporan."""
        FormLaporan(self, self.service, self.segarkan)

    def ubah_status(self):
        """Mengubah status laporan terpilih sesuai pilihan di combobox."""
        id_laporan = self._id_terpilih()
        if id_laporan is None:
            return
        try:
            self.service.ubah_status(id_laporan, self.var_status_baru.get())
        except (ValueError, OSError) as e:
            messagebox.showerror("Gagal mengubah status", str(e))
            return
        self.segarkan()

    def hapus(self):
        """Menghapus laporan terpilih setelah pengguna mengonfirmasi."""
        id_laporan = self._id_terpilih()
        if id_laporan is None:
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus laporan {id_laporan}?"):
            return
        try:
            self.service.hapus(id_laporan)
        except (ValueError, OSError) as e:
            messagebox.showerror("Gagal menghapus", str(e))
            return
        self.segarkan()

    def lihat_detail(self):
        """Menampilkan detail lengkap laporan yang di-double-click."""
        pilihan = self.tree.selection()
        if not pilihan:
            return
        lap = self.service.cari_id(pilihan[0])
        if lap is not None:
            messagebox.showinfo(
                f"Detail {lap.id}",
                f"Jenis     : {lap.jenis}\nLokasi    : {lap.lokasi}\n"
                f"Tanggal   : {lap.tanggal}\nStatus    : {lap.status}\n\n"
                f"Deskripsi :\n{lap.deskripsi}",
            )

    def muat_ulang(self):
        """Membaca ulang file CSV dan menyegarkan tampilan."""
        self.service.muat()
        self.segarkan()
        if self.service.peringatan:
            self._tampilkan_peringatan()

    def _tampilkan_peringatan(self):
        """Menampilkan masalah yang ditemukan saat membaca file (maks 10)."""
        pesan = "\n".join(self.service.peringatan[:10])
        messagebox.showwarning("Peringatan saat memuat data", pesan)

    def tentang(self):
        """Menampilkan informasi singkat tentang aplikasi."""
        messagebox.showinfo(
            "Tentang LaporYuk",
            "LaporYuk\nSistem pelaporan kerusakan fasilitas kampus.\n"
            "UAS Pemrograman Terstruktur (Python).",
        )