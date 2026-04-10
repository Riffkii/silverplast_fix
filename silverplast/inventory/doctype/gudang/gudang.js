// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Gudang", {

    refresh(frm) {
        frm.trigger("set_status_indicator");
        frm.trigger("show_capacity_info");
        frm.trigger("toggle_fields_by_level");
        if (!frm.is_new()) {
            frm.trigger("add_custom_buttons");
        }
    },

    level(frm) {
        frm.trigger("toggle_fields_by_level");
        if (frm.doc.level === "Gudang") {
            frm.set_value("induk_gudang", "");
        }
    },

    kapasitas_ton(frm) { frm.trigger("show_capacity_info"); },
    stok_saat_ini_ton(frm) { frm.trigger("show_capacity_info"); },

    toggle_fields_by_level(frm) {
        const isAreaOrRak = frm.doc.level === "Area" || frm.doc.level === "Rak";
        const isRak       = frm.doc.level === "Rak";

        // Induk Gudang: wajib untuk Area dan Rak
        frm.toggle_display("induk_gudang", isAreaOrRak);
        frm.toggle_reqd("induk_gudang",   isAreaOrRak);

        // Kapasitas: tampil untuk Gudang dan Area saja
        frm.toggle_display("kapasitas_ton",     !isRak);
        frm.toggle_display("stok_saat_ini_ton", !isRak);

        // PIC: wajib hanya di level Gudang
        frm.toggle_reqd("pic", frm.doc.level === "Gudang");

        // FIX: tipe_barang dan kode_barang — tampil HANYA di level Rak
        // tipe_barang tidak pernah mandatory
        frm.toggle_display("tipe_barang", isRak);
        frm.toggle_reqd("tipe_barang",    false);   // ← tidak pernah wajib

        frm.toggle_display("kode_barang", isRak);

        // Rate: tampil hanya jika tipe_barang = Barang Jadi (sudah ada depends_on di JSON)

        // Filter induk berdasarkan level yang benar
        if (frm.doc.level === "Area") {
            frm.set_query("induk_gudang", () => ({
                filters: { level: "Gudang", status: "Aktif" }
            }));
        } else if (isRak) {
            frm.set_query("induk_gudang", () => ({
                filters: { level: "Area", status: "Aktif" }
            }));
        }
    },

    set_status_indicator(frm) {
        const color = frm.doc.status === "Aktif" ? "green" : "red";
        frm.page.set_indicator(frm.doc.status || "Aktif", color);
    },

    show_capacity_info(frm) {
        frm.dashboard.reset();
        if (!frm.doc.kapasitas_ton || frm.doc.level === "Rak") return;

        const kap  = frm.doc.kapasitas_ton     || 0;
        const stok = frm.doc.stok_saat_ini_ton || 0;
        const pct  = kap > 0 ? Math.min(Math.round(stok / kap * 100), 100) : 0;

        let warna = "#28a745", label = "Normal";
        if (pct >= 90)      { warna = "#dc3545"; label = "Hampir Penuh!"; }
        else if (pct >= 70) { warna = "#fd7e14"; label = "Perlu Perhatian"; }

        frm.dashboard.add_comment(
            `<div style="margin:4px 0">
                <span style="font-size:12px;color:#6c7680">Kapasitas Terpakai</span>
                <div style="background:#e9ecef;border-radius:4px;height:10px;margin:4px 0;overflow:hidden">
                    <div style="width:${pct}%;background:${warna};height:100%;border-radius:4px"></div>
                </div>
                <span style="font-size:12px;font-weight:500;color:${warna}">
                    ${stok} / ${kap} ton (${pct}%) — ${label}
                </span>
            </div>`,
            pct >= 90 ? "red" : pct >= 70 ? "orange" : "green",
            true
        );
    },

    add_custom_buttons(frm) {
        frm.add_custom_button(__("Sub-Lokasi"), () => {
            frm.trigger("show_child_locations");
        }, __("Aksi"));

        frm.add_custom_button(__("Riwayat Mutasi"), () => {
            frappe.set_route("List", "Mutasi Barang", {
                source_warehouse: frm.doc.kode_gudang
            });
        }, __("Aksi"));
    },

    show_child_locations(frm) {
        frappe.call({
            method: "silverplast.api.gudang.get_child_locations",
            args: { kode_gudang: frm.doc.kode_gudang },
            callback(r) {
                if (!r.message || !r.message.length) {
                    frappe.msgprint(__("Belum ada Area atau Rak di gudang ini."));
                    return;
                }
                const rows = r.message.map(d =>
                    `<tr>
                        <td><a href="/app/gudang/${d.kode_gudang}" target="_blank">
                            ${d.kode_gudang}</a></td>
                        <td>${d.nama_gudang}</td>
                        <td>${d.level}</td>
                        <td>${d.tipe_barang || "-"}</td>
                    </tr>`
                ).join("");
                frappe.msgprint({
                    title: __("Sub-Lokasi: " + frm.doc.nama_gudang),
                    message: `
                        <table class="table table-bordered table-condensed" style="font-size:13px">
                            <thead style="background:#f8f9fa">
                                <tr><th>Kode</th><th>Nama</th><th>Level</th><th>Tipe</th></tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>`,
                    wide: true,
                });
            }
        });
    }
});