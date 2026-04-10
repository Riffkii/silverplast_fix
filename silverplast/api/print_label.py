import frappe
from silverplast.inventory.doctype.stok.stok import catat_transaksi_stok

@frappe.whitelist()
def create_print_label(source_document):

    source = frappe.get_doc("Item Receipt Document", source_document)

    if frappe.db.exists("Print Label", {
        "source_document": source_document
    }):
        frappe.throw("Print Label already created")

    if not source.item_code:
        frappe.throw("Item Code wajib diisi")

    if not source.qty or source.qty <= 0:
        frappe.throw("Quantity harus lebih dari 0")

    if not source.gudang:
        frappe.throw("Gudang wajib dipilih")

    item_code = source.item_code
    item_name = item_code
    qty = source.qty
    item_type = source.item_type
    gudang = source.gudang

    tipe_map = {
        "Bahan Baku": "Bahan Baku",
        "Additive": "Additive",
        "Bahan Penolong": "Bahan Penolong"
    }
    tipe_barang = tipe_map.get(item_type, "Bahan Baku")

    catat_transaksi_stok(
        item_code=item_code,
        item_name=item_name,
        qty=qty,
        gudang=gudang,
        tipe_transaksi="Masuk",
        ref_doctype="Item Receipt Document",
        ref_docname=source.name,
        uom="Kg",
        keterangan="Auto dari Item Receipt",
        tipe_barang=tipe_barang
    )

    doc = frappe.get_doc({
        "doctype": "Print Label",
        "source_document": source.name,
        "item_code": item_code,
        "qty": qty
    })

    doc.insert(ignore_permissions=True)

    return doc.name