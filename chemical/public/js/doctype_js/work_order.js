frappe.ui.form.on("Work Order", {
    onload: function (frm) {
        // Ensure BOM is fetched if bom_no exists
        if (frm.doc.bom_no) {
            frappe.db.get_value("BOM", frm.doc.bom_no, 'is_multiple_item', function (r) {
                if (r && r.is_multiple_item) {
                    frm.fields_dict['total_qty'].df.hidden = false;
                } else {
                    frm.fields_dict['total_qty'].df.hidden = true;
                }
                frm.refresh_field('total_qty'); // Refresh field to apply visibility changes
            });
        }
    },

    bom_no: function (frm) {
        // Handle case when bom_no changes
        if (frm.doc.bom_no) {
            frappe.db.get_value("BOM", frm.doc.bom_no, 'is_multiple_item', function (r) {
                if (r && r.is_multiple_item) {
                    frm.fields_dict['total_qty'].df.hidden = false;
                } else {
                    frm.fields_dict['total_qty'].df.hidden = true;
                }
                frm.refresh_field('total_qty'); // Refresh field to apply visibility changes
            });
        } else {
            // Hide total_qty if bom_no is not set
            frm.fields_dict['total_qty'].df.hidden = true;
            frm.refresh_field('total_qty');
        }
    }
});


// cur_frm.add_fetch('bom_no', 'based_on', 'based_on');
// cur_frm.add_fetch('bom_no', 'batch_yield', 'batch_yield');


// if (cur_frm.doc.skip_transfer && !cur_frm.doc.__islocal) {
// 	cur_frm.dashboard.add_transactions({
// 		'label': '',
// 		'items': ['Material Transfer Instruction']
// 	});
// }
// frappe.ui.form.on("Work Order", {
// 	onload: function (frm) {
// 		frm.set_query("bom_no", function (doc) {
// 			return {
// 				filters: {
// 					"item": doc.production_item,
// 					'is_active': 1,
// 					'docstatus': 1,
// 					"company": doc.company
// 				}
// 			}
// 		})
// 		if (frm.doc.__islocal) {
// 			if (frm.doc.bom_no) {
// 				frappe.db.get_value("BOM", frm.doc.bom_no, ["based_on", "batch_yield", "is_multiple_item"], function (r) {
// 					if (r) {
// 						frm.set_value("based_on", r.based_on);
// 						frm.set_value("batch_yield", r.batch_yield);
// 						frm.set_value("is_multiple_item", r.is_multiple_item);
// 					}
// 				})
// 			}
// 		}
// 		frm.trigger('set_source_warehouse')
// 	},
// 	refresh: function (frm) {
// 	},
// 	set_source_warehouse: function (frm) {
// 		if (frm.doc.company) {
// 			if (frappe.meta.get_docfield(frm.doc.doctype, "source_warehouse")) {
// 				if (!frm.doc.source_warehouse) {
// 					frappe.db.get_value("Company", frm.doc.company, 'default_raw_material_warehouse', function (r) {
// 						if (r.default_raw_material_warehouse) {
// 							frm.set_value('source_warehouse', r.default_raw_material_warehouse);
// 						}
// 					})
// 				}
// 			}
// 		}
// 	},
// 	qty: function (frm) {
// 		frm.trigger('source_warehouse')
// 	},
// 	source_warehouse: function (frm) {
// 		if (frappe.meta.get_docfield(frm.doc.doctype, "source_warehouse")) {
// 			if (frm.doc.source_warehouse) {
// 				if (frm.doc.required_items) {
// 					frm.doc.required_items.forEach(function (d) {
// 						frappe.model.set_value(d.doctype, d.name, 'source_warehouse', frm.doc.source_warehouse)
// 					});
// 				}
// 			}
// 		}
// 	},
// 	before_save: function (frm) {
// 		if (frm.doc.based_on_qty) {
// 			let qty = flt(frm.doc.batch_yield * frm.doc.based_on_qty, 3);
// 			frm.set_value('qty', qty);
// 		}
// 		if (frm.doc.volume) {
// 			cost = flt(frm.doc.volume * frm.doc.volume_rate);
// 			frm.set_value('volume_cost', cost);
// 		}
// 	},
// 	bom_no: function (frm) {
// 		frappe.run_serially([
// 			() => frappe.db.get_value("BOM", frm.doc.bom_no, ["based_on", "batch_yield", "is_multiple_item"], function (r) {
// 				if (r) {
// 					frm.set_value("based_on", r.based_on);
// 					frm.set_value("batch_yield", r.batch_yield);
// 					frm.set_value("is_multiple_item", r.is_multiple_item);
// 				}
// 			}),
// 		]);
// 	},
// 	based_on: function (frm) {
// 		if (frm.doc.based_on) {
// 			cur_frm.set_df_property('based_on_qty', 'label', "Required " + cstr(frm.doc.based_on) + " Qty");
// 		}
// 	},
// 	based_on_qty: function (frm) {
// 		if (!frm.doc.based_on) {
// 			frappe.db.get_value("BOM", frm.doc.bom_no, "based_on", function (r) {
// 				if (r) {
// 					frm.set_value("based_on", r.based_on)
// 				}
// 			});
// 		} else {
// 			let qty = flt(frm.doc.batch_yield * frm.doc.based_on_qty);
// 			frm.set_value('qty', flt(qty, precision("qty")));
// 		}
// 	},
// 	volume_rate: function (frm) {
// 		cost = flt(frm.doc.volume * frm.doc.volume_rate);
// 		frm.set_value('volume_cost', cost);
// 	},
// 	volume: function (frm) {
// 		cost = flt(frm.doc.volume * frm.doc.volume_rate);
// 		frm.set_value('volume_cost', cost);
// 	},

