frappe.ui.form.on("BOM", {
    onload: function (frm) {
        if (frm.doc.__islocal){
            if(!frm.doc.is_multiple_item){
                frm.set_value("total_quantity",flt(frm.doc.quantity))
            }
            else{
                frm.events.is_multiple_item(frm)
                cur_frm.set_df_property("quantity", "read_only",1);
                cur_frm.set_df_property("quantity", "label",'First Item Quantity');
            }
        }
        if (frm.doc.__islocal && frm.doc.rm_cost_as_per == "Price List") {
            frm.set_value("buying_price_list", "Standard Buying");
        }
    },
    refresh: function(frm){
        if (frm.doc.is_multiple_item){
            cur_frm.set_df_property("quantity", "read_only",1);
            cur_frm.set_df_property("quantity", "label",'First Item Quantity');
        }
    },
    before_save: function (frm) {
        let unit_qty = flt(frm.doc.total_cost / frm.doc.quantity);
        frm.set_value("per_unit_price", unit_qty);
		frm.set_value('etp_amount',flt(frm.doc.etp_qty*frm.doc.etp_rate))
		let amount = 0
		frm.doc.items.forEach(function (d) {
            amount += d.amount
        });
        frm.set_value("additional_amount", amount);
        frm.events.cal_total(frm)
		
    },
    cal_total:function(frm){
        if(frm.doc.is_multiple_item){
            frm.set_value("quantity",flt(frm.doc.multiple_finish_item[0].qty))
        }
        if(!frm.doc.is_multiple_item){
            frm.doc.multiple_finish_item = []
        }
    },
    cal_batch_yield: function(frm){
        frm.doc.items.forEach(function (d){
            if (frm.doc.based_on && frm.doc.based_on == d.item_code)
            {
                if(frm.doc.is_multiple_item){
                    frm.doc.multiple_finish_item.forEach(function (row){
                        row.batch_yield = flt(row.qty) / d.qty
                    });
                }
            }
        });
        let total_yield = 0
        frm.doc.multiple_finish_item.forEach(function (row){
            total_yield += row.batch_yield
        });
        frm.set_value("batch_yield",total_yield)
    },
    total_quantity: function(frm){
        if(frm.doc.multiple_finish_item){
            frm.doc.multiple_finish_item.forEach(function (d){
                if (d.qty_ratio != 0)
                    d.qty = frm.doc.total_quantity * d.qty_ratio / 100;
            });
        }
        frm.refresh_fields("mutiple_finish_item")
        if(frm.doc.is_multiple_item){
            frm.set_value("quantity",flt(frm.doc.multiple_finish_item[0].qty))
        }
    },
    
    quantity: function (frm){
        if(!frm.doc.is_multiple_item){
            frm.set_value("total_quantity",flt(frm.doc.quantity))
        }
    },
	is_multiple_item: function(frm){
		if(frm.doc.is_multiple_item){
			cur_frm.set_df_property("quantity", "read_only",1);
            cur_frm.set_df_property("quantity", "label",'First Item Quantity');
            if (frm.doc.item && (frm.doc.multiple_finish_item == undefined || frm.doc.multiple_finish_item.length == 0)){
                var row = cur_frm.add_child("multiple_finish_item");
                row.item_code = frm.doc.item;
                row.qty = frm.doc.quantity;
                row.cost_ratio = 100;
                row.qty_ratio = 100;
                row.batch_yield = 0
                frm.refresh_fields("multiple_finish_item");
            }
		}
		if(!frm.doc.is_multiple_item){
			cur_frm.set_df_property("quantity", "read_only",0);
            cur_frm.set_df_property("quantity", "label",'Quantity');
            frm.doc.multiple_finish_item = []
        }
	},
	
    total_operational_cost: function (frm) {
        frm.set_value("total_cost", flt(frm.doc.additional_amount + frm.doc.raw_material_cost + frm.doc.volume_amount + frm.doc.etp_amount - frm.doc.scrap_material_cost));
    },

    total_cost: function (frm) {
        frm.set_value("per_unit_price", flt(frm.doc.total_cost / frm.doc.quantity));
    },

    before_submit: function (frm) {
        if(frm.doc.is_multiple_item){
            let total_yield = 0
            frm.doc.multiple_finish_item.forEach(function (row){
                total_yield += row.batch_yield
            });
            frm.set_value("batch_yield",total_yield)
        }
        else{
            let cal_yield = 0;
            frm.doc.items.forEach(function (d) {
                if (frm.doc.based_on == d.item_code) {
                    cal_yield = frm.doc.quantity / d.qty;
                }
            });
            frm.set_value("batch_yield", cal_yield);
        }
    },

    update_price_list: function (frm) {
        frappe.call({
            method: "chemical.chemical.whitelisted_method.bom.upadte_item_price",
            args: {
                docname: frm.doc.name,
                item: frm.doc.item,
                price_list: frm.doc.buying_price_list,
                per_unit_price: frm.doc.per_unit_price
            },
            callback: function (r) {
                frappe.msgprint(r.message);
                refresh_field("items");
                frm.refresh_fields();
                frm.reload_doc();
            }
        });
    },
    update_cost: function (frm) {
        if (!frm.is_dirty()){
            return frappe.call({
                method: "chemical.chemical.whitelisted_method.bom.update_bom_cost",
                freeze: true,
                args: {
                    doc:frm.doc.name,
                    update_parent: true,
                    from_child_bom: false,
                    save: true
                },
                callback: function (r) {
                    frm.events.update_price_list(frm);
                    refresh_field("items");
                    if (!r.exc){
                        frm.refresh_fields();
                    }
                }
            });
        }
    },
	etp_qty: function(frm){
		frm.set_value('etp_amount',flt(frm.doc.etp_qty*frm.doc.etp_rate))
	},
	etp_rate: function(frm){
		frm.set_value('etp_amount',flt(frm.doc.etp_qty*frm.doc.etp_rate))
    },
});

frappe.ui.form.on("BOM Additional Cost", {
	rate: function(frm, cdt, cdn){
		let d = locals[cdt][cdn]
		frappe.model.set_value(d.doctype,d.name,'amount',flt(d.qty*d.rate))
    },
    additional_cost_add:function(frm,cdt,cdn){
        var row = frappe.get_doc(cdt, cdn)
        if (!row.qty){
            row.qty = frm.doc.total_quantity
        }
        if(!row.uom){
            row.uom = "FG QTY"
        }
        frm.refresh_field('additional_cost');
    }
});
frappe.ui.form.on("BOM Multiple Finish Item", {
	qty: function(frm, cdt, cdn){
        frm.events.cal_total(frm)
        frm.events.quantity(frm)
    },
    qty_ratio: function(frm, cdt, cdn){
        frm.events.total_quantity(frm)
    },
});

frappe.ui.form.on("BOM Item", {
    qty: function(frm, cdt, cdn){
        frm.events.cal_batch_yield(frm)
    },
});