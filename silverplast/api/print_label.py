import frappe

@frappe.whitelist()
def create_print_label(source_document):

    source = frappe.get_doc("Item Receipt Document", source_document)

    if frappe.db.exists("Print Label", {
        "source_document": source_document
    }):
        frappe.throw("Print Label already created")

    doc = frappe.get_doc({
        "doctype": "Print Label",
        "source_document": source.name,
        "item_code": source.item_code,
        "qty": source.qty
    })

    doc.insert(ignore_permissions=True)

    return doc.name