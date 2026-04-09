# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from silverplast.inventory.doctype.stok.stok import (
    catat_transaksi_stok, get_stok_terkini, get_ringkasan_stok
)


class StockOpname(Document):

    def validate(self):
        if self.is_new():
            self.status = "Draft"
        # Hitung difference hanya jika sudah ada items dengan actual_qty
        if any(row.actual_qty for row in self.items):
            self._calculate_differences()

    def on_submit(self):
        """BPMN: Pembuatan Perintah SO → In Progress"""
        self.db_set("status", "In Progress")
        frappe.msgprint(
            _("Stock Opname {0} started. Staff can begin counting.").format(
                frappe.bold(self.name)
            ),
            title=_("Opname Started"), indicator="orange"
        )

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    def _calculate_differences(self):
        total_system = 0
        total_actual = 0
        total_gain   = 0
        total_loss   = 0

        for row in self.items:
            row.system_qty = get_stok_terkini(row.item_code, self.warehouse)
            diff = (row.actual_qty or 0) - (row.system_qty or 0)
            row.difference = round(diff, 3)

            if diff > 0:
                row.difference_type = "Gain"
                total_gain += diff
            elif diff < 0:
                row.difference_type = "Loss"
                total_loss += abs(diff)
            else:
                row.difference_type = "Match"

            total_system += row.system_qty or 0
            total_actual += row.actual_qty or 0

        self.total_system_qty = round(total_system, 3)
        self.total_actual_qty = round(total_actual, 3)
        self.total_gain       = round(total_gain, 3)
        self.total_loss       = round(total_loss, 3)


# ─────────────────────────────────────────────────────────
# Whitelist functions — dipanggil dari JS via frappe.call
# ─────────────────────────────────────────────────────────

@frappe.whitelist()
def load_system_stock(docname):
    """
    BPMN: Cetak Posisi Stock — baca dari Data Stock (tabStok).
    Auto-fill system_qty untuk semua item di gudang yang di-opname.
    """
    doc = frappe.get_doc("Stock Opname", docname)

    if doc.status not in ("Draft", "In Progress"):
        frappe.throw(_("Can only load stock in Draft or In Progress status."))

    ringkasan = get_ringkasan_stok(gudang=doc.warehouse)

    if not ringkasan:
        frappe.throw(
            _("No stock data found for warehouse {0}. "
              "Make sure stock entries exist.").format(doc.warehouse)
        )

    # Clear existing rows
    frappe.db.delete("Stock Opname Item", {"parent": docname})

    for r in ringkasan:
        row = frappe.get_doc({
            "doctype"    : "Stock Opname Item",
            "parent"     : docname,
            "parenttype" : "Stock Opname",
            "parentfield": "items",
            "item_code"  : r["item_code"],
            "item_name"  : r["item_name"],
            "uom"        : r["uom"],
            "system_qty" : r["stok_saat_ini"],
            "actual_qty" : 0,
            "difference" : 0,
            "difference_type": "Match"
        })
        row.insert(ignore_permissions=True)

    frappe.db.commit()

    frappe.msgprint(
        _("{0} items loaded from system stock. "
          "Staff can now fill in the actual counted qty.").format(len(ringkasan)),
        title=_("Stock Position Loaded"), indicator="blue"
    )
    return {"items_loaded": len(ringkasan)}


@frappe.whitelist()
def recapitulate(docname):
    """
    BPMN: Rekapitulasi Hasil SO → Perhitungan Gain/Loss.
    Sync system_qty terbaru dan hitung difference.
    """
    doc = frappe.get_doc("Stock Opname", docname)

    if doc.status != "In Progress":
        frappe.throw(_("Status must be 'In Progress' to recapitulate."))

    total_system = total_actual = total_gain = total_loss = 0

    for row in doc.items:
        row.system_qty = get_stok_terkini(row.item_code, doc.warehouse)
        diff = (row.actual_qty or 0) - (row.system_qty or 0)
        row.difference = round(diff, 3)

        if diff > 0:
            row.difference_type = "Gain"
            total_gain += diff
        elif diff < 0:
            row.difference_type = "Loss"
            total_loss += abs(diff)
        else:
            row.difference_type = "Match"

        total_system += row.system_qty or 0
        total_actual += row.actual_qty or 0

    doc.total_system_qty = round(total_system, 3)
    doc.total_actual_qty = round(total_actual, 3)
    doc.total_gain       = round(total_gain, 3)
    doc.total_loss       = round(total_loss, 3)

    doc.save(ignore_permissions=True)
    doc.db_set("status", "Recapitulated")

    frappe.msgprint(
        _("Recapitulation complete.\n"
          "Total Gain: {0} Kg | Total Loss: {1} Kg").format(
            round(total_gain, 2), round(total_loss, 2)
        ),
        title=_("Recapitulated"), indicator="blue"
    )
    return {
        "total_gain": round(total_gain, 3),
        "total_loss": round(total_loss, 3)
    }


@frappe.whitelist()
def approve_and_update_stock(docname):
    """
    BPMN: Update Stock → Data Stock → End.
    Catat transaksi Opname ke tabStok untuk setiap item yang berbeda.
    """
    doc = frappe.get_doc("Stock Opname", docname)

    if doc.status != "Recapitulated":
        frappe.throw(_("Status must be 'Recapitulated' before approving."))

    updated = 0
    skipped = 0

    for row in doc.items:
        if row.difference == 0:
            skipped += 1
            continue

        catat_transaksi_stok(
            item_code      = row.item_code,
            item_name      = row.item_name or row.item_code,
            qty            = row.actual_qty,
            gudang         = doc.warehouse,
            tipe_transaksi = "Opname",
            ref_doctype    = "Stock Opname",
            ref_docname    = doc.name,
            batch_no       = row.batch_no,
            uom            = row.uom or "Kg",
            keterangan     = (
                f"Stock Opname {doc.name} - "
                f"{'Gain' if row.difference > 0 else 'Loss'} "
                f"{abs(row.difference)} Kg"
            )
        )
        updated += 1

    doc.db_set("status", "Approved")
    doc.db_set("approved_by", frappe.session.user)

    frappe.msgprint(
        _("Stock Opname {0} Approved.\n"
          "{1} items adjusted | {2} items matched (no change).").format(
            frappe.bold(doc.name), updated, skipped
        ),
        title=_("Stock Updated"), indicator="green"
    )
    return {"updated": updated, "skipped": skipped}