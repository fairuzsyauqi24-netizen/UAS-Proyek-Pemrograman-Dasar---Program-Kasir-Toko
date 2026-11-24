import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

# ======================= FILE PENYIMPANAN =======================
FOLDER = os.path.dirname(os.path.abspath(__file__))
FILE_DATA = os.path.join(FOLDER, "data_barang.json")
FILE_RIWAYAT = os.path.join(FOLDER, "riwayat_transaksi.txt")

# ======================= STRUKTUR DATA =======================
# Dictionary: kode -> {nama, harga, stok}  (data awal jika belum ada file)
data_barang = {
    "B001": {"nama": "Beras 5kg", "harga": 65000, "stok": 20},
    "B002": {"nama": "Minyak Goreng 1L", "harga": 18000, "stok": 30},
    "B003": {"nama": "Gula 1kg", "harga": 16000, "stok": 25},
}

# List berisi tuple: (kode, nama, harga, jumlah)
keranjang = []


# ======================= FUNGSI (LOGIKA) =======================
def simpan_data():
    """Simpan data_barang ke file JSON."""
    try:
        with open(FILE_DATA, "w", encoding="utf-8") as f:
            json.dump(data_barang, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"[PERINGATAN] Gagal menyimpan data: {e}")


def muat_data():
    """Muat data_barang dari file JSON jika ada; jika gagal, pakai data awal."""
    if not os.path.exists(FILE_DATA):
        return
    try:
        with open(FILE_DATA, "r", encoding="utf-8") as f:
            isi = json.load(f)
        data_barang.clear()
        data_barang.update(isi)
        print(f"[INFO] Data dimuat dari {FILE_DATA}")
    except (OSError, json.JSONDecodeError):
        print("[PERINGATAN] File data rusak, memakai data awal.")


def ke_angka(teks, nama_field):
    """Ubah teks ke bilangan bulat; error jika bukan angka atau negatif."""
    try:
        angka = int(teks)
    except ValueError:
        raise ValueError(f"{nama_field} harus berupa angka bulat.")
    if angka < 0:
        raise ValueError(f"{nama_field} tidak boleh negatif.")
    return angka


def tambah_barang(kode, nama, harga, stok):
    kode = kode.strip().upper()
    nama = nama.strip()
    if kode == "" or nama == "":
        raise ValueError("Kode dan nama barang tidak boleh kosong.")
    if kode in data_barang:
        raise ValueError(f"Kode {kode} sudah ada. Gunakan tombol Ubah.")
    data_barang[kode] = {
        "nama": nama,
        "harga": ke_angka(harga, "Harga"),
        "stok": ke_angka(stok, "Stok"),
    }


def ubah_barang(kode, nama, harga, stok):
    kode = kode.strip().upper()
    if kode not in data_barang:
        raise ValueError(f"Kode {kode} tidak ditemukan.")
    if nama.strip() == "":
        raise ValueError("Nama barang tidak boleh kosong.")
    data_barang[kode]["nama"] = nama.strip()
    data_barang[kode]["harga"] = ke_angka(harga, "Harga")
    data_barang[kode]["stok"] = ke_angka(stok, "Stok")


def hapus_barang(kode):
    kode = kode.strip().upper()
    if kode not in data_barang:
        raise ValueError(f"Kode {kode} tidak ditemukan.")
    del data_barang[kode]


def tambah_ke_keranjang(kode, jumlah):
    if kode not in data_barang:
        raise ValueError("Pilih barang terlebih dahulu.")
    jumlah = ke_angka(jumlah, "Jumlah")
    if jumlah == 0:
        raise ValueError("Jumlah harus lebih dari 0.")

    # hitung jumlah barang yang sudah ada di keranjang
    sudah_ada = 0
    for item in keranjang:
        if item[0] == kode:
            sudah_ada += item[3]

    if sudah_ada + jumlah > data_barang[kode]["stok"]:
        raise ValueError(
            f"Stok tidak cukup. Sisa stok: {data_barang[kode]['stok']}, "
            f"di keranjang: {sudah_ada}."
        )
    barang = data_barang[kode]
    keranjang.append((kode, barang["nama"], barang["harga"], jumlah))


def hitung_total():
    """Return (subtotal, diskon, total). Diskon ditentukan dengan pengkondisian."""
    subtotal = 0
    for _, _, harga, jumlah in keranjang:
        subtotal += harga * jumlah

    if subtotal >= 200000:
        persen = 10
    elif subtotal >= 100000:
        persen = 5
    else:
        persen = 0

    diskon = subtotal * persen // 100
    return subtotal, diskon, subtotal - diskon


def rupiah(angka):
    return "Rp " + f"{angka:,}".replace(",", ".")


