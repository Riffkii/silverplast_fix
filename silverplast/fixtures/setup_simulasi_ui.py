"""
silverplast/fixtures/setup_simulasi_ui.py
==========================================
Setup data untuk simulasi Mutasi Barang via UI.

Script ini HANYA menyiapkan:
  1. Data Gudang (jika belum ada)
  2. Stok awal (jika belum ada)
  3. Dokumen Mutasi Barang status DRAFT — siap dilanjutkan dari UI

Jalankan SEKALI:
  bench --site dev.local execute \
    silverplast.fixtures.setup_simulasi_ui.run

Setelah script selesai, buka UI dan lanjutkan dari sana.
Tidak ada perubahan pada kode existing.
"""

import frappe
from frappe.utils import nowdate
from silverplast.inventory.doctype.stok.stok import (
    catat_transaksi_stok, get_stok_terkini
)


# ═══════════════════════════════════════════════════════════════
# KONFIGURASI DATA
# ═══════════════════════════════════════════════════════════════

GUDANG_DATA = [
    # ── Level Gudang (induk) ───────────────────────────────────
    {
        "kode_gudang" : "GDG-01",
        "nama_gudang" : "Gudang Produksi",
        "level"       : "Gudang",
        "tipe_barang" : "Campuran",
        "status"      : "Aktif",
        "kapasitas_ton": 200,
        "pic"         : "Admin Gudang 1",
        "alamat"      : "Area Produksi Blok A",
    },
    {
        "kode_gudang" : "GDG-02",
        "nama_gudang" : "Gudang Barang Jadi",
        "level"       : "Gudang",
        "tipe_barang" : "Barang Jadi",
        "status"      : "Aktif",
        "kapasitas_ton": 200,
        "pic"         : "Admin Gudang 2",
        "alamat"      : "Area Produksi Blok B",
    },
    {
        "kode_gudang" : "GDG-03",
        "nama_gudang" : "Gudang Bahan Baku",
        "level"       : "Gudang",
        "tipe_barang" : "Bahan Baku",
        "status"      : "Aktif",
        "kapasitas_ton": 150,
        "pic"         : "Admin Gudang 3",
        "alamat"      : "Area Penerimaan Blok C",
    },
    {
        "kode_gudang" : "GDG-04",
        "nama_gudang" : "Gudang Additive",
        "level"       : "Gudang",
        "tipe_barang" : "Additive",
        "status"      : "Aktif",
        "kapasitas_ton": 100,
        "pic"         : "Admin Gudang 4",
        "alamat"      : "Area Additive Blok D",
    },

    # ── Level Area ─────────────────────────────────────────────
    {
        "kode_gudang" : "GDG-01-A",
        "nama_gudang" : "Gudang Produksi - Area A (Barang Jadi)",
        "level"       : "Area",
        "tipe_barang" : "Barang Jadi",
        "status"      : "Aktif",
        "kapasitas_ton": 100,
        "induk_gudang": "GDG-01",
    },
    {
        "kode_gudang" : "GDG-01-B",
        "nama_gudang" : "Gudang Produksi - Area B (Bahan Baku)",
        "level"       : "Area",
        "tipe_barang" : "Bahan Baku",
        "status"      : "Aktif",
        "kapasitas_ton": 100,
        "induk_gudang": "GDG-01",
    },
    {
        "kode_gudang" : "GDG-02-A",
        "nama_gudang" : "Gudang Barang Jadi - Area A",
        "level"       : "Area",
        "tipe_barang" : "Barang Jadi",
        "status"      : "Aktif",
        "kapasitas_ton": 200,
        "induk_gudang": "GDG-02",
    },
    {
        "kode_gudang" : "GDG-03-A",
        "nama_gudang" : "Gudang Bahan Baku - Area A",
        "level"       : "Area",
        "tipe_barang" : "Bahan Baku",
        "status"      : "Aktif",
        "kapasitas_ton": 150,
        "induk_gudang": "GDG-03",
    },

    # ── Level Rak ──────────────────────────────────────────────
    {
        "kode_gudang" : "GDG-01-A-RAK1",
        "nama_gudang" : "Area A - Rak 1",
        "level"       : "Rak",
        "tipe_barang" : "",          # tidak wajib di Rak
        "status"      : "Aktif",
        "induk_gudang": "GDG-01-A",
        "kode_barang" : "PP-NAT-01",  # info barang di rak ini
    },
    {
        "kode_gudang" : "GDG-01-A-RAK2",
        "nama_gudang" : "Area A - Rak 2",
        "level"       : "Rak",
        "tipe_barang" : "",
        "status"      : "Aktif",
        "induk_gudang": "GDG-01-A",
        "kode_barang" : "PP-NAT-01",
    },
    {
        "kode_gudang" : "GDG-01-B-RAK1",
        "nama_gudang" : "Area B - Rak 1",
        "level"       : "Rak",
        "tipe_barang" : "",
        "status"      : "Aktif",
        "induk_gudang": "GDG-01-B",
        "kode_barang" : "BB-PLASTIK-01",
    },
]

