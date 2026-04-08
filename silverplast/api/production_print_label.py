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

    existing = frappe.db.get_value(
        "Gudang",
        {"kode_gudang": item_code},
        ["name", "stok_saat_ini_ton"],
        as_dict=True
    )

    if not existing:
        frappe.throw(f"Barang {item_code} tidak ditemukan di Gudang")

    new_stock = (existing.stok_saat_ini_ton or 0) + qty

    frappe.db.set_value(
        "Gudang",
        existing.name,
        "stok_saat_ini_ton",
        new_stock
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