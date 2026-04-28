frappe.ui.form.on("Batch", {
	onload_post_render: function(frm) {
		setTimeout( () => {
			$("div").remove(".form-dashboard-section.custom");
		}, 20)
		setTimeout( () => {
			frm.trigger('_make_dashboard')
		}, 40)
	},
	_make_dashboard: (frm) => {
		if(!frm.is_new()) {
			frappe.call({
				method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
				args: {batch_no: frm.doc.name},
				callback: (r) => {
					if(!r.message) {
						return;
					}
					frappe.db.get_value("Item",frm.doc.item,'maintain_as_is_stock',function(m){
						var section = frm.dashboard.add_section(`<h5 style="margin-top: 0px;">
						${ __("Stock Levels") }</a></h5>`);

					// sort by qty
					r.message.sort(function(a, b) { a.qty > b.qty ? 1 : -1 });

					var rows = $('<div></div>').appendTo(section);

					// show
					(r.message || []).forEach(function(d) {
						let actual_qty = 0
						if(m.maintain_as_is_stock) {
							actual_qty = flt(d.qty * frm.doc.concentration / 100)
						}
						else{
							actual_qty = d.qty
						}
						if(d.qty > 0) {
							$(`<div class='row' style='margin-bottom: 10px;'>
								<div class='col-sm-3 small' style='padding-top: 3px;'>${d.warehouse}</div>

								<div class='col-sm-3 small text-right' style='padding-top: 3px;'>${d.qty} (${actual_qty})</div>
								<div class='col-sm-6'>
									<button class='btn btn-default btn-xs btn-move' style='margin-right: 7px;'
										data-qty = "${d.qty}"
										data-warehouse = "${d.warehouse}">
										${__('Move')}</button>
									<button class='btn btn-default btn-xs btn-split'
										data-qty = "${d.qty}"
										data-warehouse = "${d.warehouse}">
										${__('Split')}</button>
								</div>
							</div>`).appendTo(rows);
						}
					});

					// move - ask for target warehouse and make stock entry
					rows.find('.btn-move').on('click', function() {
						var $btn = $(this);
						const fields = [
							{
								fieldname: 'to_warehouse',
								label: __('To Warehouse'),
								fieldtype: 'Link',
								options: 'Warehouse'
							}
						];

						frappe.prompt(
							fields,
							(data) => {
								frappe.call({
									method: 'erpnext.stock.doctype.stock_entry.stock_entry_utils.make_stock_entry',
									args: {
										item_code: frm.doc.item,
										batch_no: frm.doc.name,
										qty: $btn.attr('data-qty'),
										from_warehouse: $btn.attr('data-warehouse'),
										to_warehouse: data.to_warehouse,
										source_document: frm.doc.reference_name,
										reference_doctype: frm.doc.reference_doctype
									},
									callback: (r) => {
										frappe.show_alert(__('Stock Entry {0} created',
											['<a href="#Form/Stock Entry/'+r.message.name+'">' + r.message.name+ '</a>']));
										frm.refresh();
									},
								});
							},
							__('Select Target Warehouse'),
							__('Move')
						);
					});

					// split - ask for new qty and batch ID (optional)
					// and make stock entry via batch.batch_split
					rows.find('.btn-split').on('click', function() {
						var $btn = $(this);
						frappe.prompt([{
							fieldname: 'qty',
							label: __('New Batch Qty'),
							fieldtype: 'Float',
							'default': $btn.attr('data-qty')
						},
						{
							fieldname: 'new_batch_id',
							label: __('New Batch ID (Optional)'),
							fieldtype: 'Data',
						}],
						(data) => {
							frappe.call({
								method: 'erpnext.stock.doctype.batch.batch.split_batch',
								args: {
									item_code: frm.doc.item,
									batch_no: frm.doc.name,
									qty: data.qty,
									warehouse: $btn.attr('data-warehouse'),
									new_batch_id: data.new_batch_id
								},
								callback: (r) => {
									frm.refresh();
								},
							});
						},
						__('Split Batch'),
						__('Split')
						);
					})

					});
					
				}
			});
		}
	}
});