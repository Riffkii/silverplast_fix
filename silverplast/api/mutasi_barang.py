# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def terima_barang(docname):
    doc = frappe.get_doc("Mutasi Barang", docname)
    if doc.docstatus != 1:
        frappe.throw(_("Dokumen harus Submitted."))
    if doc.mutation_type != "Antar Gudang":
        frappe.throw(_("Hanya untuk Mutasi Antar Gudang."))
    doc.terima_barang()
    return {"status": doc.status}


@frappe.whitelist()
def verifikasi_nota(docname):
    doc = frappe.get_doc("Mutasi Barang", docname)
    if doc.docstatus != 1:
        frappe.throw(_("Dokumen harus Submitted."))
    doc.verifikasi_nota()
    return {"status": doc.status}


@frappe.whitelist()
def get_mutasi_summary(warehouse=None, from_date=None, to_date=None):
    """Ringkasan mutasi untuk dashboard."""
    filters = {"docstatus": 1}
    if warehouse:
        filters["source_warehouse"] = warehouse
    if from_date:
        filters["tanggal_mutasi"] = [">=", from_date]
    if to_date:
        filters["tanggal_mutasi"] = ["<=", to_date]

    return frappe.db.get_all(
        "Mutasi Barang",
        filters=filters,
        fields=[
            "name", "mutation_type", "status",
            "tanggal_mutasi", "source_warehouse",
            "destination_warehouse", "catatan"
        ],
        order_by="tanggal_mutasi desc",
        limit=100
    )