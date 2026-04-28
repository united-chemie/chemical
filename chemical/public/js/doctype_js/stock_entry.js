
cur_frm.fields_dict.from_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company,
            "is_group":0,
        }
    }
};
cur_frm.fields_dict.to_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company,
            "is_group":0,
        }
    }
};
cur_frm.fields_dict.items.grid.get_field("s_warehouse").get_query = function (doc) {
    return {
        filters: {
            "company": doc.company,
            "is_group":0,
        }
    }
};
cur_frm.fields_dict.items.grid.get_field("t_warehouse").get_query = function (doc) {
    return {
        filters: {
            "company": doc.company,
            "is_group":0,
        }
    }
};
cur_frm.fields_dict.items.grid.get_field("bom_no").get_query = function (doc) {
    return {
        filters: {
            "docstatus": 1,
        }
    }
};

frappe.ui.form.on("Stock Entry", {
    onload: function(frm){
        frappe.db.get_value("Company", frm.doc.company, "maintain_as_is_new", function(c) {
            if(!c.maintain_as_is_new) {
                frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
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
                if(frm.doc.__islocal){

                    frm.doc.items.forEach(function (d){
                        if (d.qty && d.quantity == 0) {
                            frappe.model.set_value(d.doctype, d.name, "quantity", d.qty);
                        }
                        if(d.basic_rate && d.price == 0){
                            frappe.model.set_value(d.doctype, d.name, "price", d.basic_rate);
                        }
                    });
                    frm.refresh_field('items');
                }

                if(frm.doc.work_order){
                    frappe.db.get_value("Work Order", frm.doc.work_order, 'skip_transfer', function (r) {
                        if (r.skip_transfer == 1) {
                            cur_frm.set_df_property("get_raw_materials", "hidden", 0);
                        }
                    });
                }
            } else {
                //
            }
        })
    },

    before_save: function (frm) {
        frappe.db.get_value("Company", frm.doc.company, 'abbr', function (r) {
            if (frm.doc.is_opening == "Yes") {
                $.each(frm.doc.items || [], function (i, d) {
                    d.expense_account = 'Temporary Opening - ' + r.abbr;
                });
            }
        });

        if (frm.doc.purpose == "Manufacture" && frm.doc.work_order) {
            frm.call({
                method: 'get_stock_and_rate',
                doc: frm.doc
            });
        }
    },
    validate: function(frm) {
        frm.trigger('cal_qty');
        if ((frm.doc.purpose == 'Material Receipt' || frm.doc.purpose =='Repack') && frappe.meta.get_docfield("Stock Entry", "reference_docname") && frappe.meta.get_docfield("Stock Entry", "jw_ref")) { 
            frappe.db.get_value("Company", frm.doc.company, "maintain_as_is_new", function(c) {
                if(!c.maintain_as_is_new) {
                        frm.doc.items.forEach(function (d) {     
                        if (!frm.doc.reference_docname && !frm.doc.jw_ref && !d.s_warehouse){
                                var packing_size = 0;
                                frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "tare_weight")){
                                            if (frappe.meta.get_docfield("Stock Entry Detail", "receive_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "receive_no_of_packages")){
                                                packing_size = (d.receive_packing_size - d.tare_weight)
                                                frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                                            }
                                        }
                                        else{
                                            if (frappe.meta.get_docfield("Stock Entry Detail", "receive_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "receive_no_of_packages")){
                                                packing_size = d.receive_packing_size
                                                frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                                            }                        
                                        }
                                    }
                                    else{
                                        if (d.packing_size && d.no_of_packages){
                                            frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                            frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                        }
                                    }
                    
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_qty")){
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "accepted_no_of_packages")){
                                            frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages));
                                    }
                                    }
                    
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_qty")){
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "supplier_no_of_packages")){
                                            frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages));
                                    }
                                    if(!d.supplier_qty){
                                        frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier Qty")
                                    }
                                    }
                    
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "receive_packing_size")){
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_packing_size")){
                                            frappe.model.set_value(d.doctype, d.name, 'packing_size', d.accepted_packing_size || packing_size);
                                            frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.accepted_no_of_packages || d.receive_no_of_packages);
                                        }
                                        else{
                                            frappe.model.set_value(d.doctype, d.name, 'packing_size',packing_size);
                                            frappe.model.set_value(d.doctype, d.name, 'no_of_packages',d.receive_no_of_packages);
                                        }
                                    }
                    
                                    if(r.maintain_as_is_stock){
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty) * d.received_concentration / 100);
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_concentration")){
                                            if(!d.supplier_concentration){
                                                frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier concentration")
                                            }
                                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty) * d.supplier_concentration / 100);
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty) * d.accepted_concentration / 100);
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_qty") && frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                            frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration") && frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'concentration',d.accepted_concentration || d.received_concentration || 100);
                                        }
                                        if (!d.qty){
                                            if (frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                                frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                                            }
                                            else{
                                                frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                                            }
                                        }
                    
                                        if (!d.concentration){
                                            if (frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                                frappe.throw(d.doctype + " Row: "+ d.idx +" Please add received or accepted concentration")
                                            }
                                            else{
                                                frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add concentration")
                                            }
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_quantity") && frappe.meta.get_docfield("Stock Entry Detail", "receive_quantity")){
                                            frappe.model.set_value(d.doctype, d.name, 'quantity',d.accepted_quantity || d.receive_quantity);
                                        }
                    
                                        else{
                                            if(!d.concentration){
                                                frappe.model.set_value(d.doctype, d.name, 'd.concentration',100);
                                            }
                                            frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty)*flt(d.concentration)/100);
                                        }
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_quantity")){
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                                        }
                                        else{
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate',flt(d.quantity) * flt(d.price) / flt(d.qty));
                                        }
                                    }
                                    else{
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty));
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty));
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty));
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_qty") && frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                            frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration") && frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                            frappe.model.set_value(d.doctype, d.name, 'concentration',flt(d.accepted_concentration) || flt(d.received_concentration || 100));
                                        }
                    
                                        if (!d.qty){
                                            if (frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                                frappe.throw(d.doctype + " Row: "+ d.idx +" Please add Receive Qty or Accepted Qty")
                                            }
                                            else{
                                                frappe.throw(d.doctype + " Row: "+ d.idx +"  Please add Qty")
                                            }
                                        }
                    
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_quantity") && frappe.meta.get_docfield("Stock Entry Detail", "receive_quantity")){
                                            frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.accepted_quantity) || flt(d.receive_quantity));
                                        }
                                        else{
                                            frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty));
                                        }
                                        if(d.price && !d.set_basic_rate_manually){
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate',d.price);
                                        }
                                    }
                    
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "short_quantity")){
                                        frappe.model.set_value(d.doctype, d.name, 'short_quantity',flt(d.quantity) - flt(d.supplier_quantity));
                                        if(d.short_quantity){
                                            frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                                        }
                                    }
                    
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "amount_difference")){
                                        frappe.model.set_value(d.doctype, d.name, 'amount_difference',flt(d.price) * flt(d.short_quantity));
                                    }
                    
                                });
                    
                        }
                        else{
                            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                                if (d.packing_size && d.no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                                    if (r.maintain_as_is_stock) {
                                        if (!d.concentration) {
                                            frappe.model.set_value(d.doctype, d.name,'concentration',100)
                                            //frappe.throw("Please add concentration for Item " + d.item_code)
                                        }
                                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                                    }
                                    else {
                                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                                    }
                                }
                                else {
                                    if (r.maintain_as_is_stock) {
                                        if (!d.concentration && d.t_warehouse) {
                                            //frappe.throw("Please add concentration for Item " + d.item_code);
                                        }
                                        let concentration = 0
                                        concentration = d.concentration
                                        if (d.quantity) {
                                            frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / concentration));
                                        }
                                        if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.quantity * d.price) / flt(d.qty));
                                        }
                                    }
                                    else {
                                        if (d.quantity) {
                                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                                        }
                                        if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.price));
                                        }
                                    }
                                }
                                
                            })
                        }
                    })
                } else {
                    frm.doc.items.forEach(function(d) {
                        if(!d.ignore_calculation) {
                            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                                if(r.maintain_as_is_stock && d.packing_size * d.no_of_packages * d.concentration){
                                    frappe.model.set_value(d.doctype, d.name, 'qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                    frappe.model.set_value(d.doctype, d.name, 'received_qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                } else {
                                    if (d.packing_size && d.no_of_packages) {
                                        packing_size = d.packing_size
                                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                        frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                    }
                                }
                            });
                        } else {
                            if(d.ignore_calculation){
                                if (d.packing_size && d.no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                }
                            }
                        }
                    });
                }
            });
        }
            else{
                frappe.db.get_value("Company", frm.doc.company, "maintain_as_is_new", function(c) {
                    if(!c.maintain_as_is_new) {
                        frm.doc.items.forEach(function (d) {
                            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                                if (d.packing_size && d.no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                                    if (r.maintain_as_is_stock) {
                                        if (!d.concentration) {
                                            frappe.model.set_value(d.doctype, d.name,'concentration',100)
                                        //     frappe.throw("Please add concentration for Item " + d.item_code)
                                        }
                                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                                        if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.quantity * d.price) / flt(d.qty));
                                        }
                                    }
                                    else {
                                        frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                                        if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.price));
                                        }
                                    }
                                }
                                else {
                                    if (r.maintain_as_is_stock) {
                                        if (!d.concentration && d.t_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name,'concentration',100)
                                        //     frappe.throw("Please add concentration for Item " + d.item_code)
                                        }
                                        let concentration = 0

                                        concentration = d.concentration
                                        if (d.quantity) {
                                            frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / concentration));
                                        }
                                        if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.quantity * d.price) / flt(d.qty));
                                        }
                                    }
                                    else {
                                        if (d.quantity) {
                                            frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                                        }
                                        if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.price));
                                        }
                                    }
                                }		
                            })
                        });
                    } else {
                        frm.doc.items.forEach(function(d) {
                            if(!d.ignore_calculation) {
                                frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                                    if(r.maintain_as_is_stock && d.packing_size * d.no_of_packages * d.concentration){
                                        frappe.model.set_value(d.doctype, d.name, 'qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                        frappe.model.set_value(d.doctype, d.name, 'received_qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                    } else {
                                        if (d.packing_size && d.no_of_packages) {
                                            packing_size = d.packing_size
                                            frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                            frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                        }
                                    }
                                });
                            } else {
                                if(d.ignore_calculation){
                                    if (d.packing_size && d.no_of_packages) {
                                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                    }
                                }
                            }
                        });
                    }
                });
            }
                
    },
    cal_rate_qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        if ((frm.doc.purpose == 'Material Receipt' || frm.doc.purpose =='Repack') && frappe.meta.get_docfield("Stock Entry", "reference_docname") && frappe.meta.get_docfield("Stock Entry", "jw_ref")) {
            frappe.db.get_value("Company", frm.doc.company, "maintain_as_is_new", function(c) {
                if(!c.maintain_as_is_new) {
                    if (!frm.doc.reference_docname && !frm.doc.jw_ref && !d.s_warehouse){
                            var packing_size = 0;
                            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                                if (frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "tare_weight")){
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "receive_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "receive_no_of_packages")){
                                            packing_size = (d.receive_packing_size - d.tare_weight)
                                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                                        }
                                    }
                                    else{
                                        if (frappe.meta.get_docfield("Stock Entry Detail", "receive_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "receive_no_of_packages")){
                                            packing_size = d.receive_packing_size
                                            frappe.model.set_value(d.doctype, d.name, 'receive_qty', packing_size * d.receive_no_of_packages);
                                        }                        
                                    }
                                }
                                else{
                                    if (d.packing_size && d.no_of_packages){
                                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                        frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                    }
                                }
                
                                if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_qty")){
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "accepted_no_of_packages")){
                                        frappe.model.set_value(d.doctype, d.name, 'accepted_qty', flt(d.accepted_packing_size) * flt(d.accepted_no_of_packages));
                                }
                                }
                
                                if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_qty")){
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_packing_size") && frappe.meta.get_docfield("Stock Entry Detail", "supplier_no_of_packages")){
                                        frappe.model.set_value(d.doctype, d.name, 'supplier_qty', flt(d.supplier_packing_size) * flt(d.supplier_no_of_packages));
                                }
                                if(!d.supplier_qty){
                                    // frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier Qty")
                                }
                                }
                
                                if (frappe.meta.get_docfield("Stock Entry Detail", "receive_packing_size")){
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_packing_size")){
                                        frappe.model.set_value(d.doctype, d.name, 'packing_size', d.accepted_packing_size || packing_size);
                                        frappe.model.set_value(d.doctype, d.name, 'no_of_packages', d.accepted_no_of_packages || d.receive_no_of_packages);
                                    }
                                    else{
                                        frappe.model.set_value(d.doctype, d.name, 'packing_size',packing_size);
                                        frappe.model.set_value(d.doctype, d.name, 'no_of_packages',d.receive_no_of_packages);
                                    }
                                }
                
                                if(r.maintain_as_is_stock){
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty) * d.received_concentration / 100);
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_concentration")){
                                        if(!d.supplier_concentration){
                                        // frappe.throw(d.doctype + " Row: "+ d.idx +" Please add supplier concentration")
                                        }
                                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty) * d.supplier_concentration / 100);
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty) * d.accepted_concentration / 100);
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_qty") && frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                        frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration") && frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'concentration',d.accepted_concentration || d.received_concentration || 100);
                                    }
                
                                    if (!d.concentration){
                                        frappe.model.set_value(d.doctype, d.name, 'concentration',100);
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_quantity") && frappe.meta.get_docfield("Stock Entry Detail", "receive_quantity")){
                                        frappe.model.set_value(d.doctype, d.name, 'quantity',d.accepted_quantity || d.receive_quantity);
                                    }
                
                                    else{
                                        frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty)*flt(d.concentration)/100);
                                    }
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_quantity")){
                                        frappe.model.set_value(d.doctype, d.name, 'basic_rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                                    }
                                    else{
                                        if(d.price && !d.set_basic_rate_manually & !d.s_warehouse){

                                            frappe.model.set_value(d.doctype, d.name, 'basic_rate',flt(d.quantity) * flt(d.price) / flt(d.qty));
                                        }
                                    }
                                }
                                else{
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'receive_quantity',flt(d.receive_qty));
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "supplier_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'supplier_quantity',flt(d.supplier_qty));
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'accepted_quantity',flt(d.accepted_qty));
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_qty") && frappe.meta.get_docfield("Stock Entry Detail", "receive_qty")){
                                        frappe.model.set_value(d.doctype, d.name, 'qty',flt(d.accepted_qty) || flt(d.receive_qty));
                                    }
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_concentration") && frappe.meta.get_docfield("Stock Entry Detail", "received_concentration")){
                                        frappe.model.set_value(d.doctype, d.name, 'concentration',flt(d.accepted_concentration) || flt(d.received_concentration) || 100);
                                    }
                
                
                                    if (frappe.meta.get_docfield("Stock Entry Detail", "accepted_quantity") && frappe.meta.get_docfield("Stock Entry Detail", "receive_quantity")){
                                        frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.accepted_quantity) || flt(d.receive_quantity));
                                    }
                                    else{
                                        frappe.model.set_value(d.doctype, d.name, 'quantity',flt(d.qty));
                                    }
                                    if(d.price && !d.set_basic_rate_manually & !d.s_warehouse){

                                        frappe.model.set_value(d.doctype, d.name, 'basic_rate',d.price);
                                    }
                                }
                
                                if (frappe.meta.get_docfield("Stock Entry Detail", "short_quantity")){
                                    frappe.model.set_value(d.doctype, d.name, 'short_quantity',flt(d.quantity) - flt(d.supplier_quantity));
                                    if(d.short_quantity){
                                        frappe.model.set_value(d.doctype, d.name, 'rate',flt(d.supplier_quantity) * flt(d.price) / flt(d.qty));
                                    }
                                }
                
                                if (frappe.meta.get_docfield("Stock Entry Detail", "amount_difference")){
                                    frappe.model.set_value(d.doctype, d.name, 'amount_difference',flt(d.price) * flt(d.short_quantity));
                                }
                
                            });        
                    }
                    else {frm.events.se_cal_rate_qty(frm,cdt,cdn) }
                } else {
                    frm.doc.items.forEach(function(d) {
                        if(!d.ignore_calculation) {
                            frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                                if(r.maintain_as_is_stock && d.packing_size * d.no_of_packages * d.concentration){
                                    frappe.model.set_value(d.doctype, d.name, 'qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                    frappe.model.set_value(d.doctype, d.name, 'received_qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                } else {
                                    if (d.packing_size && d.no_of_packages) {
                                        packing_size = d.packing_size
                                        frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                        frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                    }
                                }
                            });
                        } else {
                            if(d.ignore_calculation){
                                if (d.packing_size && d.no_of_packages) {
                                    frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                }
                            }
                        }
                    });
                }
            });
        }
        else {
            frappe.db.get_value("Company", frm.doc.company, "maintain_as_is_new", function(c) {
                if(!c.maintain_as_is_new) {
                    frm.events.se_cal_rate_qty(frm,cdt,cdn) 
                }
            });
        }
    },
    se_cal_rate_qty: function(frm,cdt,cdn){
        var d = locals[cdt][cdn];
        frappe.db.get_value("Company", frm.doc.company, "maintain_as_is_new", function(c) {
            if(!c.maintain_as_is_new) {
                frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function (r) {
                    if(d.concentration){
                        frappe.model.set_value(d.doctype, d.name, 'concentration',d.concentration);
                    }else{
                        frappe.model.set_value(d.doctype, d.name, 'concentration',100);
                    }
                    
                    if (d.packing_size && d.no_of_packages) {
                        frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.packing_size * d.no_of_packages));
                        if (r.maintain_as_is_stock) {
                            if (!d.concentration) {
                                frappe.model.set_value(d.doctype, d.name, 'concentration',100);
                            }
                            frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty * d.concentration / 100);
                        }
                        else {
                            frappe.model.set_value(d.doctype, d.name, 'quantity', d.qty);
                        }
                    }
                    else {
                        if (r.maintain_as_is_stock) {
                        
                            let concentration = 0

                            concentration = d.concentration
                            if (d.quantity) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt((d.quantity * 100.0) / concentration));
                            }
                            if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.quantity * d.price) / flt(d.qty));
                            }
                        }
                        else {
                            if (d.quantity) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', flt(d.quantity));
                            }
                            if (d.price && !d.set_basic_rate_manually & !d.s_warehouse) {
                                frappe.model.set_value(d.doctype, d.name, 'basic_rate', flt(d.price));
                            }
                        }
                    }
                    
                })
            } else {
                frm.doc.items.forEach(function(d) {
                    if(!d.ignore_calculation) {
                        frappe.db.get_value("Item", d.item_code, 'maintain_as_is_stock', function(r) {
                            if(r.maintain_as_is_stock && d.packing_size * d.no_of_packages * d.concentration){
                                frappe.model.set_value(d.doctype, d.name, 'qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                                frappe.model.set_value(d.doctype, d.name, 'received_qty', (d.packing_size * d.no_of_packages * d.concentration) / 100.0);
                            } else {
                                if (d.packing_size && d.no_of_packages) {
                                    packing_size = d.packing_size
                                    frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                                    frappe.model.set_value(d.doctype, d.name, 'received_qty', d.packing_size * d.no_of_packages);
                                }
                            }
                        });
                    } else {
                        if(d.ignore_calculation){
                            if (d.packing_size && d.no_of_packages) {
                                frappe.model.set_value(d.doctype, d.name, 'qty', d.packing_size * d.no_of_packages);
                            }
                        }
                    }
                });
            }
        });

    },
    stock_entry_type: function(frm){
        if(frm.doc.stock_entry_type=="Send to Jobwork" || frm.doc.stock_entry_type=="Send Jobwork Finish" ){
            if (frappe.meta.get_docfield("Stock Entry Detail", "send_to_party")){
                frm.set_value("send_to_party",1)
                frm.set_value("receive_from_party",0)
            }

        }
        else if(frm.doc.stock_entry_type=="Receive Jobwork Raw Material" || frm.doc.stock_entry_type=="Receive Jobwork Return" ){
            if (frappe.meta.get_docfield("Stock Entry Detail", "send_to_party")){
                frm.set_value("receive_from_party",1)
                frm.set_value("send_to_party",0)
            }
        }
        else{
            if (frappe.meta.get_docfield("Stock Entry Detail", "send_to_party")){
                frm.set_value("receive_from_party",0)
                frm.set_value("send_to_party",0)
            }
        }
        if(frm.doc.purpose == "Repack"){
            frm.doc.from_warehouse = ""
            frm.doc.to_warehouse = ""
        }
       
    },
    
    set_basic_rate: function (frm, cdt, cdn) {
        const item = locals[cdt][cdn];
        if (item.t_warehouse) {
            return
        }
        item.transfer_qty = flt(item.qty) * flt(item.conversion_factor);

        let batch = '';
        if (!item.t_warehouse) {
            batch = item.batch_no;
        }

        const args = {
            'item_code': item.item_code,
            'posting_date': frm.doc.posting_date,
            'posting_time': frm.doc.posting_time,
            'warehouse': cstr(item.s_warehouse) || cstr(item.t_warehouse),
            'serial_no': item.serial_no,
            'company': frm.doc.company,
            'qty': item.s_warehouse ? -1 * flt(item.transfer_qty) : flt(item.transfer_qty),
            'voucher_type': frm.doc.doctype,
            'voucher_no': item.name,
            'allow_zero_valuation': 1,
            'batch_no': batch || ''
        };

        if (item.item_code || item.serial_no) {
            frappe.call({
                method: "erpnext.stock.utils.get_incoming_rate",
                args: {
                    args: args
                },
                callback: function (r) {
                    if(!item.set_basic_rate_manually){
                        frappe.model.set_value(cdt, cdn, 'basic_rate', (r.message || 0.0));
                    }
                    frm.events.calculate_basic_amount(frm, item);
                }
            });
        }
    },

    cal_qty: function (frm) {
        let qty = 0;
        frm.doc.items.forEach(function (d) {
            if (d.batch_no && d.s_warehouse) {
                frappe.db.get_value("Batch", d.batch_no, ['packaging_material', 'packing_size', 'lot_no', 'batch_yield', 'concentration'], function (r) {
                    frappe.model.set_value(d.doctype, d.name, 'packaging_material', r.packaging_material);
                    frappe.model.set_value(d.doctype, d.name, 'packing_size', r.packing_size);
                    frappe.model.set_value(d.doctype, d.name, 'lot_no', r.lot_no);
                    frappe.model.set_value(d.doctype, d.name, 'batch_yield', r.batch_yield);
                    frappe.model.set_value(d.doctype, d.name, 'concentration', r.concentration);
                })
            }

        });
    }
});

