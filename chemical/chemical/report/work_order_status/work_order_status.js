// Copyright (c) 2016, FinByz Tech Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

var checkedRowsData=[];
let column_length;
let unhighlight_list=[]
frappe.query_reports["Work Order Status"] = {
	"filters": [
        {
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"production_item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"reqd": 1
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("company")
		},
		{
			"fieldname":"finish_quantity",
			"label": __("Finish Quantity"),
			"fieldtype": "Float",
			"width": "80",
		},

	],
    get_datatable_options(options) {
		// for getting total length of cloumns
		if (options.columns) {
			column_length = options.columns.length;
		  }
        return Object.assign(options, {
            checkboxColumn: true,
            events: {
			},
		});
	},  
}
$(document).ready(function() {
	// on clicking for all check reinitialize list
    $(document).on("click", ".dt-cell--header input[type='checkbox']", function() {
		unhighlight_list=[]
    });

    $(document).on("click", ".dt-scrollable--highlight-all input[type='checkbox']", function() {
		var $row = $(this).closest(".dt-row");
		var value = $row.find("a").text().trim();
		// Check if the value is in the unhighlight_list
		var index = $.inArray(value, unhighlight_list);
		if (index !== -1) {
			// If the value is already in the list, remove it
			unhighlight_list.splice(index, 1);
		} else {
			// If the value is not in the list, push it
			unhighlight_list.push(value);
		}
    });

	frappe.query_report.page.set_primary_action('Create BOM', function () {
		let d = new frappe.ui.Dialog({
			title: 'Enter Details',
			fields: [
				{
					label: 'Rate Of Materials Based On',
					fieldname: 'rm_cost_as_per',
					fieldtype: 'Select',
					options: ["Valuation Rate", "Last Purchase Rate", "Price List"],
					reqd: 1
				},
				{
					label: 'Price List',
					fieldname: 'price_list',
					fieldtype: 'Link',
					options: "Price List",
					depends_on: 'eval:doc.rm_cost_as_per==="Price List"',
					mandatory_depends_on: 'eval:doc.rm_cost_as_per==="Price List"'
				}
			],
			size: 'small', // small, large, extra-large 
			primary_action_label: 'Create BOM',
			primary_action(values) {
				console.log(values)
				var element = $('.dt-scrollable');
				// work on when you select all the row option by checking all select checkbox
				if (element.hasClass('dt-scrollable--highlight-all'))
				{
					checkedRowsData=[]
					$(".dt-row--unhighlight").each(function() {
						var value = $(this).find("a").text();
						checkedRowsData.push(value)
					});
					var productionItemValue = frappe.query_report.get_filter_value('production_item');
					var finish_quantity = frappe.query_report.get_filter_value('finish_quantity');
					if (finish_quantity === undefined || finish_quantity === null || finish_quantity === 0) {
						frappe.throw("Finish Quantity is required.");
					} 
					frappe.call({
						method: "chemical.chemical.report.work_order_status.work_order_status.create_bom_for_all_row",
						args: {
							doc:unhighlight_list,
							productionItemValue:productionItemValue,
							finish_quantity:finish_quantity,
							rm_cost_as_per:values.rm_cost_as_per,
							price_list:values.price_list
						},
						callback: function(response) {
							if (response.message== 'Successful') {
								frappe.msgprint("BOM created successfully!");
							}
						}
					});
					checkedRowsData=[];
				}
				else {
					checkedRowsData=[]
					$(".dt-row--highlight").each(function() {
						var dict={}
						var value = $(this).find("a").text();
						dict[$('.dt-row-header').find(".dt-cell__content--header-2").text().trim()]=value.trim();
						// traversing the rest column value
						for(var i=3;i<column_length+2;i++)
						{
							var header_value=".dt-cell__content--header-"+i
							var selector = ".dt-cell__content--col-" + i;
							var val= $(this).find(selector).text();
							dict[$('.dt-row-header').find(header_value).text().trim()]=val.trim();
							
						}
						checkedRowsData.push(dict)
					});
					var productionItemValue = frappe.query_report.get_filter_value('production_item');
					var finish_quantity = frappe.query_report.get_filter_value('finish_quantity');
					if (finish_quantity === undefined || finish_quantity === null || finish_quantity === 0) {
						frappe.throw("Finish Quantity is required.");
					} 
					if (checkedRowsData.length === 0) {
						frappe.throw("Please select at least one row to create a BOM.");
					}
					frappe.call({
						method: "chemical.chemical.report.work_order_status.work_order_status.create_bom",
						args: {
							doc:checkedRowsData,
							productionItemValue:productionItemValue,
							finish_quantity:finish_quantity,
							rm_cost_as_per:values.rm_cost_as_per,
							price_list:values.price_list
						},
						callback: function(response) {
							if (response.message== 'Successful') {
								frappe.msgprint("BOM created successfully!");
							}
						}
					});
					checkedRowsData=[];
				}
				
				d.hide();
			}
		});
		
		d.show();
	})
});