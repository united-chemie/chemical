frappe.ui.form.on("Item", {
    refresh: function(frm) {
        frm.remove_custom_button("Stock Balance", "View");
        if (frm.doc.is_stock_item) {
            frm.add_custom_button(__("Stock Balance Chemical"), function() {
                frappe.route_options = {
                    item_code : frm.doc.name
                }
                frappe.set_route("query-report", "Stock Balance Chemical");
            }, __("View"));
        }
        //added
        const stock_exists = (frm.doc.__onload
			&& frm.doc.__onload.stock_exists) ? 1 : 0;

		['maintain_as_is_stock'].forEach((fieldname) => {
			frm.set_df_property(fieldname, 'read_only', stock_exists);
		});
    },
});