import frappe

@frappe.whitelist()
def accept_material_request(docname):

    doc = frappe.get_doc("Material Request Memo", docname)

    if doc.status == "Accepted":
        frappe.throw("Material Request sudah diproses")

    if not doc.kode_barang:
        frappe.throw("Kode Barang wajib diisi")

    if not doc.qty or doc.qty <= 0:
        frappe.throw("Qty harus lebih dari 0")

    gudang = frappe.get_doc("Gudang", doc.kode_barang)

    current_stock = gudang.stok_saat_ini_ton or 0

    if current_stock < doc.qty:
        frappe.throw(f"Stok tidak cukup. Stok tersedia: {current_stock}")

    new_stock = current_stock - doc.qty

    frappe.db.set_value(
        "Gudang",
        gudang.name,
        "stok_saat_ini_ton",
        new_stock
    )

    frappe.db.set_value(
        "Material Request Memo",
        docname,
        "status",
        "Accepted"
    )

    frappe.db.commit()

    return "OK"