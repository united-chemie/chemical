// Copyright (c) 2021, FinByz Tech Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.fields_dict.item_code.get_query = function(doc) {
	return {
		filters: {
			"is_stock_item": 1
		}
	}
};
frappe.ui.form.on('Change Has Batch No', {
	// refresh: function(frm) {

	// }
});
