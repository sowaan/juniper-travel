// Copyright (c) 2023, Sowaan and contributors
// For license information, please see license.txt

frappe.ui.form.on("Juniper Site", {
  // refresh(frm) {

  // },

  fetch_data: function (frm) {
    frappe.call({
      method: "juniper.juniper.doctype.juniper_site.juniper_site.sync_customer",
      args: {
        doc: frm.doc,
        from_date: frm.doc.from_date,
        to_date: frm.doc.to_date,
      },
      callback: function (r) {
        if (!r.exc) {
          // frm.set_value('access_token', r.message)
          // frm.save();
        }
      },
      freeze: true,
      freeze_message: __("Syncing data from Juniper..."),
    });
  },

  fetch_suppliers: function (frm) {
    frappe.call({
      method: "juniper.juniper.doctype.juniper_site.juniper_site.sync_supplier",
      args: {
        doc: frm.doc,
        from_date: frm.doc.sup_from_date,
        to_date: frm.doc.sup_to_date,
      },
      callback: function (r) {
        if (!r.exc) {
          // frm.set_value('access_token', r.message)
          // frm.save();
        }
      },
      freeze: true,
      freeze_message: __("Syncing data from Juniper..."),
    });
  },

  fetch_bookings: function (frm) {
    frappe.call({
      method:
        "juniper.juniper.doctype.juniper_site.juniper_site.sync_sales_order",
      args: {
        doc: frm.doc,
        from_date: frm.doc.sales_from_date,
        to_date: frm.doc.sale_to_date,
      },
      callback: function (r) {
        if (!r.exc) {
          // frm.set_value('access_token', r.message)
          // frm.save();
        }
      },
      freeze: true,
      freeze_message: __("Syncing data from Juniper..."),
    });
  },

  fetch_invoices: function (frm) {
    frappe.call({
      method:
        "juniper.juniper.doctype.juniper_site.juniper_site.sync_sales_invoice",
      args: {
        doc: frm.doc,
        from_date: frm.doc.invoice_from_date,
        to_date: frm.doc.invoice_to_date,
      },
      callback: function (r) {
        if (!r.exc) {
          // frm.set_value('access_token', r.message)
          // frm.save();
        }
      },
      freeze: true,
      freeze_message: __("Syncing data from Juniper..."),
    });
  },
});
