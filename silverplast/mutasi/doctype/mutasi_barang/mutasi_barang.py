# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now_datetime

# Import fungsi utilitas stok custom
from silverplast.inventory.doctype.stok.stok import catat_transaksi_stok


class MutasiBarang(Document):

    def validate(self):
        self.validate_gudang()
        self.validate_items()
        self.validate_backdate()
        if self.is_new():
            self.status = "Draft"

    def on_submit(self):
        if self.mutation_type == "Antar Gudang":
            self._kirim_barang()
        else:
            self._selesaikan_intern()

    def on_cancel(self):
        self._batalkan_mutasi()
        self.db_set("status", "Dibatalkan")

    # ── Validasi ──────────────────────────────────

    def validate_gudang(self):
        if self.mutation_type == "Antar Gudang":
            if not self.destination_warehouse:
                frappe.throw(_("Gudang Tujuan wajib diisi untuk Mutasi Antar Gudang."))
            if self.source_warehouse == self.destination_warehouse:
                frappe.throw(_("Gudang Asal dan Gudang Tujuan tidak boleh sama."))

        if self.mutation_type == "Intern Gudang":
            if (self.source_area_intern and self.destination_area_intern
                    and self.source_area_intern == self.destination_area_intern):
                frappe.throw(_("Area/Rak Asal dan Tujuan tidak boleh sama."))

    def validate_items(self):
        if not self.items:
            frappe.throw(_("Daftar Barang tidak boleh kosong."))
        for i, row in enumerate(self.items, start=1):
            if not row.qty or row.qty <= 0:
                frappe.throw(
                    _("Baris {0}: QTY harus lebih besar dari 0.").format(i)
                )

    def validate_backdate(self):
        if not self.tanggal_mutasi:
            return
        if getdate(self.tanggal_mutasi) < getdate(nowdate()) and not self.backdate_reason:
            frappe.throw(
                _("Alasan Backdate wajib diisi karena tanggal mutasi bukan hari ini.")
            )

    # ── Antar Gudang: Kirim ───────────────────────

    def _kirim_barang(self):
        """
        BPMN: Pengiriman Barang → update stok (Data Stock)
        Catat transaksi Pindah Keluar untuk setiap item.
        """
        stok_refs = []

        for row in self.items:
            ref = catat_transaksi_stok(
                item_code    = row.item_code,
                item_name    = row.item_name or row.item_code,
                qty          = row.qty,
                gudang       = self.source_warehouse,
                tipe_transaksi = "Pindah Keluar",
                ref_doctype  = "Mutasi Barang",
                ref_docname  = self.name,
                batch_no     = row.batch_no,
                uom          = row.uom or "Kg",
                keterangan   = f"Keluar ke {self.destination_warehouse}"
            )
            stok_refs.append(ref)

        ref_gabung = ", ".join(stok_refs)
        self.db_set("stock_entry_kirim", ref_gabung)
        self.db_set("status", "Dikirim")
        self.db_set("dikirim_oleh", frappe.session.user)
        self.db_set("tanggal_kirim", now_datetime())

        frappe.msgprint(
            _("Barang dikirim. {0} transaksi stok dicatat.").format(len(stok_refs)),
            title=_("Pengiriman Berhasil"), indicator="orange"
        )

    # ── Antar Gudang: Terima ──────────────────────

    def terima_barang(self):
        """
        BPMN: Penerimaan Barang → update stok
        Catat transaksi Pindah Masuk untuk setiap item.
        """
        if self.status != "Dikirim":
            frappe.throw(
                _("Status harus 'Dikirim'. Status saat ini: {0}").format(self.status)
            )

        stok_refs = []

        for row in self.items:
            ref = catat_transaksi_stok(
                item_code    = row.item_code,
                item_name    = row.item_name or row.item_code,
                qty          = row.qty,
                gudang       = self.destination_warehouse,
                tipe_transaksi = "Pindah Masuk",
                ref_doctype  = "Mutasi Barang",
                ref_docname  = self.name,
                batch_no     = row.batch_no,
                uom          = row.uom or "Kg",
                keterangan   = f"Masuk dari {self.source_warehouse}"
            )
            stok_refs.append(ref)

        ref_gabung = ", ".join(stok_refs)
        self.db_set("stock_entry_terima", ref_gabung)
        self.db_set("status", "Diterima")
        self.db_set("diterima_oleh", frappe.session.user)
        self.db_set("tanggal_terima", now_datetime())

        frappe.msgprint(
            _("Barang diterima. {0} transaksi stok dicatat.").format(len(stok_refs)),
            title=_("Penerimaan Berhasil"), indicator="blue"
        )

    # ── Antar Gudang: Verifikasi ──────────────────

    def verifikasi_nota(self):
        if self.status != "Diterima":
            frappe.throw(
                _("Status harus 'Diterima'. Status saat ini: {0}").format(self.status)
            )

        self.db_set("status", "Selesai")
        self.db_set("verified_by", frappe.session.user)
        self.db_set("tanggal_verifikasi", now_datetime())

        from silverplast.inventory.doctype.gudang.gudang import Gudang
        Gudang.update_stok_gudang(self.source_warehouse)
        Gudang.update_stok_gudang(self.destination_warehouse)

        frappe.msgprint(
            _("Nota {0} diverifikasi. Mutasi selesai.").format(frappe.bold(self.name)),
            title=_("Verifikasi Berhasil"), indicator="green"
        )

    # ── Intern Gudang ─────────────────────────────

    def _selesaikan_intern(self):
        """
        BPMN: Pembuatan Nota → Data Stock → Penempatan Ulang
        Catat Keluar dari area asal dan Masuk ke area tujuan.
        """
        stok_refs = []

        for row in self.items:
            gudang_asal   = row.source_area      or self.source_area_intern      or self.source_warehouse
            gudang_tujuan = row.destination_area or self.destination_area_intern or self.source_warehouse

            # Keluar dari area asal
            ref_keluar = catat_transaksi_stok(
                item_code    = row.item_code,
                item_name    = row.item_name or row.item_code,
                qty          = row.qty,
                gudang       = gudang_asal,
                tipe_transaksi = "Pindah Keluar",
                ref_doctype  = "Mutasi Barang",
                ref_docname  = self.name,
                batch_no     = row.batch_no,
                uom          = row.uom or "Kg",
                keterangan   = f"Intern: pindah ke {gudang_tujuan}"
            )

            # Masuk ke area tujuan
            ref_masuk = catat_transaksi_stok(
                item_code    = row.item_code,
                item_name    = row.item_name or row.item_code,
                qty          = row.qty,
                gudang       = gudang_tujuan,
                tipe_transaksi = "Pindah Masuk",
                ref_doctype  = "Mutasi Barang",
                ref_docname  = self.name,
                batch_no     = row.batch_no,
                uom          = row.uom or "Kg",
                keterangan   = f"Intern: dari {gudang_asal}"
            )

            stok_refs.extend([ref_keluar, ref_masuk])

        self.db_set("stock_entry_kirim", ", ".join(stok_refs[:3]))  # simpan sebagian ref
        self.db_set("status", "Selesai")
        self.db_set("verified_by", frappe.session.user)
        self.db_set("tanggal_verifikasi", now_datetime())

        frappe.msgprint(
            _("Mutasi intern {0} selesai.").format(frappe.bold(self.name)),
            title=_("Selesai"), indicator="green"
        )

    # ── Cancel: balikkan transaksi stok ──────────

    def _batalkan_mutasi(self):
        """
        Tandai semua transaksi Stok terkait sebagai Dibatalkan.
        """
        stok_docs = frappe.db.get_all(
            "Stok",
            filters={"ref_docname": self.name, "status": "Aktif"},
            fields=["name"]
        )

        for s in stok_docs:
            frappe.db.set_value("Stok", s.name, "status", "Dibatalkan")

        frappe.msgprint(
            _("Mutasi {0} dibatalkan. {1} transaksi stok dibatalkan.").format(
                frappe.bold(self.name), len(stok_docs)
            )
        )