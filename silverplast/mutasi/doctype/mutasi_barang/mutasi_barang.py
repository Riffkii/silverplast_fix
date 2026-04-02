# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, now_datetime


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
    # Tidak buat Stock Entry (tidak pakai ERPNext)
    # Cukup update status dan catat referensi

    def _kirim_barang(self):
        # Buat nomor referensi internal
        ref_no = f"KIRIM-{self.name}-{nowdate()}"

        self.db_set("stock_entry_kirim", ref_no)
        self.db_set("status", "Dikirim")
        self.db_set("dikirim_oleh", frappe.session.user)
        self.db_set("tanggal_kirim", now_datetime())

        # Update stok gudang asal (kurangi)
        self._update_stok_gudang(
            kode_gudang=self.source_warehouse,
            tipe="keluar"
        )

        frappe.msgprint(
            _("Barang dikirim. Ref: {0}").format(frappe.bold(ref_no)),
            title=_("Pengiriman Berhasil"),
            indicator="orange"
        )

    # ── Antar Gudang: Terima ──────────────────────

    def terima_barang(self):
        if self.status != "Dikirim":
            frappe.throw(
                _("Status harus 'Dikirim'. Status saat ini: {0}").format(self.status)
            )

        ref_no = f"TERIMA-{self.name}-{nowdate()}"

        self.db_set("stock_entry_terima", ref_no)
        self.db_set("status", "Diterima")
        self.db_set("diterima_oleh", frappe.session.user)
        self.db_set("tanggal_terima", now_datetime())

        # Update stok gudang tujuan (tambah)
        self._update_stok_gudang(
            kode_gudang=self.destination_warehouse,
            tipe="masuk"
        )

        frappe.msgprint(
            _("Barang diterima. Ref: {0}").format(frappe.bold(ref_no)),
            title=_("Penerimaan Berhasil"),
            indicator="blue"
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

        frappe.msgprint(
            _("Nota {0} diverifikasi. Mutasi selesai.").format(frappe.bold(self.name)),
            title=_("Verifikasi Berhasil"),
            indicator="green"
        )

    # ── Intern Gudang ─────────────────────────────

    def _selesaikan_intern(self):
        ref_no = f"INTERN-{self.name}-{nowdate()}"

        self.db_set("stock_entry_kirim", ref_no)
        self.db_set("status", "Selesai")
        self.db_set("verified_by", frappe.session.user)
        self.db_set("tanggal_verifikasi", now_datetime())

        frappe.msgprint(
            _("Mutasi intern {0} selesai. Barang siap dipindahkan.").format(
                frappe.bold(self.name)
            ),
            title=_("Selesai"),
            indicator="green"
        )

    # ── Cancel ────────────────────────────────────

    def _batalkan_mutasi(self):
        # Kembalikan stok jika sudah sempat dikirim/diterima
        if self.status == "Dikirim":
            # Kembalikan stok gudang asal
            self._update_stok_gudang(self.source_warehouse, "masuk")

        elif self.status in ("Diterima", "Selesai"):
            # Kembalikan stok gudang asal dan kurangi gudang tujuan
            self._update_stok_gudang(self.source_warehouse, "masuk")
            if self.destination_warehouse:
                self._update_stok_gudang(self.destination_warehouse, "keluar")

        frappe.msgprint(
            _("Mutasi {0} dibatalkan.").format(frappe.bold(self.name))
        )

    # ── Update stok di DocType Gudang ─────────────

    def _update_stok_gudang(self, kode_gudang, tipe):
        """
        Update stok_saat_ini_ton di Gudang berdasarkan
        total qty item yang dimutasi (konversi Kg -> Ton).
        tipe: 'masuk' atau 'keluar'
        """
        if not kode_gudang:
            return

        if not frappe.db.exists("Gudang", kode_gudang):
            return

        # Hitung total qty dari semua item dalam dokumen ini
        total_kg = sum(row.qty for row in self.items if row.qty)
        total_ton = round(total_kg / 1000, 3)

        stok_saat_ini = frappe.db.get_value(
            "Gudang", kode_gudang, "stok_saat_ini_ton"
        ) or 0

        if tipe == "masuk":
            stok_baru = stok_saat_ini + total_ton
        else:
            stok_baru = max(stok_saat_ini - total_ton, 0)

        frappe.db.set_value("Gudang", kode_gudang, "stok_saat_ini_ton",
                            round(stok_baru, 3))