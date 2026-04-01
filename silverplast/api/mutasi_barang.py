# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt
#
# API Mutasi Barang — dipanggil dari mutasi_barang.js
# via frappe.call({ method: "silverplast.api.mutasi_barang.xxx" })

import frappe
from frappe import _


@frappe.whitelist()
def terima_barang(docname):
    """
    Diagram Antar Gudang: Gudang Tujuan → Penerimaan Barang → update stock
    Dipanggil dari tombol 'Terima Barang' di form.
    """
    doc = frappe.get_doc("Mutasi Barang", docname)

    if doc.docstatus != 1:
        frappe.throw(_("Dokumen harus dalam status Submitted untuk menerima barang."))

    if doc.mutation_type != "Antar Gudang":
        frappe.throw(_("Aksi ini hanya berlaku untuk Mutasi Antar Gudang."))

    doc.terima_barang()
    return {"status": doc.status}


@frappe.whitelist()
def verifikasi_nota(docname):
    """
    Diagram Antar Gudang: Gudang Tujuan → Verifikasi Nota → End
    Dipanggil dari tombol 'Verifikasi Nota' di form.
    """
    doc = frappe.get_doc("Mutasi Barang", docname)

    if doc.docstatus != 1:
        frappe.throw(_("Dokumen harus dalam status Submitted untuk diverifikasi."))

    doc.verifikasi_nota()
    return {"status": doc.status}


@frappe.whitelist()
def get_stock_available(item_code, warehouse):
    """
    Cek stok tersedia untuk item tertentu di gudang tertentu.
    Dipanggil saat input item di child table.
    """
    if not item_code or not warehouse:
        return 0

    result = frappe.db.sql("""
        SELECT SUM(actual_qty) AS qty
        FROM `tabStock Ledger Entry`
        WHERE
            item_code = %(item_code)s
            AND warehouse = %(warehouse)s
            AND is_cancelled = 0
    """, {"item_code": item_code, "warehouse": warehouse}, as_dict=True)

    return result[0].qty if result and result[0].qty else 0


@frappe.whitelist()
def get_mutasi_summary(warehouse=None, from_date=None, to_date=None):
    """
    Ringkasan mutasi barang untuk dashboard.
    Opsional filter per gudang dan tanggal.
    """
    filters = {"docstatus": 1}

    if warehouse:
        filters["source_warehouse"] = warehouse
    if from_date:
        filters["tanggal_mutasi"] = [">=", from_date]
    if to_date:
        filters["tanggal_mutasi"] = ["<=", to_date]

    mutasi = frappe.db.get_all(
        "Mutasi Barang",
        filters=filters,
        fields=[
            "name",
            "mutation_type",
            "status",
            "tanggal_mutasi",
            "source_warehouse",
            "destination_warehouse",
            "catatan"
        ],
        order_by="tanggal_mutasi desc",
        limit=100
    )
    return mutasi