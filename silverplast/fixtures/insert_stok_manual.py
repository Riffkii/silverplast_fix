"""
fixtures/insert_stok_manual.py
================================
Insert data stok awal langsung ke database MariaDB
menggunakan frappe.db (bukan lewat UI).

Menghitung qty_sebelum dan qty_sesudah otomatis.

Jalankan:
  bench --site [site] execute \
    silverplast.fixtures.insert_stok_manual.run
"""

import frappe
from frappe.utils import nowdate, now_datetime


# ─────────────────────────────────────────────────────────────
# DATA STOK AWAL
# Sesuai item_receipt dan gudang yang sudah dibuat
# ─────────────────────────────────────────────────────────────

STOK_AWAL = [
    # ── Bahan Baku di GDG-03 ──────────────────────────────────
    {
        "item_code"  : "BB-PLASTIK-01",
        "item_name"  : "Plastik Cacah Campuran",
        "qty"        : 2000,
        "gudang"     : "GDG-03",
        "area_rak"   : "GDG-03-A",
        "batch_no"   : "BCH-2026-001",
        "uom"        : "Kg",
    },
    {
        "item_code"  : "BB-PP-01",
        "item_name"  : "PP Bekas / Regrind",
        "qty"        : 1500,
        "gudang"     : "GDG-03",
        "area_rak"   : "GDG-03-A",
        "batch_no"   : "BCH-2026-002",
        "uom"        : "Kg",
    },

    # ── Additive di GDG-04 ────────────────────────────────────
    {
        "item_code"  : "ADD-01",
        "item_name"  : "Additive Putih (Masterbatch)",
        "qty"        : 500,
        "gudang"     : "GDG-04",
        "area_rak"   : None,
        "batch_no"   : None,
        "uom"        : "Kg",
    },
    {
        "item_code"  : "ADD-02",
        "item_name"  : "Additive Hitam (Masterbatch)",
        "qty"        : 300,
        "gudang"     : "GDG-04",
        "area_rak"   : None,
        "batch_no"   : None,
        "uom"        : "Kg",
    },

    # ── Barang Jadi di GDG-01 ─────────────────────────────────
    {
        "item_code"  : "PP-NAT-01",
        "item_name"  : "Plastik Granul PP Natural",
        "qty"        : 5000,
        "gudang"     : "GDG-01",
        "area_rak"   : "GDG-01-A",
        "batch_no"   : "BCH-2026-003",
        "uom"        : "Kg",
    },
    {
        "item_code"  : "HDPE-01",
        "item_name"  : "Granul HDPE Daur Ulang",
        "qty"        : 3000,
        "gudang"     : "GDG-01",
        "area_rak"   : "GDG-01-A",
        "batch_no"   : "BCH-2026-004",
        "uom"        : "Kg",
    },
    {
        "item_code"  : "PP-WH-01",
        "item_name"  : "Plastik Granul PP White",
        "qty"        : 2500,
        "gudang"     : "GDG-01",
        "area_rak"   : "GDG-01-A-RAK1",
        "batch_no"   : "BCH-2026-005",
        "uom"        : "Kg",
    },

    # ── Bahan Baku cadangan di GDG-01-B ──────────────────────
    {
        "item_code"  : "BB-PLASTIK-01",
        "item_name"  : "Plastik Cacah Campuran",
        "qty"        : 200,
        "gudang"     : "GDG-01",
        "area_rak"   : "GDG-01-B",
        "batch_no"   : "BCH-2026-001",
        "uom"        : "Kg",
    },
]


