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

                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Material Request Memo',
                        name: frm.doc.material_request
                    },
                    callback: function(res) {

                        let items = res.message.items || [];

                        let data = items.map(row => {
                            return {
                                kode_barang: row.kode_barang,
                                qty_request: row.qty,
                                qty_sisa: 0
                            };
                        });

                        let dialog = new frappe.ui.Dialog({
                            title: 'Send To QC',
                            fields: [
                                {
                                    label: 'Quantity',
                                    fieldname: 'qty',
                                    fieldtype: 'Float',
                                    reqd: 1
                                },
                                {
                                    fieldname: 'materials',
                                    fieldtype: 'Table',
                                    label: 'Material Sisa',
                                    cannot_add_rows: true,
                                    cannot_delete_rows: true,
                                    in_place_edit: true,
                                    data: data,
                                    fields: [
                                        {
                                            fieldname: 'kode_barang',
                                            fieldtype: 'Data',
                                            label: 'Kode Barang',
                                            read_only: 1,
                                            in_list_view: 1
                                        },
                                        {
                                            fieldname: 'qty_request',
                                            fieldtype: 'Float',
                                            label: 'Qty Request',
                                            read_only: 1,
                                            in_list_view: 1
                                        },
                                        {
                                            fieldname: 'qty_sisa',
                                            fieldtype: 'Float',
                                            label: 'Qty Sisa',
                                            in_list_view: 1
                                        }
                                    ]
                                }
                            ],
                            primary_action_label: 'Submit',
                            primary_action(values) {

                                frappe.call({
                                    method: 'silverplast.api.production.send_to_qc',
                                    args: {
                                        production_id: frm.doc.name,
                                        qty: values.qty,
                                        materials: values.materials
                                    },
                                    callback: function() {
                                        frappe.msgprint("Berhasil dikirim ke QC");
                                        dialog.hide();
                                        frm.reload_doc();
                                    }
                                });

                            }
                        });

                        dialog.show();
                    }
                });

            });

        }
    }
});