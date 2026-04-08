# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from silverplast.inventory.doctype.stok.stok import get_ringkasan_stok


@frappe.whitelist()
def get_child_locations(kode_gudang):
    """WH-01: Ambil Area dan Rak di bawah gudang."""
    if not kode_gudang:
        frappe.throw(_("Kode gudang tidak boleh kosong."))

    return frappe.db.get_all(
        "Gudang",
        filters={"induk_gudang": kode_gudang, "status": "Aktif"},
        fields=["kode_gudang", "nama_gudang", "level", "tipe_barang"],
        order_by="level asc, kode_gudang asc"
    )


@frappe.whitelist()
def get_stock_summary(kode_gudang):
    """
    WH-02 & WH-03: Ringkasan stok semua item di gudang ini.
    Pakai tabStok custom (bukan tabStock Ledger Entry ERPNext).
    """
    if not kode_gudang:
        frappe.throw(_("Kode gudang tidak boleh kosong."))

    return get_ringkasan_stok(gudang=kode_gudang)


@frappe.whitelist()
def get_all_warehouses():
    """Dashboard Pak Michael: semua gudang + persentase kapasitas."""
    warehouses = frappe.db.get_all(
        "Gudang",
        filters={"status": "Aktif", "level": "Gudang"},
        fields=[
            "kode_gudang", "nama_gudang", "tipe_barang",
            "kapasitas_ton", "stok_saat_ini_ton", "pic", "alamat"
        ],
        order_by="kode_gudang asc"
    )

    for wh in warehouses:
        cap = wh.get("kapasitas_ton") or 0
        cur = wh.get("stok_saat_ini_ton") or 0
        wh["usage_pct"] = round((cur / cap * 100), 1) if cap > 0 else 0

    return warehouses