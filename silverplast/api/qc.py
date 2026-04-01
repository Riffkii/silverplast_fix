import frappe

@frappe.whitelist()
def create_qc_checks(incoming_qc):

    source = frappe.get_doc("Incoming QC", incoming_qc)

    if frappe.db.exists("QCT", {"source_incoming_qc": incoming_qc}):
        frappe.throw("QC sudah pernah dibuat")

    frappe.get_doc({
        "doctype": "QCT",
        "source_incoming_qc": source.name,
        "item_code": source.item_code,
        "item_type": source.item_type,
        "qty": source.qty_received
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype": "QCE",
        "source_incoming_qc": source.name,
        "item_code": source.item_code,
        "item_type": source.item_type,
        "qty": source.qty_received
    }).insert(ignore_permissions=True)

    return "success"

def on_qc_update(doc, method):
    try_aggregate(doc.source_incoming_qc)

def try_aggregate(source_incoming_qc):

    if frappe.db.exists("Item Receipt Document", {
        "source_qc": source_incoming_qc
    }):
        return

    qct, qce = get_qc_docs(source_incoming_qc)

    if not qct or not qce:
        return

    if not qct.qc_result or not qce.qc_result:
        return

    return evaluate_qc(source_incoming_qc)

def get_qc_docs(source_incoming_qc):
    qct_name = frappe.db.get_value("QCT", {
        "source_incoming_qc": source_incoming_qc
    }, "name")

    qce_name = frappe.db.get_value("QCE", {
        "source_incoming_qc": source_incoming_qc
    }, "name")

    if not qct_name or not qce_name:
        return None, None

    qct = frappe.get_doc("QCT", qct_name)
    qce = frappe.get_doc("QCE", qce_name)

    return qct, qce

@frappe.whitelist()
def evaluate_qc(source_incoming_qc):

    if frappe.db.exists("Item Receipt Document", {
        "source_qc": source_incoming_qc
    }):
        return

    qct, qce = get_qc_docs(source_incoming_qc)

    if not qct or not qce:
        frappe.throw("QC document tidak lengkap")

    if not qct.qc_result or not qce.qc_result:
        frappe.throw("QC belum lengkap")

    r1 = qct.qc_result
    r2 = qce.qc_result

    qc_note = ""
    final_result = ""

    if r1 == "Pass" and r2 == "Pass":
        final_result = "Pass"

    elif (r1 == "Reject" and r2 == "Pass"):
        final_result = "Conditional Pass"
        qc_note = qct.qc_note or ""

    elif (r1 == "Pass" and r2 == "Reject"):
        final_result = "Conditional Pass"
        qc_note = qce.qc_note or ""

    elif (r1 == "Reject" and r2 == "Reject"):
        final_result = "Reject"

    if final_result == "Reject":
        frappe.throw("QC Failed: kedua QC Reject")

    doc = frappe.get_doc({
        "doctype": "Item Receipt Document",
        "source_qc": source_incoming_qc,
        "item_code": qct.item_code,
        "item_type": qct.item_type,
        "qty": qct.qty,
        "qc_result": final_result,
        "qc_note": qc_note
    })

    doc.insert(ignore_permissions=True)

    return doc.name