def run():
    """
    Insert stok awal langsung ke tabStok via frappe.db.
    Menghitung qty_sebelum dari transaksi terakhir yang ada.
    """
    print("\n" + "="*60)
    print("  INSERT STOK AWAL — Silverplast")
    print("="*60)

    # Cek apakah sudah ada stok awal
    existing = frappe.db.count("Stok", {"ref_docname": "SETUP-AWAL"})
    if existing > 0:
        print(f"\n[SKIP] Sudah ada {existing} record stok awal (ref: SETUP-AWAL).")
        print("  Jalankan reset_stok() dulu jika ingin insert ulang.\n")
        return

    tanggal = nowdate()
    jam     = "07:00:00"
    created = []

    for d in STOK_AWAL:
        # Hitung qty_sebelum dari record terakhir item+gudang ini
        last = frappe.db.sql("""
            SELECT qty_sesudah
            FROM   `tabStok`
            WHERE  item_code = %(ic)s
              AND  gudang    = %(gd)s
              AND  status    = 'Aktif'
            ORDER BY tanggal DESC, jam DESC, creation DESC
            LIMIT 1
        """, {"ic": d["item_code"], "gd": d["gudang"]}, as_dict=True)

        qty_sebelum = (last[0].qty_sesudah if last else 0) or 0
        qty_sesudah = qty_sebelum + d["qty"]

        # Generate naming series manual
        # Format: STK-2026-XXXXX
        count   = frappe.db.count("Stok") + len(created) + 1
        name    = f"STK-{tanggal[:4]}-{str(count).zfill(5)}"

        now_str = now_datetime().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Insert langsung ke database
        frappe.db.sql("""
            INSERT INTO `tabStok`
                (name, creation, modified, modified_by, owner, docstatus,
                 naming_series, tanggal, jam, tipe_transaksi, status,
                 item_code, item_name, qty, uom, batch_no,
                 gudang, area_rak,
                 qty_sebelum, qty_sesudah,
                 ref_doctype, ref_docname, keterangan)
            VALUES
                (%(name)s, %(now)s, %(now)s, 'Administrator', 'Administrator', 0,
                 'STK-.YYYY.-', %(tanggal)s, %(jam)s, 'Masuk', 'Aktif',
                 %(item_code)s, %(item_name)s, %(qty)s, %(uom)s, %(batch_no)s,
                 %(gudang)s, %(area_rak)s,
                 %(qty_sebelum)s, %(qty_sesudah)s,
                 'Item Receipt Document', 'SETUP-AWAL',
                 'Setup awal stok simulasi')
        """, {
            "name"       : name,
            "now"        : now_str,
            "tanggal"    : tanggal,
            "jam"        : jam,
            "item_code"  : d["item_code"],
            "item_name"  : d["item_name"],
            "qty"        : d["qty"],
            "uom"        : d.get("uom", "Kg"),
            "batch_no"   : d.get("batch_no") or "",
            "gudang"     : d["gudang"],
            "area_rak"   : d.get("area_rak") or "",
            "qty_sebelum": qty_sebelum,
            "qty_sesudah": qty_sesudah,
        })

        created.append(name)
        area_info = d.get("area_rak") or "-"
        print(f"  [OK] {name}")
        print(f"       {d['item_code']:15s} | {d['gudang']:10s} | "
              f"{area_info:18s} | "
              f"{qty_sebelum:>6.0f} → {qty_sesudah:>6.0f} Kg")

    frappe.db.commit()

    print("\n" + "-"*60)
    print(f"  SELESAI: {len(created)} stok awal berhasil diinsert")
    print("-"*60)
    _print_ringkasan()
    return created


def _print_ringkasan():
    """Tampilkan ringkasan stok terkini setelah insert."""
    print("\n  RINGKASAN STOK TERKINI:")
    print(f"  {'Gudang':<10} {'Item':<15} {'Stok':>8} {'Satuan':<6}")
    print("  " + "-"*44)

    rows = frappe.db.sql("""
        SELECT s1.gudang, s1.item_code, s1.qty_sesudah AS stok, s1.uom
        FROM `tabStok` s1
        INNER JOIN (
            SELECT item_code, gudang, MAX(creation) AS mc
            FROM `tabStok` WHERE status='Aktif'
            GROUP BY item_code, gudang
        ) s2 ON s1.item_code=s2.item_code
             AND s1.gudang=s2.gudang
             AND s1.creation=s2.mc
        WHERE s1.qty_sesudah > 0
        ORDER BY s1.gudang, s1.item_code
    """, as_dict=True)

    for r in rows:
        print(f"  {r.gudang:<10} {r.item_code:<15} "
              f"{r.stok:>8.0f} {r.uom:<6}")
    print()


def reset_stok():
    """
    HATI-HATI: Hapus semua stok dengan ref SETUP-AWAL.
    Hanya untuk keperluan testing/reset simulasi.

    bench --site [site] execute \
      silverplast.fixtures.insert_stok_manual.reset_stok
    """
    docs = frappe.db.get_all("Stok", {"ref_docname": "SETUP-AWAL"}, ["name"])
    for d in docs:
        frappe.db.sql("DELETE FROM `tabStok` WHERE name=%s", d.name)
    frappe.db.commit()
    print(f"[RESET] {len(docs)} record stok awal dihapus.")