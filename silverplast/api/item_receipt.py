import frappe
from frappe.utils import getdate, nowdate, nowtime

def create_incoming_qc(doc, method):
    frappe.get_doc({
        "doctype": "Incoming QC",
        "source_receipt": doc.name,
        "item_code": doc.item_code,
        "item_type": doc.item_type,
        "qty_received": doc.qty_received,
        "posting_date": doc.posting_date,
        "backdate_reason": doc.backdate_reason,
        "remarks": doc.remarks
    }).insert(ignore_permissions=True)

def validate(self):
    today = getdate(nowdate())
    posting = getdate(self.posting_date)

    if posting < today:

        if not self.backdate_reason:
            frappe.throw("Backdate reason wajib diisi")

        current_time = nowtime()

        if "08:00:00" <= current_time <= "17:00:00":
            frappe.throw("Backdate hanya diperbolehkan di luar jam kerja (08:00 - 17:00)")