# ── Data Stok Awal ─────────────────────────────────────────────
# Setiap entry akan menjadi 1 record di tabStok (tipe: Masuk)
STOK_AWAL = [
    # Bahan Baku di GDG-03
    {
        "item_code" : "BB-PLASTIK-01",
        "item_name" : "Plastik Cacah Campuran",
        "qty"       : 2000,
        "gudang"    : "GDG-03",
        "batch_no"  : "BCH-2026-001",
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },
    {
        "item_code" : "BB-PP-01",
        "item_name" : "PP Regrind / Bekas",
        "qty"       : 1500,
        "gudang"    : "GDG-03",
        "batch_no"  : "BCH-2026-002",
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },

    # Additive di GDG-04
    {
        "item_code" : "ADD-01",
        "item_name" : "Additive Putih Masterbatch",
        "qty"       : 500,
        "gudang"    : "GDG-04",
        "batch_no"  : None,
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },
    {
        "item_code" : "ADD-02",
        "item_name" : "Additive Hitam Masterbatch",
        "qty"       : 300,
        "gudang"    : "GDG-04",
        "batch_no"  : None,
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },

    # Barang Jadi di GDG-01
    {
        "item_code" : "PP-NAT-01",
        "item_name" : "Plastik Granul PP Natural",
        "qty"       : 3000,
        "gudang"    : "GDG-01",
        "batch_no"  : "BCH-2026-003",
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },
    {
        "item_code" : "PP-WH-01",
        "item_name" : "Plastik Granul PP White",
        "qty"       : 2000,
        "gudang"    : "GDG-01",
        "batch_no"  : "BCH-2026-004",
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },
    {
        "item_code" : "HDPE-01",
        "item_name" : "Granul HDPE Daur Ulang",
        "qty"       : 1500,
        "gudang"    : "GDG-01",
        "batch_no"  : "BCH-2026-005",
        "uom"       : "Kg",
        "keterangan": "Stok awal setup simulasi",
    },

    # Stok di area/rak — untuk simulasi intern gudang
    {
        "item_code" : "PP-NAT-01",
        "item_name" : "Plastik Granul PP Natural",
        "qty"       : 500,
        "gudang"    : "GDG-01-A",
        "batch_no"  : "BCH-2026-003",
        "uom"       : "Kg",
        "keterangan": "Stok awal area A — setup simulasi",
    },
    {
        "item_code" : "BB-PLASTIK-01",
        "item_name" : "Plastik Cacah Campuran",
        "qty"       : 200,
        "gudang"    : "GDG-01-B",
        "batch_no"  : "BCH-2026-001",
        "uom"       : "Kg",
        "keterangan": "Stok awal area B — setup simulasi",
    },
]

