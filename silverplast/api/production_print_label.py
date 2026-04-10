import frappe

@frappe.whitelist()
def create_print_label(source_document):

    source = frappe.get_doc("Production Summary", source_document)

    if frappe.db.exists("Production Print Label", {
        "source_document": source_document
    }):
        frappe.throw("Print Label sudah dibuat")

    if source.qc_result not in ["Pass", "Conditional Pass"]:
        frappe.throw("Hanya bisa print untuk hasil QC Pass / Conditional Pass")

    item_code = source.item_code
    qty = source.qty or 0

    stok = frappe.db.get_value(
        "Stok",
        item_code,
        ["name", "qty_sesudah"],
        as_dict=True
    )

    if not stok:
        frappe.throw(f"Item {item_code} tidak ditemukan di Stok")

    qty_sebelum = stok.qty_sesudah or 0
    qty_sesudah = qty_sebelum + qty

    frappe.db.set_value(
        "Stok",
        stok.name,
        {
            "qty": qty_sesudah,
            "qty_sebelum": qty_sebelum,
            "qty_sesudah": qty_sesudah
        }
    )

    doc = frappe.get_doc({
        "doctype": "Production Print Label",
        "source_document": source.name,
        "item_code": item_code,
        "qty": qty
    })

    doc.insert(ignore_permissions=True)

    frappe.db.commit()

    return doc.name