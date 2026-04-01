# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now_datetime


class MutasiBarang(Document):

    # ─────────────────────────────────────────────
    # Lifecycle hooks
    # ─────────────────────────────────────────────

    def validate(self):
        self.validate_gudang()
        self.validate_items()
        self.validate_backdate()
        self.validate_status()

    def on_submit(self):
        """
        Submit = Nota Mutasi resmi dibuat.
        - Antar Gudang : status → 'Dikirim', buat Stock Entry pengurangan gudang asal
        - Intern Gudang: status → 'Selesai', langsung pindah stok dalam gudang
        """
        if self.mutation_type == "Antar Gudang":
            self._kirim_barang()
        else:
            self._selesaikan_intern()

    def on_cancel(self):
        """Batalkan Stock Entry terkait jika masih bisa dibatalkan."""
        self._cancel_stock_entries()
        self.db_set("status", "Dibatalkan")

    # ─────────────────────────────────────────────
    # Validasi
    # ─────────────────────────────────────────────

    def validate_gudang(self):
        """Pastikan gudang asal dan tujuan tidak sama."""
        if self.mutation_type == "Antar Gudang":
            if not self.destination_warehouse:
                frappe.throw(_("Gudang Tujuan wajib diisi untuk Mutasi Antar Gudang."))

            if self.source_warehouse == self.destination_warehouse:
                frappe.throw(
                    _("Gudang Asal dan Gudang Tujuan tidak boleh sama.")
                )

        if self.mutation_type == "Intern Gudang":
            if (self.source_area_intern and self.destination_area_intern
                    and self.source_area_intern == self.destination_area_intern):
                frappe.throw(
                    _("Area/Rak Asal dan Tujuan tidak boleh sama.")
                )

    def validate_items(self):
        """Pastikan ada barang dan qty > 0."""
        if not self.items:
            frappe.throw(_("Daftar Barang tidak boleh kosong."))

        for i, row in enumerate(self.items, start=1):
            if not row.qty or row.qty <= 0:
                frappe.throw(
                    _("Baris {0}: QTY harus lebih besar dari 0.").format(i)
                )

    def validate_backdate(self):
        """
        Sesuai pola item_receipt.py — backdate_reason wajib diisi
        jika tanggal bukan hari ini.
        """
        if not self.tanggal_mutasi:
            return

        today = getdate(nowdate())
        posting = getdate(self.tanggal_mutasi)

        if posting < today and not self.backdate_reason:
            frappe.throw(
                _("Alasan Backdate wajib diisi karena tanggal mutasi bukan hari ini.")
            )

    def validate_status(self):
        """Status tidak boleh diubah manual lewat form."""
        if self.is_new():
            self.status = "Draft"

    # ─────────────────────────────────────────────
    # Aksi: Antar Gudang — Kirim
    # ─────────────────────────────────────────────

    def _kirim_barang(self):
        """
        Diagram: Gudang Asal → Pengiriman Barang → update stock (Data Stock)
        Buat Stock Entry 'Material Transfer Out' — stok gudang asal berkurang.
        """
        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type  = "Material Issue"
        se.company           = frappe.defaults.get_user_default("Company")
        se.posting_date      = self.tanggal_mutasi
        se.posting_time      = self.posting_time
        se.custom_ref_mutasi = self.name  # field custom jika ada
        se.remarks           = f"Pengiriman mutasi {self.name} dari {self.source_warehouse}"

        for row in self.items:
            se.append("items", {
                "item_code"  : row.item_code,
                "qty"        : row.qty,
                "uom"        : row.uom or "Kg",
                "s_warehouse": self.source_warehouse,
                "batch_no"   : row.batch_no or None,
            })

        se.insert(ignore_permissions=True)
        se.submit()

        # Simpan referensi ke dokumen mutasi
        self.db_set("stock_entry_kirim", se.name)
        self.db_set("status", "Dikirim")
        self.db_set("dikirim_oleh", frappe.session.user)
        self.db_set("tanggal_kirim", now_datetime())

        frappe.msgprint(
            _("Barang telah dikirim. Stock Entry {0} dibuat.").format(
                frappe.bold(se.name)
            ),
            title=_("Pengiriman Berhasil"),
            indicator="orange"
        )

    # ─────────────────────────────────────────────
    # Aksi: Antar Gudang — Terima
    # ─────────────────────────────────────────────

    def terima_barang(self):
        """
        Diagram: Gudang Tujuan → Penerimaan Barang → update stock
        Buat Stock Entry Material Receipt — stok gudang tujuan bertambah.
        Dipanggil dari tombol 'Terima Barang' di form.
        """
        if self.status != "Dikirim":
            frappe.throw(
                _("Hanya bisa menerima barang yang berstatus 'Dikirim'. "
                  "Status saat ini: {0}").format(self.status)
            )

        se = frappe.new_doc("Stock Entry")
        se.stock_entry_type = "Material Receipt"
        se.company          = frappe.defaults.get_user_default("Company")
        se.posting_date     = nowdate()
        se.posting_time     = now_datetime().strftime("%H:%M:%S")
        se.remarks          = f"Penerimaan mutasi {self.name} di {self.destination_warehouse}"

        for row in self.items:
            se.append("items", {
                "item_code"  : row.item_code,
                "qty"        : row.qty,
                "uom"        : row.uom or "Kg",
                "t_warehouse": self.destination_warehouse,
                "batch_no"   : row.batch_no or None,
            })

        se.insert(ignore_permissions=True)
        se.submit()

        self.db_set("stock_entry_terima", se.name)
        self.db_set("status", "Diterima")
        self.db_set("diterima_oleh", frappe.session.user)
        self.db_set("tanggal_terima", now_datetime())

        frappe.msgprint(
            _("Barang diterima. Stock Entry {0} dibuat.").format(
                frappe.bold(se.name)
            ),
            title=_("Penerimaan Berhasil"),
            indicator="blue"
        )

    # ─────────────────────────────────────────────
    # Aksi: Antar Gudang — Verifikasi Nota
    # ─────────────────────────────────────────────

    def verifikasi_nota(self):
        """
        Diagram: Gudang Tujuan → Verifikasi Nota → End
        Status berubah menjadi Selesai.
        """
        if self.status != "Diterima":
            frappe.throw(
                _("Hanya bisa verifikasi nota yang berstatus 'Diterima'. "
                  "Status saat ini: {0}").format(self.status)
            )

        self.db_set("status", "Selesai")
        self.db_set("verified_by", frappe.session.user)
        self.db_set("tanggal_verifikasi", now_datetime())

        frappe.msgprint(
            _("Nota Mutasi {0} telah diverifikasi. Mutasi selesai.").format(
                frappe.bold(self.name)
            ),
            title=_("Verifikasi Berhasil"),
            indicator="green"
        )

    # ─────────────────────────────────────────────
    # Aksi: Intern Gudang — Selesaikan
    # ─────────────────────────────────────────────

    def _selesaikan_intern(self):
        """
        Diagram: Admin Gudang buat nota → update Data Stock
                 Staff Gudang → Penempatan Ulang Barang → End

        Pindah stok antar area/rak dalam gudang yang sama
        menggunakan Material Transfer ERPNext.
        """
        # Jika ada area/rak sumber dan tujuan, buat Transfer antar area
        if self.source_area_intern and self.destination_area_intern:
            se = frappe.new_doc("Stock Entry")
            se.stock_entry_type = "Material Transfer"
            se.company          = frappe.defaults.get_user_default("Company")
            se.posting_date     = self.tanggal_mutasi
            se.posting_time     = self.posting_time
            se.remarks          = (
                f"Mutasi intern {self.name}: "
                f"{self.source_area_intern} → {self.destination_area_intern}"
            )

            for row in self.items:
                se.append("items", {
                    "item_code"  : row.item_code,
                    "qty"        : row.qty,
                    "uom"        : row.uom or "Kg",
                    "s_warehouse": row.source_area or self.source_area_intern,
                    "t_warehouse": row.destination_area or self.destination_area_intern,
                    "batch_no"   : row.batch_no or None,
                })

            se.insert(ignore_permissions=True)
            se.submit()

            self.db_set("stock_entry_kirim", se.name)

        self.db_set("status", "Selesai")
        self.db_set("verified_by", frappe.session.user)
        self.db_set("tanggal_verifikasi", now_datetime())

        frappe.msgprint(
            _("Penempatan ulang barang selesai. Mutasi intern {0} telah diproses.").format(
                frappe.bold(self.name)
            ),
            title=_("Mutasi Intern Selesai"),
            indicator="green"
        )

    # ─────────────────────────────────────────────
    # Helper: Batalkan Stock Entry
    # ─────────────────────────────────────────────

    def _cancel_stock_entries(self):
        """Batalkan semua Stock Entry yang dibuat oleh mutasi ini."""
        for field in ("stock_entry_kirim", "stock_entry_terima"):
            se_name = self.get(field)
            if se_name and frappe.db.exists("Stock Entry", se_name):
                se = frappe.get_doc("Stock Entry", se_name)
                if se.docstatus == 1:
                    se.cancel()
                    frappe.msgprint(
                        _("Stock Entry {0} dibatalkan.").format(frappe.bold(se_name))
                    )