// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Production", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Production', {
    onload: function(frm) {
        frm.set_query('material_request', function() {
            return {
                filters: {
                    status: 'Accepted'
                }
            };
        });
    }
});

frappe.ui.form.on('Production', {
    material_request: function(frm) {

        if (frm.doc.material_request) {

            frappe.db.get_doc('Material Request Memo', frm.doc.material_request)
                .then(doc => {

                    frm.set_value('item_code', doc.barang_jadi);

                });

        } else {
            frm.set_value('item_code', '');
        }
    }
});

frappe.ui.form.on('Production', {
    refresh: function(frm) {

        if (!frm.is_new() && !frm.doc.qc_sent) {

            frm.add_custom_button('Send To QC', function() {

                let dialog = new frappe.ui.Dialog({
                    title: 'Send To QC',
                    fields: [
                        {
                            label: 'Quantity',
                            fieldname: 'qty',
                            fieldtype: 'Float',
                            reqd: 1
                        }
                    ],
                    primary_action_label: 'Submit',
                    primary_action(values) {

                        frappe.call({
                            method: 'silverplast.api.production.send_to_qc',
                            args: {
                                production_id: frm.doc.name,
                                qty: values.qty
                            },
                            callback: function() {
                                frappe.msgprint("Berhasil dikirim ke QC");
                                dialog.hide();
                            }
                        });

                    }
                });

                dialog.show();
            });

        }
    }
});