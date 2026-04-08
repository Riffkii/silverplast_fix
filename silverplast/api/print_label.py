import frappe

@frappe.whitelist()
def create_print_label(source_document):

    source = frappe.get_doc("Item Receipt Document", source_document)

    if frappe.db.exists("Print Label", {
        "source_document": source_document
    }):
        frappe.throw("Print Label already created")

    item_code = source.item_code
    qty = source.qty or 0
    item_type = source.item_type

    tipe_map = {
        "Bahan Baku": "Bahan Baku",
        "Additive": "Additive",
        "Bahan Penolong": "Bahan Penolong"
    }
    tipe_barang = tipe_map.get(item_type, "Bahan Baku")

    existing = frappe.db.get_value(
        "Gudang",
        {"kode_barang": item_code},
        ["name", "stok_saat_ini_ton"],
        as_dict=True
    )

    if existing:
        new_stock = (existing.stok_saat_ini_ton or 0) + qty

        frappe.db.set_value(
            "Gudang",
            existing.name,
            "stok_saat_ini_ton",
            new_stock
        )

    else:
        gudang = frappe.get_doc({
            "doctype": "Gudang",
            "kode_gudang": f"GDG-{item_code}",
            "nama_gudang": f"Gudang {item_code}",
            "level": "Gudang",
            "kode_barang": item_code,
            "tipe_barang": tipe_barang,
            "status": "Aktif",
            "kapasitas_ton": 100,
            "stok_saat_ini_ton": qty,
            "pic": "System",
            "telepon": "-"
        })

        gudang.insert(ignore_permissions=True)

    doc = frappe.get_doc({
        "doctype": "Print Label",
        "source_document": source.name,
        "item_code": item_code,
        "qty": qty
    })

    doc.insert(ignore_permissions=True)

    return doc.name