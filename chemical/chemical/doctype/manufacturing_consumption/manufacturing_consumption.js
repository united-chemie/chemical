// Copyright (c) 2021, FinByz Tech Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.fields_dict.manufacturing_consumption_details.grid.get_field("work_order").get_query = function(doc) {
	return {
		'filters': {'docstatus':1,
			"Status": ['!=', "Completed"],
		}
	}
};
cur_frm.fields_dict.manufacturing_consumption_details.grid.get_field("item_code").get_query = function(doc) {
	return {
		filters: {
			"is_stock_item":1,
		}
	}
};
cur_frm.fields_dict.manufacturing_consumption_details.grid.get_field("s_warehouse").get_query = function(doc) {
	return {
		filters: {
			'is_group':0,
			"company":doc.company,
		}
	}
};
cur_frm.fields_dict.source_warehouse.get_query = function(doc) {
	return {
	   'filters': {
		'is_group':0,
		"company":doc.company,
		}
	}
};

frappe.ui.form.on('Manufacturing Consumption', {
	// refresh: function(frm) {

	// }
	
	onload: function(frm){
        frm.set_query("batch_no", "manufacturing_consumption_details", function (doc, cdt, cdn) {
            let d = locals[cdt][cdn];
            if (!d.item_code) {
                frappe.msgprint(__("Please select Item Code"));
            }
            else if (!d.s_warehouse) {
                frappe.msgprint(__("Please select source warehouse"));
            }
            else {
                return {
                    query: "chemical.query.get_batch_no",
                    filters: {
                        'item_code': d.item_code,
                        'warehouse': d.s_warehouse
                    }
                }
            }
        })
	},
	source_warehouse: function (frm) {
		if (frm.doc.source_warehouse){
		   frm.doc.manufacturing_consumption_details.forEach(function (row) {
		   frappe.model.set_value(row.doctype, row.name, "s_warehouse", frm.doc.source_warehouse);
		   });
		   frm.refresh();
		}
   		
   },
});
frappe.ui.form.on('Manufacturing Consumption Details', {
	item_code : function(frm,cdt,cdn){
		let d = locals[cdt][cdn]
		frappe.call({
			method: "chemical.chemical.doctype.manufacturing_consumption.manufacturing_consumption.get_required_qty",
			args: {
				'work_order': d.work_order,
				'item_code': d.item_code
			},
			callback: function(r) {
				if(r.message){
					frappe.model.set_value(d.doctype,d.name,'required_qty',r.message)
				}
				else{
					frappe.model.set_value(d.doctype,d.name,'required_qty',0)
				}
			}
		});
	},
	manufacturing_consumption_details_add: function(frm){
		if (frm.doc.source_warehouse){
		   frm.doc.manufacturing_consumption_details.forEach(function (row) {
		   frappe.model.set_value(row.doctype, row.name, "s_warehouse", frm.doc.source_warehouse);
		   });
		   frm.refresh();
		}
		
   },
});

