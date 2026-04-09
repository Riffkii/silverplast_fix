// Copyright (c) 2026, P79 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Opname", {

    refresh(frm) {
        frm.trigger("set_status_indicator");
        frm.trigger("add_action_buttons");
        frm.trigger("show_flow_info");
    },

    set_status_indicator(frm) {
        const map = {
            Draft:"gray", "In Progress":"orange", Recapitulated:"blue",
            Approved:"green", Cancelled:"red"
        };
        frm.page.set_indicator(frm.doc.status || "Draft", map[frm.doc.status] || "gray");
    },

    show_flow_info(frm) {
        frm.dashboard.reset();
        frm.dashboard.add_comment(
            `<span style="font-size:12px;color:#6c7680">Flow: </span>
             <span style="font-size:12px">
               Draft → <b>In Progress</b> (submit) → 
               <b>Load System Stock</b> → Staff Count → 
               <b>Recapitulate</b> → <b>Approve & Update Stock</b> → Approved
             </span>`,
            "blue", true
        );
    },

    add_action_buttons(frm) {
        if (frm.doc.docstatus !== 1) return;

        const s = frm.doc.status;

        // Step 1: Load system stock (Cetak Posisi Stock)
        if (s === "In Progress") {
            frm.add_custom_button(__("Load System Stock"), () => {
                frappe.confirm(
                    __("Load current stock from system? Existing rows will be cleared."),
                    () => frappe.call({
                        method: "silverplast.inventory.doctype.stock_opname.stock_opname.load_system_stock",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    })
                );
            }, __("Actions")).addClass("btn-primary");
        }

        // Step 2: Recapitulate (setelah staff isi actual_qty)
        if (s === "In Progress") {
            frm.add_custom_button(__("Recapitulate"), () => {
                frappe.confirm(
                    __("Recapitulate and calculate Gain/Loss?"),
                    () => frappe.call({
                        method: "silverplast.inventory.doctype.stock_opname.stock_opname.recapitulate",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    })
                );
            }, __("Actions"));
        }

        // Step 3: Approve & Update Stock
        if (s === "Recapitulated") {
            frm.add_custom_button(__("Approve & Update Stock"), () => {
                frappe.confirm(
                    __("This will adjust the actual stock in the system. Continue?"),
                    () => frappe.call({
                        method: "silverplast.inventory.doctype.stock_opname.stock_opname.approve_and_update_stock",
                        args: { docname: frm.doc.name },
                        callback(r) { if (!r.exc) frm.reload_doc(); }
                    })
                );
            }, __("Actions")).addClass("btn-success");
        }
    }
});

frappe.ui.form.on("Stock Opname Item", {
    actual_qty(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const diff = (row.actual_qty || 0) - (row.system_qty || 0);
        frappe.model.set_value(cdt, cdn, "difference", Math.round(diff * 1000) / 1000);
        frappe.model.set_value(cdt, cdn, "difference_type",
            diff > 0 ? "Gain" : diff < 0 ? "Loss" : "Match"
        );
    }
});