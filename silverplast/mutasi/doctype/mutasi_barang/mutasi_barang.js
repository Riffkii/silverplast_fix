// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mutasi Barang", {

    // ─────────────────────────────────────────────
    // Form refresh
    // ─────────────────────────────────────────────

    refresh(frm) {
        frm.trigger("set_status_indicator");
        frm.trigger("toggle_fields_by_type");
        frm.trigger("add_action_buttons");
        frm.trigger("show_flow_info");
    },

    // ─────────────────────────────────────────────
    // Saat jenis mutasi berubah
    // ─────────────────────────────────────────────

    mutation_type(frm) {
        frm.trigger("toggle_fields_by_type");
        // Reset gudang tujuan saat ganti tipe
        frm.set_value("destination_warehouse", "");
        frm.set_value("source_area_intern", "");
        frm.set_value("destination_area_intern", "");
    },

    // ─────────────────────────────────────────────
    // Saat gudang asal dipilih — filter area intern
    // ─────────────────────────────────────────────

    source_warehouse(frm) {
        // Filter area/rak agar hanya milik gudang asal
        frm.set_query("source_area_intern", function () {
            return {
                filters: {
                    parent_warehouse: frm.doc.source_warehouse,
                    status: "Aktif"
                }
            };
        });
        frm.set_query("destination_area_intern", function () {
            return {
                filters: {
                    parent_warehouse: frm.doc.source_warehouse,
                    status: "Aktif"
                }
            };
        });
    },

    // ─────────────────────────────────────────────
    // Helper: toggle field
    // ─────────────────────────────────────────────

    toggle_fields_by_type(frm) {
        const isAntar  = frm.doc.mutation_type === "Antar Gudang";
        const isIntern = frm.doc.mutation_type === "Intern Gudang";

        frm.toggle_display("destination_warehouse",  isAntar);
        frm.toggle_reqd("destination_warehouse",     isAntar);

        frm.toggle_display("source_area_intern",     isIntern);
        frm.toggle_display("destination_area_intern", isIntern);

        frm.toggle_display("section_verifikasi",     isAntar);
        frm.toggle_display("stock_entry_terima",     isAntar);
    },

    // ─────────────────────────────────────────────
    // Helper: status indicator berwarna
    // ─────────────────────────────────────────────

    set_status_indicator(frm) {
        const colorMap = {
            "Draft"     : "gray",
            "Dikirim"   : "orange",
            "Diterima"  : "blue",
            "Selesai"   : "green",
            "Dibatalkan": "red"
        };
        const color = colorMap[frm.doc.status] || "gray";
        frm.page.set_indicator(frm.doc.status || "Draft", color);
    },

    // ─────────────────────────────────────────────
    // Helper: info alur di atas form
    // ─────────────────────────────────────────────

    show_flow_info(frm) {
        frm.dashboard.reset();
        if (!frm.doc.mutation_type) return;

        const flows = {
            "Antar Gudang" : "Draft → <b>Dikirim</b> (submit) → <b>Diterima</b> → <b>Verifikasi Nota</b> → Selesai",
            "Intern Gudang": "Draft → <b>Submit</b> → Selesai (penempatan ulang langsung)"
        };

        const flow = flows[frm.doc.mutation_type];
        if (flow) {
            frm.dashboard.add_comment(
                `<span style="font-size:12px;color:#6c7680">Alur: </span>
                 <span style="font-size:12px">${flow}</span>`,
                "blue",
                true
            );
        }
    },

    // ─────────────────────────────────────────────
    // Tombol aksi sesuai status & tipe
    // ─────────────────────────────────────────────

    add_action_buttons(frm) {
        // Hanya tampilkan tombol jika dokumen sudah di-submit
        if (frm.doc.docstatus !== 1) return;

        const status = frm.doc.status;
        const type   = frm.doc.mutation_type;

        // ── Antar Gudang ──
        if (type === "Antar Gudang") {

            // Status Dikirim → tampilkan tombol Terima Barang
            if (status === "Dikirim") {
                frm.add_custom_button(__("Terima Barang"), function () {
                    frappe.confirm(
                        __("Konfirmasi penerimaan barang di gudang tujuan?"),
                        function () {
                            frappe.call({
                                method: "silverplast.api.mutasi_barang.terima_barang",
                                args: { docname: frm.doc.name },
                                callback(r) {
                                    if (!r.exc) frm.reload_doc();
                                }
                            });
                        }
                    );
                }, __("Aksi")).addClass("btn-primary");
            }

            // Status Diterima → tampilkan tombol Verifikasi Nota
            if (status === "Diterima") {
                frm.add_custom_button(__("Verifikasi Nota"), function () {
                    frappe.confirm(
                        __("Konfirmasi verifikasi nota mutasi ini?"),
                        function () {
                            frappe.call({
                                method: "silverplast.api.mutasi_barang.verifikasi_nota",
                                args: { docname: frm.doc.name },
                                callback(r) {
                                    if (!r.exc) frm.reload_doc();
                                }
                            });
                        }
                    );
                }, __("Aksi")).addClass("btn-success");
            }
        }

        // ── Tombol Print Nota (semua status setelah Draft) ──
        if (status !== "Draft" && status !== "Dibatalkan") {
            frm.add_custom_button(__("Cetak Nota Mutasi"), function () {
                frappe.set_route("print", "Mutasi Barang", frm.doc.name);
            }, __("Aksi"));
        }

        // ── Lihat Stock Entry ──
        if (frm.doc.stock_entry_kirim) {
            frm.add_custom_button(__("Stock Entry Kirim"), function () {
                frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry_kirim);
            }, __("Referensi"));
        }
        if (frm.doc.stock_entry_terima) {
            frm.add_custom_button(__("Stock Entry Terima"), function () {
                frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry_terima);
            }, __("Referensi"));
        }
    },
});

// ─────────────────────────────────────────────
// Child table: Mutasi Barang Item
// ─────────────────────────────────────────────

frappe.ui.form.on("Mutasi Barang Item", {

    item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        // Auto-fill UOM dari item master
        frappe.db.get_value("Item", row.item_code, "stock_uom", function (r) {
            if (r && r.stock_uom) {
                frappe.model.set_value(cdt, cdn, "uom", r.stock_uom);
            }
        });

        // Cek stok tersedia di gudang asal
        if (frm.doc.source_warehouse) {
            frappe.call({
                method: "silverplast.api.mutasi_barang.get_stock_available",
                args: {
                    item_code : row.item_code,
                    warehouse : frm.doc.source_warehouse
                },
                callback(r) {
                    if (r.message !== undefined) {
                        frappe.model.set_value(cdt, cdn, "catatan_item",
                            `Stok tersedia: ${r.message} ${row.uom || "Kg"}`
                        );
                    }
                }
            });
        }
    },

    qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.qty || row.qty <= 0) {
            frappe.model.set_value(cdt, cdn, "qty", 0);
            frappe.msgprint({
                message: __("QTY harus lebih besar dari 0."),
                indicator: "red"
            });
        }
    }
});