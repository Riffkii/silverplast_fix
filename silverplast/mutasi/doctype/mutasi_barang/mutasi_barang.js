// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mutasi Barang", {

    refresh(frm) {
        frm.trigger("set_status_indicator");
        frm.trigger("toggle_fields_by_type");
        frm.trigger("add_action_buttons");
        frm.trigger("show_flow_info");
    },

    mutation_type(frm) {
        frm.trigger("toggle_fields_by_type");
        frm.set_value("destination_warehouse", "");
        frm.set_value("source_area_intern", "");
        frm.set_value("destination_area_intern", "");
    },

    source_warehouse(frm) {
        // Filter area/rak intern agar hanya milik gudang asal
        frm.set_query("source_area_intern", () => ({
            filters: { induk_gudang: frm.doc.source_warehouse, status: "Aktif" }
        }));
        frm.set_query("destination_area_intern", () => ({
            filters: { induk_gudang: frm.doc.source_warehouse, status: "Aktif" }
        }));
    },

    toggle_fields_by_type(frm) {
        const isAntar  = frm.doc.mutation_type === "Antar Gudang";
        const isIntern = frm.doc.mutation_type === "Intern Gudang";

        frm.toggle_display("destination_warehouse",   isAntar);
        frm.toggle_reqd("destination_warehouse",      isAntar);
        frm.toggle_display("source_area_intern",      isIntern);
        frm.toggle_display("destination_area_intern", isIntern);
        frm.toggle_display("section_verifikasi",      isAntar);
        frm.toggle_display("stock_entry_terima",      isAntar);
    },

    set_status_indicator(frm) {
        const map = {
            Draft: "gray", Dikirim: "orange", Diterima: "blue",
            Selesai: "green", Dibatalkan: "red"
        };
        frm.page.set_indicator(frm.doc.status || "Draft", map[frm.doc.status] || "gray");
    },

    show_flow_info(frm) {
        frm.dashboard.reset();
        if (!frm.doc.mutation_type) return;
        const flows = {
            "Antar Gudang" : "Draft → <b>Dikirim</b> → <b>Diterima</b> → <b>Verifikasi</b> → Selesai",
            "Intern Gudang": "Draft → <b>Submit</b> → Selesai"
        };
        const flow = flows[frm.doc.mutation_type];
        if (flow) {
            frm.dashboard.add_comment(
                `<span style="font-size:12px;color:#6c7680">Alur: </span>
                 <span style="font-size:12px">${flow}</span>`,
                "blue", true
            );
        }
    },

    add_action_buttons(frm) {
        if (frm.doc.docstatus !== 1) return;

        const { status, mutation_type: type } = frm.doc;

        if (type === "Antar Gudang" && status === "Dikirim") {
            frm.add_custom_button(__("Terima Barang"), () => {
                frappe.confirm(__("Konfirmasi penerimaan barang di gudang tujuan?"), () => {
                    frappe.call({
                        method: "silverplast.api.mutasi_barang.terima_barang",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    });
                });
            }, __("Aksi")).addClass("btn-primary");
        }

        if (type === "Antar Gudang" && status === "Diterima") {
            frm.add_custom_button(__("Verifikasi Nota"), () => {
                frappe.confirm(__("Konfirmasi verifikasi nota mutasi ini?"), () => {
                    frappe.call({
                        method: "silverplast.api.mutasi_barang.verifikasi_nota",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    });
                });
            }, __("Aksi")).addClass("btn-success");
        }

        if (status !== "Draft" && status !== "Dibatalkan") {
            frm.add_custom_button(__("Cetak Nota"), () => {
                frappe.set_route("print", "Mutasi Barang", frm.doc.name);
            }, __("Aksi"));
        }
    },
});

// ── Child table ───────────────────────────────────────────

frappe.ui.form.on("Mutasi Barang Item", {

    item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        // Set UOM default jika belum diisi
        if (!row.uom) {
            frappe.model.set_value(cdt, cdn, "uom", "Kg");
        }
    },

    qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.qty || row.qty <= 0) {
            frappe.model.set_value(cdt, cdn, "qty", 0);
            frappe.msgprint({ message: __("QTY harus lebih besar dari 0."), indicator: "red" });
        }
    }
});