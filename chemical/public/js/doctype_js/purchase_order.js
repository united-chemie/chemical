cur_frm.fields_dict.taxes_and_charges.get_query = function(doc) {
	return {
		filters: {
			"company": doc.company
		}
	}
};

frappe.ui.form.on("Purchase Order", {
    validate: function(frm) {
		frappe.db.get_value("Company",frm.doc.company,'maintain_as_is_new',function(c){
			if(!c.maintain_as_is_new){
				frm.doc.items.forEach(function (d) {
					frappe.db.get_value("Item",d.item_code,'maintain_as_is_stock',function(r){
						if(r.maintain_as_is_stock){
							if (d.quantity){
								frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
							}
							if (d.price){
								frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
							}
						}
						else{
							if (d.quantity){
								frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
							}
							if (d.price){
								frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
							}
						}
					})
				});
			}
		});
		frm.trigger("cal_total_quantity");

	},
	cal_rate_qty: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		frappe.db.get_value("Company", frm.doc.company, 'maintain_as_is_new', function (c) {
			if(!c.maintain_as_is_new) {
				frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
					if(r.maintain_as_is_stock){
						if (d.quantity){
							frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / d.concentration));
						}
						if (d.price){
							frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.quantity * d.price) / flt(d.qty));
						}
					}
					else{
						if (d.quantity){
							frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
						}
						if (d.price){
							frappe.model.set_value(d.doctype, d.name, 'rate', flt(d.price));
						}
					}
				});
			}
		})
	},

	cal_total_quantity: function (frm) {
		frappe.db.get_value("Company", frm.doc.company, 'maintain_as_is_new', function (c) {
			if(!c.maintain_as_is_new) {
				let total_quantity = 0.0;
				
				frm.doc.items.forEach(function (d) {
					total_quantity += flt(d.quantity);
				});
				frm.set_value("total_quantity", total_quantity);
			}
		});
	},
    
});

frappe.ui.form.on("Purchase Order Item", {
	quantity: function(frm,cdt,cdn){
		frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    price:function(frm,cdt,cdn){
		frm.events.cal_rate_qty(frm,cdt,cdn)
	},  
    concentration: function(frm, cdt, cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    }
});