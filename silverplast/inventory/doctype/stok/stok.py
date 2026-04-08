# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, now_datetime


class Stok(Document):
    pass


# ─────────────────────────────────────────────────────────
# Fungsi utilitas — dipanggil dari Mutasi Barang & Item Receipt
# ─────────────────────────────────────────────────────────

def catat_transaksi_stok(
    item_code,
    item_name,
    qty,
    gudang,
    tipe_transaksi,
    ref_doctype=None,
    ref_docname=None,
    area_rak=None,
    batch_no=None,
    uom="Kg",
    keterangan=None
):
    """
    Catat satu baris transaksi stok.

    tipe_transaksi:
      - 'Masuk'        : barang masuk dari Item Receipt Document (QC Pass)
      - 'Keluar'       : barang keluar untuk penjualan / produksi
      - 'Pindah Keluar': barang keluar gudang asal (Mutasi Antar Gudang)
      - 'Pindah Masuk' : barang masuk gudang tujuan (Mutasi Antar Gudang)
      - 'Opname'       : koreksi stok dari stock opname
    """
    
    existing = frappe.db.get_value("Stok", {
        "ref_doctype": ref_doctype,
        "ref_docname": ref_docname,
        "tipe_transaksi": tipe_transaksi,
        "item_code": item_code,
        "gudang": gudang
    }, "name")
    if existing:
        return existing
    
    qty_sebelum = get_stok_terkini(item_code, gudang)

    if tipe_transaksi in ("Masuk", "Pindah Masuk"):
        qty_sesudah = qty_sebelum + qty
    elif tipe_transaksi in ("Keluar", "Pindah Keluar"):
        qty_sesudah = max(qty_sebelum - qty, 0)
    else:  # Opname
        qty_sesudah = qty  # qty adalah nilai koreksi langsung

    # Buat dokumen Stok
    doc = frappe.get_doc({
        "doctype"         : "Stok",
        "tanggal"         : nowdate(),
        "jam"             : now_datetime().strftime("%H:%M:%S"),
        "tipe_transaksi"  : tipe_transaksi,
        "item_code"       : item_code,
        "item_name"       : item_name or item_code,
        "qty"             : qty,
        "uom"             : uom,
        "batch_no"        : batch_no,
        "gudang"          : gudang,
        "area_rak"        : area_rak,
        "qty_sebelum"     : qty_sebelum,
        "qty_sesudah"     : qty_sesudah,
        "ref_doctype"     : ref_doctype,
        "ref_docname"     : ref_docname,
        "keterangan"      : keterangan,
        "status"          : "Aktif"
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def get_stok_terkini(item_code, gudang):
    """
    Ambil stok terkini dari tabel Stok
    berdasarkan qty_sesudah transaksi terakhir.
    """
    result = frappe.db.sql("""
        SELECT qty_sesudah
        FROM `tabStok`
        WHERE
            item_code = %(item_code)s
            AND gudang  = %(gudang)s
            AND status  = 'Aktif'
        ORDER BY tanggal DESC, jam DESC, creation DESC
        LIMIT 1
    """, {"item_code": item_code, "gudang": gudang}, as_dict=True)

    return result[0].qty_sesudah if result else 0


def get_ringkasan_stok(gudang=None, item_code=None):
    """
    Ringkasan stok terkini per item per gudang.
    Dipakai di dashboard dan laporan.
    """
    where = ["s1.status = 'Aktif'"]
    params = {}

    if gudang:
        where.append("s1.gudang = %(gudang)s")
        params["gudang"] = gudang

    if item_code:
        where.append("s1.item_code = %(item_code)s")
        params["item_code"] = item_code

    where_str = " AND ".join(where)

    # Ambil qty_sesudah dari transaksi terakhir per item per gudang
    result = frappe.db.sql(f"""
        SELECT
            s1.item_code,
            s1.item_name,
            s1.gudang,
            s1.uom,
            s1.qty_sesudah AS stok_saat_ini
        FROM `tabStok` s1
        INNER JOIN (
            SELECT item_code, gudang, MAX(creation) AS max_creation
            FROM `tabStok`
            WHERE status = 'Aktif'
            GROUP BY item_code, gudang
        ) s2 ON s1.item_code = s2.item_code
              AND s1.gudang   = s2.gudang
              AND s1.creation = s2.max_creation
        WHERE {where_str}
          AND s1.qty_sesudah > 0
        ORDER BY s1.gudang, s1.item_code
    """, params, as_dict=True)

    return result



