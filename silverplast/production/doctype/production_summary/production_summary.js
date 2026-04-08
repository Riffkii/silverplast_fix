// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Production Summary", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Production Summary', {
    refresh: function(frm) {

        if (frm.doc.qc_result === "Conditional Pass") {
            frm.set_df_property('qc_note', 'hidden', 0);
        } else {
            frm.set_df_property('qc_note', 'hidden', 1);
        }

        if (!frm.is_new() && ["Pass", "Conditional Pass"].includes(frm.doc.qc_result)) {

            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Production Print Label',
                    filters: {
                        source_document: frm.doc.name
                    },
                    limit_page_length: 1
                },
                callback: function(r) {

                    if (!r.message || r.message.length === 0) {

                        frm.add_custom_button('Print Label', function() {

                            frm.disable_save();

                            frappe.call({
                                method: 'silverplast.api.production_print_label.create_print_label',
                                args: {
                                    source_document: frm.doc.name
                                },
                                callback: function() {
                                    frappe.msgprint("Berhasil print label & update stok");
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