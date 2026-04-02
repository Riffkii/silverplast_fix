// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Incoming QC", {
// 	refresh(frm) {

// 	},
// });

frappe.ui.form.on('Incoming QC', {

    onload: function(frm) {
        toggle_backdate_field(frm);
    },

    refresh: function(frm) {
        toggle_backdate_field(frm);
    },

    posting_date: function(frm) {
        toggle_backdate_field(frm);
    }
});

function toggle_backdate_field(frm) {

    let posting_date = frm.doc.posting_date;
    let today = frappe.datetime.get_today();

    if (!posting_date) {
        frm.set_df_property('backdate_reason', 'hidden', 1);
        frm.set_df_property('backdate_reason', 'reqd', 0);
        frm.set_value('backdate_reason', '');
        return;
    }

    if (posting_date < today) {
        frm.set_df_property('backdate_reason', 'hidden', 0);
        frm.set_df_property('backdate_reason', 'reqd', 1);

    } else {
        frm.set_df_property('backdate_reason', 'hidden', 1);
        frm.set_df_property('backdate_reason', 'reqd', 0);
        frm.set_value('backdate_reason', '');
    }
}

frappe.ui.form.on('Incoming QC', {
    refresh: function(frm) {

        if (!frm.doc.__islocal) {

            frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'QCT',
                    filters: {
                        source_incoming_qc: frm.doc.name
                    },
                    limit_page_length: 1
                },
                callback: function(r) {

                    if (!r.message || r.message.length === 0) {

                        frm.add_custom_button('Create QC', function() {

                            frappe.call({
                                method: 'silverplast.api.qc.create_qc_checks',
                                args: {
                                    incoming_qc: frm.doc.name
                                },
                                callback: function(res) {

                                    frappe.msgprint("QCT & QCE berhasil dibuat");

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