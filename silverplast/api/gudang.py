# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt
#
# API untuk module Warehouse — dipanggil dari warehouse.js
# via frappe.call({ method: "silverplast.api.warehouse.xxx" })

import frappe
from frappe import _


@frappe.whitelist()
def get_child_locations(warehouse_code):
    """
    WH-01: Ambil semua Area dan Rak di bawah gudang tertentu.
    Dipanggil dari tombol 'Sub-Lokasi' di form Warehouse.
    """
    if not warehouse_code:
        frappe.throw(_("Kode gudang tidak boleh kosong."))

    children = frappe.db.get_all(
        "Warehouse",
        filters={
            "parent_warehouse": warehouse_code,
            "status": "Aktif"
        },
        fields=["warehouse_code", "warehouse_name", "level", "warehouse_type"],
        order_by="level asc, warehouse_code asc"
    )
    return children


@frappe.whitelist()
def get_stock_summary(warehouse_code):
    """
    WH-02 & WH-03: Ringkasan stok semua item di gudang ini.
    Dipanggil dari tombol 'Lihat Stok' di form Warehouse.

    Menggunakan tabStock Ledger Entry dari ERPNext untuk
    membaca mutasi nyata (bukan hanya data master warehouse).
    """
    if not warehouse_code:
        frappe.throw(_("Kode gudang tidak boleh kosong."))

    stock = frappe.db.sql("""
        SELECT
            sle.item_code,
            i.item_name,
            i.item_group,
            SUM(sle.actual_qty) AS qty,
            sle.stock_uom
        FROM `tabStock Ledger Entry` sle
        LEFT JOIN `tabItem` i ON i.name = sle.item_code
        WHERE
            sle.warehouse = %(warehouse_code)s
            AND sle.is_cancelled = 0
        GROUP BY sle.item_code, sle.stock_uom
        HAVING SUM(sle.actual_qty) > 0
        ORDER BY i.item_group, i.item_name
    """, {"warehouse_code": warehouse_code}, as_dict=True)

    return stock


@frappe.whitelist()
def get_all_warehouses():
    warehouses = frappe.db.get_all(
        "Warehouse",
        filters={"status": "Aktif", "level": "Gudang"},
        fields=[
            "warehouse_code",
            "warehouse_name",
            "warehouse_type",
            "capacity_ton",
            "current_stock_ton",
            "pic",
            "address"
        ],
        order_by="warehouse_code asc"
    )

    for wh in warehouses:
        cap = wh.get("capacity_ton") or 0
        cur = wh.get("current_stock_ton") or 0
        wh["usage_pct"] = round((cur / cap * 100), 1) if cap > 0 else 0

    return warehouses