def catat_transaksi(subtotal, diskon, total):
    """Cetak struk ke terminal dan tambahkan ke file riwayat_transaksi.txt."""
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    baris = [f"[{waktu}] TRANSAKSI"]
    for _, nama, harga, jumlah in keranjang:
        baris.append(f"  {nama} x{jumlah} = {rupiah(harga * jumlah)}")
    baris.append(f"  Subtotal: {rupiah(subtotal)}")
    baris.append(f"  Diskon  : {rupiah(diskon)}")
    baris.append(f"  TOTAL   : {rupiah(total)}")
    teks = "\n".join(baris)

    print(teks)  # tampil di terminal VS Code
    print("-" * 40)
    try:
        with open(FILE_RIWAYAT, "a", encoding="utf-8") as f:
            f.write(teks + "\n\n")
    except OSError as e:
        print(f"[PERINGATAN] Gagal menulis riwayat: {e}")


def proses_bayar():
    """Catat transaksi, kurangi stok sesuai keranjang, simpan, lalu kosongkan keranjang.
    Return total yang dibayar."""
    if len(keranjang) == 0:
        raise ValueError("Keranjang masih kosong.")
    subtotal, diskon, total = hitung_total()
    catat_transaksi(subtotal, diskon, total)
    for kode, _, _, jumlah in keranjang:
        data_barang[kode]["stok"] -= jumlah
    keranjang.clear()
    simpan_data()
    return total