// 	make_transfer: function (frm) {
// 		var max_qty = flt(frm.doc.qty) - flt(frm.doc.material_transferred_for_instruction);
// 		max_qty = flt(max_qty, precision("qty"));
// 		frappe.call({
// 			method: "chemical.chemical.override.doctype.work_order.make_stock_entry",
// 			args: {
// 				"work_order_id": frm.doc.name,
// 				"qty": max_qty
// 			},
// 			callback: function (r) {
// 				var doclist = frappe.model.sync(r.message);
// 				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
// 			}
// 		});
// 	},

// 	show_progress: function (frm) {
// 		var bars = [];
// 		var message = '';
// 		var added_min = false;

// 		// produced qty
// 		var title = __('{0} items produced', [frm.doc.produced_qty]);
// 		bars.push({
// 			'title': title,
// 			'width': (frm.doc.produced_qty / frm.doc.qty * 100) + '%',
// 			'progress_class': 'progress-bar-success'
// 		});
// 		if (bars[0].width == '0%') {
// 			bars[0].width = '0.5%';
// 			added_min = 0.5;
// 		}
// 		message = title;
// 		// pending qty
// 		if (!frm.doc.skip_transfer) {
// 			var pending_complete = frm.doc.material_transferred_for_manufacturing - frm.doc.produced_qty;
// 			if (pending_complete) {
// 				var title = __('{0} items in progress', [pending_complete]);
// 				var width = ((pending_complete / frm.doc.qty * 100) - added_min);
// 				bars.push({
// 					'title': title,
// 					'width': (width > 100 ? "99.5" : width) + '%',
// 					'progress_class': 'progress-bar-warning'
// 				})
// 				message = message + '. ' + title;
// 			}
// 		}

// 		else if (frm.doc.skip_transfer && frm.doc.material_transferred_for_instruction) {
// 			var pending_complete = frm.doc.material_transferred_for_instruction - frm.doc.produced_qty;
// 			if (pending_complete) {
// 				var title = __('{0} items in progress', [pending_complete]);
// 				var width = ((pending_complete / frm.doc.qty * 100) - added_min);
// 				bars.push({
// 					'title': title,
// 					'width': (width > 100 ? "99.5" : width) + '%',
// 					'progress_class': 'progress-bar-warning'
// 				})
// 				message = message + '. ' + title;
// 			}
// 		}

// 		let bar = cur_frm.dashboard.progress_area.find('div')[0];
// 		bar.hidden = true;

// 		let p = cur_frm.dashboard.progress_area.find('p')[0];
// 		p.hidden = true;

// 		frm.dashboard.add_progress(__('Status'), bars, message);
// 	},

// });