# ── Dokumen Mutasi DRAFT untuk simulasi UI ─────────────────────
MUTASI_DRAFT = [
    # ── A. Antar Gudang: GDG-03 → GDG-01 ─────────────────────
    {
        "label"                : "SIMULASI-A: Antar Gudang GDG-03 → GDG-01",
        "mutation_type"        : "Antar Gudang",
        "source_warehouse"     : "GDG-03",
        "destination_warehouse": "GDG-01",
        "catatan"              : "[SIMULASI A] Transfer bahan baku dari Gudang Bahan Baku ke Gudang Produksi. Lanjutkan: Submit → Terima Barang → Verifikasi Nota",
        "items": [
            {
                "item_code" : "BB-PLASTIK-01",
                "item_name" : "Plastik Cacah Campuran",
                "qty"       : 500,
                "uom"       : "Kg",
                "batch_no"  : "BCH-2026-001",
            },
            {
                "item_code" : "BB-PP-01",
                "item_name" : "PP Regrind / Bekas",
                "qty"       : 300,
                "uom"       : "Kg",
                "batch_no"  : "BCH-2026-002",
            },
        ],
    },

    # ── B. Antar Gudang: GDG-01 → GDG-02 ─────────────────────
    {
        "label"                : "SIMULASI-B: Antar Gudang GDG-01 → GDG-02",
        "mutation_type"        : "Antar Gudang",
        "source_warehouse"     : "GDG-01",
        "destination_warehouse": "GDG-02",
        "catatan"              : "[SIMULASI B] Transfer barang jadi ke gudang finished goods. Lanjutkan: Submit → Terima Barang → Verifikasi Nota",
        "items": [
            {
                "item_code" : "PP-NAT-01",
                "item_name" : "Plastik Granul PP Natural",
                "qty"       : 1000,
                "uom"       : "Kg",
                "batch_no"  : "BCH-2026-003",
            },
            {
                "item_code" : "PP-WH-01",
                "item_name" : "Plastik Granul PP White",
                "qty"       : 500,
                "uom"       : "Kg",
                "batch_no"  : "BCH-2026-004",
            },
        ],
    },

    # ── C. Intern Gudang: GDG-01 → Area A ────────────────────
    {
        "label"                  : "SIMULASI-C: Intern GDG-01 → GDG-01-A",
        "mutation_type"          : "Intern Gudang",
        "source_warehouse"       : "GDG-01",
        "source_area_intern"     : None,          # dari gudang induk
        "destination_area_intern": "GDG-01-A",
        "catatan"                : "[SIMULASI C] Intern gudang: pindah PP-NAT-01 dari gudang induk ke Area A. Lanjutkan: Submit (langsung Selesai)",
        "items": [
            {
                "item_code"       : "PP-NAT-01",
                "item_name"       : "Plastik Granul PP Natural",
                "qty"             : 300,
                "uom"             : "Kg",
                "batch_no"        : "BCH-2026-003",
                "source_area"     : None,
                "destination_area": "GDG-01-A",
            },
        ],
    },

    # ── D. Intern Gudang: GDG-01-A → GDG-01-A-RAK1 ──────────
    {
        "label"                  : "SIMULASI-D: Intern GDG-01-A → GDG-01-A-RAK1",
        "mutation_type"          : "Intern Gudang",
        "source_warehouse"       : "GDG-01",
        "source_area_intern"     : "GDG-01-A",
        "destination_area_intern": "GDG-01-A-RAK1",
        "catatan"                : "[SIMULASI D] Intern gudang: pindah dari Area A ke Rak 1 untuk optimasi FIFO. Lanjutkan: Submit (langsung Selesai)",
        "items": [
            {
                "item_code"       : "PP-NAT-01",
                "item_name"       : "Plastik Granul PP Natural",
                "qty"             : 200,
                "uom"             : "Kg",
                "batch_no"        : "BCH-2026-003",
                "source_area"     : "GDG-01-A",
                "destination_area": "GDG-01-A-RAK1",
            },
        ],
    },
]


# ═══════════════════════════════════════════════════════════════
# RUNNER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _sep(char="─", width=58):
    print(char * width)

def _ok(msg):   print(f"  ✓  {msg}")
def _skip(msg): print(f"  →  {msg} (sudah ada, skip)")
def _err(msg):  print(f"  ✗  {msg}")
def _info(msg): print(f"     {msg}")


# ── 1. Setup Gudang ────────────────────────────────────────────

def setup_gudang():
    print("\n[1/3] SETUP DATA GUDANG")
    _sep()
    created = skipped = 0

    for d in GUDANG_DATA:
        kode = d["kode_gudang"]

        if frappe.db.exists("Gudang", kode):
            _skip(f"Gudang {kode}")
            skipped += 1
            continue

        try:
            doc = frappe.get_doc({"doctype": "Gudang", **d})
            doc.insert(ignore_permissions=True)
            _ok(f"Gudang {kode} — {d['nama_gudang']} [{d['level']}]")
            created += 1
        except Exception as e:
            _err(f"Gagal buat {kode}: {e}")

    frappe.db.commit()
    print(f"\n  Gudang: {created} dibuat, {skipped} dilewati\n")
    return created


# ── 2. Setup Stok Awal ─────────────────────────────────────────

