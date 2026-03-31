// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Item Receipt Document", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Item Receipt Document', {
    refresh: function(frm) {

        if (frm.doc.qc_note) {
            frm.set_df_property('qc_note', 'hidden', 0);
        } else {
            frm.set_df_property('qc_note', 'hidden', 1);
        }

    }
});

frappe.ui.form.on('Item Receipt Document', {
    refresh: function(frm) {

        if (!frm.is_new()) {

            frm.add_custom_button('Print Label', function() {

                frm.disable_save();

                frappe.call({
                    method: 'silverplast.api.print_label.create_print_label',
                    args: {
                        source_document: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message) {

                            frm.clear_custom_buttons();

                            frappe.set_route('Form', 'Print Label', r.message);
                        }
                    }
                });

            });

        }
    }
});