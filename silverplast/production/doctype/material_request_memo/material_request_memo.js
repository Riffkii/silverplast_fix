// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Material Request Memo", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Material Request Memo', {
    onload: function(frm) {
        frm.set_query('barang_jadi', function() {
            return {
                filters: {
                    tipe_barang: 'Barang Jadi',
                    status: 'Aktif'
                }
            };
        });
    }
});

frappe.ui.form.on('Material Request Memo', {
    onload: function(frm) {

        if (frm.is_new() && (!frm.doc.items || frm.doc.items.length === 0)) {
            let row = frm.add_child('items');
            frm.refresh_field('items');
        }
    },

    refresh: function(frm) {

        frm.set_df_property('status', 'hidden', frm.is_new());

        frm.set_query('kode_barang', 'items', function() {
            return {
                filters: {
                    status: 'Aktif',
                    qty_sesudah: ['>', 0],
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