def setup_stok_awal():
    print("\n[2/3] SETUP STOK AWAL")
    _sep()
    created = skipped = 0

    for d in STOK_AWAL:
        item_code = d["item_code"]
        gudang    = d["gudang"]

        # Skip jika stok sudah ada (ada transaksi apapun untuk item+gudang ini)
        existing_stok = get_stok_terkini(item_code, gudang)
        if existing_stok > 0:
            _skip(f"{item_code} @ {gudang}: {existing_stok} Kg")
            skipped += 1
            continue

        # Skip jika sudah ada record stok awal untuk kombinasi ini
        already = frappe.db.get_value("Stok", {
            "item_code"      : item_code,
            "gudang"         : gudang,
            "ref_docname"    : "SETUP-AWAL",
            "tipe_transaksi" : "Masuk",
        }, "name")
        if already:
            _skip(f"{item_code} @ {gudang} (record ada)")
            skipped += 1
            continue

        try:
            ref = catat_transaksi_stok(
                item_code      = item_code,
                item_name      = d["item_name"],
                qty            = d["qty"],
                gudang         = gudang,
                tipe_transaksi = "Masuk",
                ref_doctype    = "Stok Awal",
                ref_docname    = "SETUP-AWAL",
                batch_no       = d.get("batch_no"),
                uom            = d.get("uom", "Kg"),
                keterangan     = d.get("keterangan", "Setup awal simulasi"),
            )
            _ok(f"{item_code} @ {gudang}: {d['qty']:,} Kg → {ref}")
            created += 1
        except Exception as e:
            _err(f"Gagal catat stok {item_code} @ {gudang}: {e}")

    frappe.db.commit()
    print(f"\n  Stok: {created} dibuat, {skipped} dilewati")

    # Print ringkasan stok
    print("\n  RINGKASAN STOK SETELAH SETUP:")
    _sep("-")
    from silverplast.inventory.doctype.stok.stok import get_ringkasan_stok
    ringkasan = get_ringkasan_stok()
    print(f"  {'Gudang':<18} {'Item':<16} {'Stok':>8} {'UOM'}")
    _sep("-")
    for r in ringkasan:
        print(f"  {r.gudang:<18} {r.item_code:<16} {r.stok_saat_ini:>8,.0f} {r.uom}")
    print()
    return created


# ── 3. Buat Dokumen Mutasi DRAFT ──────────────────────────────

def setup_mutasi_draft():
    print("\n[3/3] BUAT DOKUMEN MUTASI BARANG (STATUS: DRAFT)")
    _sep()
    print("  Dokumen ini bisa langsung dilanjutkan dari UI.\n")
    created = skipped = 0

    for d in MUTASI_DRAFT:
        label = d.pop("label")
        items = d.pop("items")

        # Skip jika catatan sama sudah ada
        existing = frappe.db.get_value("Mutasi Barang", {
            "catatan"     : d["catatan"],
            "docstatus"   : 0,
        }, "name")
        if existing:
            _skip(f"{label} → {existing}")
            d["label"] = label
            d["items"] = items
            skipped += 1
            continue

        try:
            doc = frappe.get_doc({
                "doctype"       : "Mutasi Barang",
                "naming_series" : "MUT-.YYYY.-",
                "tanggal_mutasi": nowdate(),
                "posting_time"  : "08:00:00",
                "status"        : "Draft",
                **d
            })

            for item in items:
                doc.append("items", item)

            doc.insert(ignore_permissions=True)
            _ok(f"{label}")
            _info(f"Dokumen: {doc.name}")
            _info(f"URL    : /app/mutasi-barang/{doc.name}")
            print()
            created += 1

        except Exception as e:
            _err(f"Gagal buat {label}: {e}")

        finally:
            d["label"] = label
            d["items"] = items

    frappe.db.commit()
    print(f"  Mutasi Draft: {created} dibuat, {skipped} dilewati\n")
    return created


# ── MAIN ───────────────────────────────────────────────────────

def run():
    print()
    _sep("═")
    print("  SETUP SIMULASI MUTASI BARANG — Silverplast")
    print("  Mode: Data siap untuk dilanjutkan via UI")
    _sep("═")

    g = setup_gudang()
    s = setup_stok_awal()
    m = setup_mutasi_draft()

    _sep("═")
    print("  SELESAI!")
    print(f"  Gudang: {g} | Stok awal: {s} | Mutasi Draft: {m}")
    _sep("═")

    print()
    print("  LANGKAH SELANJUTNYA DI UI:")
    print()
    print("  A. MUTASI ANTAR GUDANG (GDG-03 → GDG-01):")
    print("     1. Buka List Mutasi Barang")
    print("     2. Pilih dokumen dengan catatan [SIMULASI A]")
    print("     3. Klik Submit → barang 'Dikirim'")
    print("     4. Klik Terima Barang → barang 'Diterima'")
    print("     5. Klik Verifikasi Nota → status 'Selesai'")
    print()
    print("  B. MUTASI ANTAR GUDANG (GDG-01 → GDG-02):")
    print("     Sama seperti A, pilih dokumen [SIMULASI B]")
    print()
    print("  C. MUTASI INTERN (GDG-01 → GDG-01-A):")
    print("     1. Pilih dokumen [SIMULASI C]")
    print("     2. Klik Submit → langsung 'Selesai'")
    print()
    print("  D. MUTASI INTERN (GDG-01-A → GDG-01-A-RAK1):")
    print("     1. Pilih dokumen [SIMULASI D]")
    print("     2. Klik Submit → langsung 'Selesai'")
    print()
    print("  Cek stok setelah simulasi:")
    print("  → Buka menu Stok → filter by gudang")
    print("  → Atau buka Gudang → klik Aksi → Riwayat Mutasi")
    print()