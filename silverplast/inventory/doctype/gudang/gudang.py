# Copyright (c) 2026, P79 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class Gudang(Document):

    # ─────────────────────────────────────────────
    # Lifecycle hooks
    # ─────────────────────────────────────────────

    def validate(self):
        self.validate_hierarchy()
        self.validate_kapasitas()

    def before_save(self):
        self.kode_gudang = self.kode_gudang.upper().strip()

    # ─────────────────────────────────────────────
    # Validasi (WH-01)
    # ─────────────────────────────────────────────

    def validate_hierarchy(self):
        """
        WH-01: Pastikan hierarki Gudang > Area > Rak konsisten.
        """
        if self.level == "Gudang":
            if self.induk_gudang:
                frappe.throw(
                    _("Level 'Gudang' tidak boleh memiliki Induk Gudang.")
                )
            return

        if not self.induk_gudang:
            frappe.throw(
                _("Level '{0}' wajib memiliki Induk Gudang.").format(self.level)
            )

        if self.induk_gudang == self.kode_gudang:
            frappe.throw(_("Induk Gudang tidak boleh merujuk ke dirinya sendiri."))

        parent_level = frappe.db.get_value("Gudang", self.induk_gudang, "level")

        if not parent_level:
            frappe.throw(
                _("Induk Gudang '{0}' tidak ditemukan.").format(self.induk_gudang)
            )

        if self.level == "Area" and parent_level != "Gudang":
            frappe.throw(
                _("Induk dari 'Area' harus berupa 'Gudang', "
                  "bukan '{0}'.").format(parent_level)
            )

        if self.level == "Rak" and parent_level != "Area":
            frappe.throw(
                _("Induk dari 'Rak' harus berupa 'Area', "
                  "bukan '{0}'.").format(parent_level)
            )

    def validate_kapasitas(self):
        if self.kapasitas_ton and self.kapasitas_ton <= 0:
            frappe.throw(_("Kapasitas (Ton) harus lebih besar dari 0."))

    # ─────────────────────────────────────────────
    # Update stok (dipanggil dari Mutasi Barang)
    # ─────────────────────────────────────────────

    @staticmethod
    def update_stok_gudang(kode_gudang):
        """
        FIX Bug 2: Hitung ulang stok aktual dari semua Mutasi Barang
        yang sudah Selesai, lalu simpan ke stok_saat_ini_ton.

        Dipanggil setiap kali Mutasi Barang berubah status.
        """
        if not frappe.db.exists("Gudang", kode_gudang):
            return

        # Hitung total masuk (sebagai gudang tujuan)
        masuk = frappe.db.sql("""
            SELECT COALESCE(SUM(mi.qty), 0) AS total
            FROM `tabMutasi Barang` m
            JOIN `tabMutasi Barang Item` mi ON mi.parent = m.name
            WHERE
                m.destination_warehouse = %(gudang)s
                AND m.status = 'Selesai'
                AND m.docstatus = 1
        """, {"gudang": kode_gudang}, as_dict=True)

        # Hitung total keluar (sebagai gudang asal)
        keluar = frappe.db.sql("""
            SELECT COALESCE(SUM(mi.qty), 0) AS total
            FROM `tabMutasi Barang` m
            JOIN `tabMutasi Barang Item` mi ON mi.parent = m.name
            WHERE
                m.source_warehouse = %(gudang)s
                AND m.mutation_type = 'Antar Gudang'
                AND m.status = 'Selesai'
                AND m.docstatus = 1
        """, {"gudang": kode_gudang}, as_dict=True)

        total_masuk  = (masuk[0].total  if masuk  else 0) or 0
        total_keluar = (keluar[0].total if keluar else 0) or 0

        # Konversi Kg → Ton (1 ton = 1000 Kg)
        stok_ton = (total_masuk - total_keluar) / 1000

        frappe.db.set_value("Gudang", kode_gudang, "stok_saat_ini_ton",
                            round(stok_ton, 3))