# ======================= GUI =======================
class AplikasiKasir(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Kasir & Stok Toko")
        self.geometry("720x520")

        tab = ttk.Notebook(self)
        tab.pack(fill="both", expand=True, padx=8, pady=8)
        self.tab_stok = ttk.Frame(tab)
        self.tab_kasir = ttk.Frame(tab)
        tab.add(self.tab_stok, text="Stok Barang")
        tab.add(self.tab_kasir, text="Kasir")

        self.buat_tab_stok()
        self.buat_tab_kasir()
        self.refresh_semua()

    # ---------- Tab Stok ----------
    def buat_tab_stok(self):
        form = ttk.LabelFrame(self.tab_stok, text="Data Barang")
        form.pack(fill="x", padx=8, pady=8)

        self.var_kode = tk.StringVar()
        self.var_nama = tk.StringVar()
        self.var_harga = tk.StringVar()
        self.var_stok = tk.StringVar()

        label_var = [("Kode", self.var_kode), ("Nama", self.var_nama),
                     ("Harga", self.var_harga), ("Stok", self.var_stok)]
        for i, (teks, var) in enumerate(label_var):
            ttk.Label(form, text=teks).grid(row=i // 2, column=(i % 2) * 2, padx=6, pady=4, sticky="e")
            ttk.Entry(form, textvariable=var, width=22).grid(row=i // 2, column=(i % 2) * 2 + 1, padx=6, pady=4)

        tombol = ttk.Frame(form)
        tombol.grid(row=2, column=0, columnspan=4, pady=6)
        ttk.Button(tombol, text="Tambah", command=self.aksi_tambah).pack(side="left", padx=4)
        ttk.Button(tombol, text="Ubah", command=self.aksi_ubah).pack(side="left", padx=4)
        ttk.Button(tombol, text="Hapus", command=self.aksi_hapus).pack(side="left", padx=4)
        ttk.Button(tombol, text="Bersihkan", command=self.bersihkan_form).pack(side="left", padx=4)

        self.tabel_stok = ttk.Treeview(self.tab_stok, columns=("kode", "nama", "harga", "stok"),
                                       show="headings", height=12)
        for kol, judul, lebar in [("kode", "Kode", 80), ("nama", "Nama Barang", 280),
                                  ("harga", "Harga", 140), ("stok", "Stok", 80)]:
            self.tabel_stok.heading(kol, text=judul)
            self.tabel_stok.column(kol, width=lebar)
        self.tabel_stok.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.tabel_stok.bind("<<TreeviewSelect>>", self.pilih_baris)

    def pilih_baris(self, _event):
        pilihan = self.tabel_stok.selection()
        if not pilihan:
            return
        kode = self.tabel_stok.item(pilihan[0])["values"][0]
        b = data_barang[str(kode)]
        self.var_kode.set(kode)
        self.var_nama.set(b["nama"])
        self.var_harga.set(b["harga"])
        self.var_stok.set(b["stok"])

    def bersihkan_form(self):
        for v in (self.var_kode, self.var_nama, self.var_harga, self.var_stok):
            v.set("")

    def jalankan(self, fungsi, *args, pesan=None):
        """Jalankan fungsi logika; tangkap error dan tampilkan sebagai pesan."""
        try:
            fungsi(*args)
        except ValueError as e:
            messagebox.showerror("Input tidak valid", str(e))
            return False
        simpan_data()
        if pesan:
            messagebox.showinfo("Berhasil", pesan)
        self.refresh_semua()
        return True

    def aksi_tambah(self):
        if self.jalankan(tambah_barang, self.var_kode.get(), self.var_nama.get(),
                         self.var_harga.get(), self.var_stok.get(), pesan="Barang ditambahkan."):
            self.bersihkan_form()

    def aksi_ubah(self):
        self.jalankan(ubah_barang, self.var_kode.get(), self.var_nama.get(),
                      self.var_harga.get(), self.var_stok.get(), pesan="Barang diperbarui.")

    def aksi_hapus(self):
        kode = self.var_kode.get()
        if messagebox.askyesno("Konfirmasi", f"Hapus barang {kode}?"):
            if self.jalankan(hapus_barang, kode, pesan="Barang dihapus."):
                self.bersihkan_form()

    # ---------- Tab Kasir ----------
    def buat_tab_kasir(self):
        atas = ttk.LabelFrame(self.tab_kasir, text="Tambah ke Keranjang")
        atas.pack(fill="x", padx=8, pady=8)

        self.var_pilih = tk.StringVar()
        self.var_jumlah = tk.StringVar(value="1")
        ttk.Label(atas, text="Barang").grid(row=0, column=0, padx=6, pady=6)
        self.combo = ttk.Combobox(atas, textvariable=self.var_pilih, state="readonly", width=34)
        self.combo.grid(row=0, column=1, padx=6)
        ttk.Label(atas, text="Jumlah").grid(row=0, column=2, padx=6)
        ttk.Entry(atas, textvariable=self.var_jumlah, width=8).grid(row=0, column=3, padx=6)
        ttk.Button(atas, text="Tambah", command=self.aksi_keranjang).grid(row=0, column=4, padx=6)

        self.tabel_keranjang = ttk.Treeview(self.tab_kasir, columns=("nama", "harga", "jumlah", "sub"),
                                            show="headings", height=10)
        for kol, judul, lebar in [("nama", "Nama Barang", 260), ("harga", "Harga", 120),
                                  ("jumlah", "Jumlah", 80), ("sub", "Subtotal", 140)]:
            self.tabel_keranjang.heading(kol, text=judul)
            self.tabel_keranjang.column(kol, width=lebar)
        self.tabel_keranjang.pack(fill="both", expand=True, padx=8)

        bawah = ttk.Frame(self.tab_kasir)
        bawah.pack(fill="x", padx=8, pady=8)
        self.lbl_subtotal = ttk.Label(bawah, text="Subtotal : Rp 0")
        self.lbl_diskon = ttk.Label(bawah, text="Diskon   : Rp 0")
        self.lbl_total = ttk.Label(bawah, text="TOTAL    : Rp 0", font=("Arial", 13, "bold"))
        for lbl in (self.lbl_subtotal, self.lbl_diskon, self.lbl_total):
            lbl.pack(anchor="w")
        ttk.Label(bawah, text="Diskon: 5% jika belanja >= Rp100.000, 10% jika >= Rp200.000",
                  foreground="gray").pack(anchor="w")

        tombol = ttk.Frame(bawah)
        tombol.pack(anchor="e")
        ttk.Button(tombol, text="Kosongkan", command=self.aksi_kosongkan).pack(side="left", padx=4)
        ttk.Button(tombol, text="Bayar", command=self.aksi_bayar).pack(side="left", padx=4)

    def aksi_keranjang(self):
        kode = self.var_pilih.get().split(" - ")[0]
        self.jalankan(tambah_ke_keranjang, kode, self.var_jumlah.get())

    def aksi_kosongkan(self):
        keranjang.clear()
        self.refresh_semua()

    def aksi_bayar(self):
        try:
            total = proses_bayar()
        except ValueError as e:
            messagebox.showerror("Gagal", str(e))
            return
        messagebox.showinfo("Pembayaran Berhasil", f"Total dibayar: {rupiah(total)}\nTerima kasih!")
        self.refresh_semua()

    # ---------- Refresh tampilan ----------
    def refresh_semua(self):
        self.tabel_stok.delete(*self.tabel_stok.get_children())
        for kode, b in data_barang.items():
            self.tabel_stok.insert("", "end", values=(kode, b["nama"], rupiah(b["harga"]), b["stok"]))

        self.combo["values"] = [f"{k} - {b['nama']} (stok {b['stok']})" for k, b in data_barang.items()]
        self.var_pilih.set("")

        self.tabel_keranjang.delete(*self.tabel_keranjang.get_children())
        for _, nama, harga, jumlah in keranjang:
            self.tabel_keranjang.insert("", "end",
                                        values=(nama, rupiah(harga), jumlah, rupiah(harga * jumlah)))

        subtotal, diskon, total = hitung_total()
        self.lbl_subtotal.config(text=f"Subtotal : {rupiah(subtotal)}")
        self.lbl_diskon.config(text=f"Diskon   : {rupiah(diskon)}")
        self.lbl_total.config(text=f"TOTAL    : {rupiah(total)}")


if __name__ == "__main__":
    muat_data()
    AplikasiKasir().mainloop()