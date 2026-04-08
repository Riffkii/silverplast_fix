import frappe

@frappe.whitelist()
def accept_material_request(docname):

    doc = frappe.get_doc("Material Request Memo", docname)

    if doc.status == "Accepted":
        frappe.throw("Material Request sudah diproses")

    if not doc.items:
        frappe.throw("Minimal 1 bahan harus diisi")

    for item in doc.items:

        if not item.kode_barang:
            frappe.throw("Kode Barang wajib diisi")

        if not item.qty or item.qty <= 0:
            frappe.throw(f"Qty untuk {item.kode_barang} harus lebih dari 0")

        gudang = frappe.get_doc("Gudang", item.kode_barang)

        current_stock = gudang.stok_saat_ini_ton or 0

        if current_stock < item.qty:
            frappe.throw(
                f"Stok {item.kode_barang} tidak cukup. Tersedia: {current_stock}"
            )

        new_stock = current_stock - item.qty

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

@frappe.whitelist()
def send_to_qc(production_id, qty):

    if not qty or float(qty) <= 0:
        frappe.throw("Qty harus lebih dari 0")

    existing = frappe.db.exists(
        "Production Incoming QC",
        {"source_production": production_id}
    )

    if existing:
        frappe.throw("Production sudah pernah dikirim ke QC")

    prod = frappe.get_doc("Production", production_id)

    doc = frappe.get_doc({
        "doctype": "Production Incoming QC",
        "source_production": prod.name,
        "item_code": prod.item_code,
        "qty": qty
    })

    doc.insert(ignore_permissions=True)

    frappe.db.set_value("Production", production_id, "qc_sent", 1)

    frappe.db.commit()

    return doc.name