
frappe.ui.form.on("Quality Inspection", {
	setup: function(frm) {
		frm.set_query("item_code", function(doc) {
			if(doc.reference_type == "Stock Entry"){
			var doctype = "Stock Entry Detail"
			}
			else if(doc.reference_type == "Outward Sample"){
				var doctype = "Outward Sample Detail"
			}
			else{
				var doctype = doc.reference_type + " Item";
			}
			if (doc.reference_type && doc.reference_name && doc.reference_type!="Inward Sample") {
				return {
					query: "chemical.query.item_query",
					filters: {
						"from": doctype
					}
				};
			}
		})
	}
})