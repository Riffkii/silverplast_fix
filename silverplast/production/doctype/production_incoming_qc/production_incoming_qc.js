// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Production Incoming QC", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Production Incoming QC', {
    refresh: function(frm) {

        if (!frm.is_new()) {

            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Production QCT',
                    filters: {
                        source_incoming_qc: frm.doc.name
                    },
                    limit_page_length: 1
                },
                callback: function(r) {

                    if (!r.message || r.message.length === 0) {

                        frm.add_custom_button('Create QC', function() {

                            frappe.call({
                                method: 'silverplast.api.production_qc.create_qc_checks_production',
                                args: {
                                    production_incoming_qc: frm.doc.name
                                },
                                callback: function() {

                                    frappe.msgprint("Production QCT & QCX berhasil dibuat");

                                    frm.reload_doc();
                                }
                            });

                        });

                    }
                }
            });

        }
    }
});