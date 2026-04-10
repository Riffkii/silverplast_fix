import frappe
from datetime import datetime, timedelta

@frappe.whitelist()
def create_qc_checks_production(production_incoming_qc):

    source = frappe.get_doc("Production Incoming QC", production_incoming_qc)

    if frappe.db.exists("Production QCT", {
        "source_incoming_qc": production_incoming_qc
    }):
        return

    frappe.get_doc({
        "doctype": "Production QCT",
        "source_incoming_qc": source.name,
        "item_code": source.item_code,
        "qty": source.qty
    }).insert(ignore_permissions=True)

    frappe.get_doc({
        "doctype": "Production QCX",
        "source_incoming_qc": source.name,
        "item_code": source.item_code,
        "qty": source.qty
    }).insert(ignore_permissions=True)

    return "success"

def on_qc_update_production(doc, method):
    try_aggregate_production(doc.source_incoming_qc)

def get_qc_docs_production(source_incoming_qc):

    qct_name = frappe.db.get_value(
        "Production QCT",
        {"source_incoming_qc": source_incoming_qc},
        "name"
    )

    qcx_name = frappe.db.get_value(
        "Production QCX",
        {"source_incoming_qc": source_incoming_qc},
        "name"
    )

    if not qct_name or not qcx_name:
        return None, None

    return (
        frappe.get_doc("Production QCT", qct_name),
        frappe.get_doc("Production QCX", qcx_name)
    )

def try_aggregate_production(source_incoming_qc):

    if frappe.db.exists("Production Summary", {
        "source_qc": source_incoming_qc
    }):
        return

    qct, qcx = get_qc_docs_production(source_incoming_qc)

    if not qct or not qcx:
        return

    if not qct.qc_result or not qcx.qc_result:
        return

    evaluate_qc_production(source_incoming_qc)

@frappe.whitelist()
def evaluate_qc_production(source_incoming_qc):

    if frappe.db.exists("Production Summary", {
        "source_qc": source_incoming_qc
    }):
        return

    qct, qcx = get_qc_docs_production(source_incoming_qc)

    if not qct or not qcx:
        frappe.throw("QC document tidak lengkap")

    if not qct.qc_result or not qcx.qc_result:
        frappe.throw("QC belum lengkap")

    r1 = qct.qc_result
    r2 = qcx.qc_result

    qc_note = ""
    final_result = ""

    if r1 == "Pass" and r2 == "Pass":
        final_result = "Pass"

    elif (r1 == "Reject" and r2 == "Pass"):
        final_result = "Conditional Pass"
        qc_note = qct.qc_note or ""

    elif (r1 == "Pass" and r2 == "Reject"):
        final_result = "Conditional Pass"
        qc_note = qcx.qc_note or ""

    elif (r1 == "Reject" and r2 == "Reject"):
        final_result = "Scrap"

    stok = frappe.db.get_value(
        "Stok",
        qct.item_code,
        ["name", "rate"],
        as_dict=True
    )

    if not stok:
        frappe.throw(f"Item {qct.item_code} tidak ditemukan di Stok")

    rate = stok.rate or 0

    now = datetime.now()

    day_map = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }

    current_day = day_map[now.weekday()]

    schedules = frappe.get_all(
        "Job Schedule",
        filters={
            "status": "Active",
            "day": current_day
        },
        fields=["start_time", "end_time"]
    )

    if not schedules:
        frappe.throw("Tidak ada Job Schedule aktif hari ini")

    work_hours = 0

    for s in schedules:

        if not s.start_time or not s.end_time:
            continue

        start_time = s.start_time
        end_time = s.end_time

        if isinstance(start_time, timedelta):
            start_time = (datetime.min + start_time).time()

        if isinstance(end_time, timedelta):
            end_time = (datetime.min + end_time).time()

        dt_start = datetime.combine(now.date(), start_time)
        dt_end = datetime.combine(now.date(), end_time)

        if dt_end < dt_start:
            dt_end += timedelta(days=1)

        hours = (dt_end - dt_start).total_seconds() / 3600
        work_hours += hours

    total_rate = rate * work_hours

    doc = frappe.get_doc({
        "doctype": "Production Summary",
        "source_qc": source_incoming_qc,
        "item_code": qct.item_code,
        "qty": qct.qty,
        "qc_result": final_result,
        "qc_note": qc_note,
        "rate": rate,
        "work_hours": work_hours,
        "total_rate": total_rate
    })

    doc.insert(ignore_permissions=True)

    return doc.name