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