frappe.ui.form.on("Stock Entry Detail", {
    form_render: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        var item_grid = frm.get_field('items').grid;
        let batch_no = item_grid.grid_rows[d.idx - 1].get_field('batch_no');
        if (!in_list(["Material Issue", "Material Transfer", "Material Transfer for Manufacture"], frm.doc.purpose)) {
            if (d.s_warehouse) {
                batch_no.df.read_only = 0;
            }
            else if (d.t_warehouse) {
                batch_no.df.read_only = 1;
            }
        }
    },
    s_warehouse: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        var item_grid = frm.get_field('items').grid;
        let batch_no = item_grid.grid_rows[d.idx - 1].get_field('batch_no');
        if (!in_list(["Material Issue", "Material Transfer", "Material Transfer for Manufacture"], frm.doc.purpose)) {
            if (d.s_warehouse) {
                batch_no.df.read_only = 0;
            }
            else if (d.t_warehouse) {
                batch_no.df.read_only = 1;
            }
        }
    },
    t_warehouse: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];
        var item_grid = frm.get_field('items').grid;
        let batch_no = item_grid.grid_rows[d.idx - 1].get_field('batch_no');
        if (!in_list(["Material Issue", "Material Transfer", "Material Transfer for Manufacture"], frm.doc.purpose)) {
            if (d.s_warehouse) {
                batch_no.df.read_only = 0;
            }
            else if (d.t_warehouse) {
                batch_no.df.read_only = 1;
            }
        }
        frm.refresh_field('items');
    },

    conversion_factor: function (frm, cdt, cdn) {
        frm.events.set_basic_rate(frm, cdt, cdn);
    },

    qty: function (frm, cdt, cdn) {
        let d = locals[cdt][cdn];

        frm.events.set_serial_no(frm, cdt, cdn, () => {
            frm.events.set_basic_rate(frm, cdt, cdn);
        });
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    quantity: function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    price: function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },   
    concentration: function(frm, cdt, cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    packing_size: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    no_of_packages: function (frm, cdt, cdn) {
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    batch_no:function(frm,cdt,cdn){
        frm.events.cal_qty(frm)
    },
    supplier_no_of_packages:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_packing_size:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    receive_no_of_packages:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    receive_packing_size:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_no_of_packages:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_packing_size:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    accepted_concentration:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    supplier_concentration:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    },
    received_concentration:function(frm,cdt,cdn){
        frm.events.cal_rate_qty(frm, cdt, cdn)
    }

});

erpnext.stock.select_batch_and_serial_no = (frm, item) => {

}