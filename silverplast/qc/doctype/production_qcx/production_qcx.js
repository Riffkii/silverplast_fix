// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Production QCX", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Production QCX', {
    qc_result: function(frm) {
        toggle_note(frm);
    },
    onload: function(frm) {
        toggle_note(frm);
    }
});

function toggle_note(frm) {
    if (frm.doc.qc_result === "Reject") {
        frm.set_df_property('qc_note', 'hidden', 0);
        frm.set_df_property('qc_note', 'reqd', 1);
    } else {
        frm.set_df_property('qc_note', 'hidden', 1);
        frm.set_df_property('qc_note', 'reqd', 0);
        frm.set_value('qc_note', '');
    }
}