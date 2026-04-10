// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mutasi Barang", {

    refresh(frm) {
        frm.trigger("set_status_indicator");
        frm.trigger("toggle_fields_by_type");
        frm.trigger("add_action_buttons");
        frm.trigger("show_flow_info");
        // Tampilkan ringkasan stok gudang asal jika sudah ada
        if (frm.doc.source_warehouse && frm.doc.docstatus === 0) {
            frm.trigger("show_stok_info");
        }
    },

    source_warehouse(frm) {
        frm.set_query("source_area_intern", () => ({
            filters: { induk_gudang: frm.doc.source_warehouse, status: "Aktif" }
        }));
        frm.set_query("destination_area_intern", () => ({
            filters: { induk_gudang: frm.doc.source_warehouse, status: "Aktif" }
        }));
        frm.trigger("show_stok_info");
    },

    mutation_type(frm) {
        frm.trigger("toggle_fields_by_type");
        frm.set_value("destination_warehouse", "");
        frm.set_value("source_area_intern", "");
        frm.set_value("destination_area_intern", "");
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
            Draft:"gray", Dikirim:"orange", Diterima:"blue",
            Selesai:"green", Dibatalkan:"red"
        };
        frm.page.set_indicator(
            frm.doc.status || "Draft",
            map[frm.doc.status] || "gray"
        );
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

    // ── Cek stok tersedia di gudang asal ──────────

    show_stok_info(frm) {
        if (!frm.doc.source_warehouse || frm.doc.docstatus !== 0) return;

        frappe.call({
            method: "silverplast.api.gudang.get_stock_summary",
            args: { kode_gudang: frm.doc.source_warehouse },
            callback(r) {
                if (!r.message || !r.message.length) return;

                const rows = r.message.map(s =>
                    `<span style="margin-right:16px;font-size:11px">
                        <b>${s.item_code}</b>: ${s.stok_saat_ini} ${s.uom}
                    </span>`
                ).join("");

                frm.dashboard.add_comment(
                    `<div style="margin:2px 0">
                        <span style="font-size:11px;color:#6c7680">
                            Stok di ${frm.doc.source_warehouse}: 
                        </span>
                        ${rows}
                    </div>`,
                    "green", true
                );
            }
        });
    },

    // ── Tombol aksi ───────────────────────────────

    add_action_buttons(frm) {
        if (frm.doc.docstatus !== 1) return;

        const { status, mutation_type: type } = frm.doc;

        if (type === "Antar Gudang" && status === "Dikirim") {
            frm.add_custom_button(__("Terima Barang"), () => {
                frappe.confirm(
                    __("Konfirmasi penerimaan barang di gudang tujuan?"),
                    () => frappe.call({
                        method: "silverplast.api.mutasi_barang.terima_barang",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    })
                );
            }, __("Aksi")).addClass("btn-primary");
        }

        if (type === "Antar Gudang" && status === "Diterima") {
            frm.add_custom_button(__("Verifikasi Nota"), () => {
                frappe.confirm(
                    __("Konfirmasi verifikasi nota mutasi ini?"),
                    () => frappe.call({
                        method: "silverplast.api.mutasi_barang.verifikasi_nota",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    })
                );
            }, __("Aksi")).addClass("btn-success");
        }

        if (status !== "Draft" && status !== "Dibatalkan") {
            frm.add_custom_button(__("Cetak Nota"), () => {
                frappe.set_route("print", "Mutasi Barang", frm.doc.name);
            }, __("Aksi"));
        }
    }
});

// ── Child table: cek stok saat isi qty ───────────────────

frappe.ui.form.on("Mutasi Barang Item", {

    item_code(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;
        if (!row.uom) frappe.model.set_value(cdt, cdn, "uom", "Kg");

        // Tampilkan stok tersedia di catatan_item
        if (frm.doc.source_warehouse) {
            frappe.db.sql(
                `SELECT qty_sesudah FROM \`tabStok\`
                 WHERE item_code=%s AND gudang=%s AND status='Aktif'
                 ORDER BY tanggal DESC, jam DESC, creation DESC LIMIT 1`,
                [row.item_code, frm.doc.source_warehouse],
                (data) => {
                    const stok = data && data[0] ? data[0][0] : 0;
                    frappe.model.set_value(
                        cdt, cdn, "catatan_item",
                        `Stok tersedia: ${stok} ${row.uom || "Kg"}`
                    );
                }
            );
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
            return;
        }

        // Cek stok real-time saat isi qty
        if (!frm.doc.source_warehouse || !row.item_code) return;

        frappe.call({
            method: "silverplast.inventory.doctype.stok.stok.cek_stok_cukup",
            args: {
                item_code   : row.item_code,
                gudang      : frm.doc.source_warehouse,
                qty_diminta : row.qty
            },
            callback(r) {
                if (!r.message) return;
                const info = r.message;

                frappe.model.set_value(
                    cdt, cdn, "catatan_item",
                    `Tersedia: ${info.qty_tersedia} | Diminta: ${info.qty_diminta}`
                );

                if (!info.cukup) {
                    frappe.msgprint({
                        title: __("Stok Tidak Cukup"),
                        message: __(
                            `<b>${row.item_code}</b> di ${frm.doc.source_warehouse}<br>` +
                            `Tersedia: <b>${info.qty_tersedia} ${row.uom || "Kg"}</b><br>` +
                            `Diminta : <b>${info.qty_diminta} ${row.uom || "Kg"}</b><br>` +
                            `Kurang  : <b style="color:red">${Math.abs(info.selisih)} ${row.uom || "Kg"}</b>`
                        ),
                        indicator: "red"
                    });
                }
            }
        });
    }
});