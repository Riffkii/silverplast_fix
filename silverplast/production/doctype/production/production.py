# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta

class Production(Document):

	def validate(self):

		now = datetime.now()

		if self.material_request:

			doc_mr = frappe.get_doc("Material Request Memo", self.material_request)

			self.item_code = doc_mr.barang_jadi

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
		current_time = now.time()

		schedules = frappe.get_all(
			"Job Schedule",
			filters={
				"status": "Active",
				"day": current_day
			},
			fields=["start_time", "end_time"]
		)

		valid = False

		for s in schedules:

			if not s.start_time or not s.end_time:
				continue

			start_time = s.start_time
			end_time = s.end_time

			if isinstance(start_time, timedelta):
				start_time = (datetime.min + start_time).time()

			if isinstance(end_time, timedelta):
				end_time = (datetime.min + end_time).time()

			if start_time <= current_time <= end_time:
				valid = True
				break

		if not valid:
			frappe.throw("Tidak ada jadwal produksi aktif saat ini")

	def after_insert(self):

		if not self.material_request:
			frappe.throw("Material Request wajib diisi")

		doc_mr = frappe.get_doc("Material Request Memo", self.material_request)

		if doc_mr.status == "Processed":
			frappe.throw("Material Request sudah dipakai")

		if doc_mr.status != "Accepted":
			frappe.throw("Material Request harus status Accepted")

		frappe.db.set_value(
            "Material Request Memo",
            doc_mr.name,
            "status",
            "Processed"
        )
