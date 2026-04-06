// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Material Request Memo", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Material Request Memo', {
    refresh: function(frm) {

        frm.set_df_property('status', 'hidden', 1);

        frm.set_query('kode_barang', function() {
            return {
                filters: {
                    status: 'Aktif',
                    stok_saat_ini_ton: ['>', 0],
                    tipe_barang: ['in', ['Bahan Baku', 'Additive', 'Bahan Penolong']]
                }
            };
        });

        if (!frm.is_new() && frm.doc.status === 'Draft') {

            frm.add_custom_button('Accept', function() {

                frappe.call({
                    method: 'silverplast.api.production.accept_material_request',
                    args: {
                        docname: frm.doc.name
                    },
                    callback: function() {

                        frappe.msgprint("Material berhasil diproses");

                        frm.reload_doc();
                    }
                });

            });

        }
    }
});