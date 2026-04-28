frappe.ui.form.on("Quotation", {
    add_details: function (frm) {
        if (frm.doc.quotation_to == "Customer" && frm.doc.party_name) {
            frappe.call({
                method: "chemical.chemical.whitelisted_method.quotation.get_approved_outward_sample_list",
                args: {
                    "party": frm.doc.party_name,
                },
                freeze: true,
                callback: function (r) {
                    if (r.message) {
                        frm.doc.items = []
                        r.message.forEach(function (item) {
                            var d = frm.add_child("items");
                            frappe.model.set_value(d.doctype, d.name, "item_code", item.product_name)
                            frappe.model.set_value(d.doctype, d.name, "outward_sample", item.name)
                            frappe.model.set_value(d.doctype, d.name, "sample_ref_no", item.ref_no)
                            frappe.model.set_value(d.doctype, d.name, "base_cost", item.per_unit_price)
                        })
                        frm.refresh_field("items")
                    }
                }
            })
        }
    },
    conversion_rate: function (frm) {
        console.log("conversion_rate")
        let conversion_rate = frm.doc.conversion_rate;
        frm.doc.items.forEach(function (item) {
            let new_cost = item.cost / conversion_rate;
            frappe.model.set_value(item.doctype, item.name, 'cost', new_cost);
        });
        frm.refresh_field('items');
    },
    get_samples: function (frm) {
        if (frm.doc.quotation_to == "Customer" && frm.doc.party_name) {
            frappe.call({
                method: "chemical.chemical.whitelisted_method.quotation.get_outward_sample_list",
                args: {
                    "party": frm.doc.party_name,
                },
                freeze: true,
                callback: function (r) {
                    if (r.message) {
                        frm.doc.items = []
                        r.message.forEach(function (item) {
                            var d = frm.add_child("items");
                            frappe.model.set_value(d.doctype, d.name, "item_code", item.product_name)
                            frappe.model.set_value(d.doctype, d.name, "outward_sample", item.name)
                            frappe.model.set_value(d.doctype, d.name, "sample_ref_no", item.ref_no)
                            frappe.model.set_value(d.doctype, d.name, "base_cost", item.per_unit_price)
                        })
                        frm.refresh_field("items")
                    }
                }
            })
        }
    },
    cal_margin: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if (frappe.meta.get_docfield("Quotation Item", "base_cost")) {
            if (d.base_cost) {
                frappe.model.set_value(d.doctype, d.name, 'margin_with_rmc', flt(d.rate - d.base_cost))
            }
        }
    }
});

frappe.ui.form.on("Quotation Item", {
    rate: function (frm, cdt, cdn) {
        frm.events.cal_margin(frm, cdt, cdn)
    },
    outward_sample: function (frm, cdt, cdn) {
        frm.events.cal_margin(frm, cdt, cdn)
    }
});