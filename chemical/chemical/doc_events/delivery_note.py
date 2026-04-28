import frappe
from frappe import msgprint, _
from frappe.utils import flt, cint
from chemical.api import cal_rate_qty, quantity_price_to_qty_rate

def onload(self,method):
	quantity_price_to_qty_rate(self)

def before_validate(self,method):
	cal_rate_qty(self)
	cal_qty(self, method)

def on_submit(self, method):
	validate_customer_batch(self)

def before_cancel(self, method):
	dn_update_status_updater_args(self)

def before_submit(self, method):
	dn_update_status_updater_args(self)

def dn_update_status_updater_args(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		self.status_updater = [{
			'source_dt': 'Delivery Note Item',
			'target_dt': 'Sales Order Item',
			'join_field': 'so_detail',
			'target_field': 'delivered_qty', # In Sales Order Item
			'target_parent_dt': 'Sales Order',
			'target_parent_field': 'per_delivered',
			'target_ref_field': 'quantity', # In Sales Order Item
			'source_field': 'quantity', # In Delivery Note Item
			'percent_join_field': 'against_sales_order',
			'status_field': 'delivery_status',
			'keyword': 'Delivered',
			'second_source_dt': 'Sales Invoice Item',
			'second_source_field': 'quantity', # In Sales Invoice Item
			'second_join_field': 'so_detail',
			'overflow_type': 'delivery',
			'second_source_extra_cond': """ and exists(select name from `tabSales Invoice`
				where name=`tabSales Invoice Item`.parent and update_stock = 1)"""
		},
		{
			'source_dt': 'Delivery Note Item',
			'target_dt': 'Sales Invoice Item',
			'join_field': 'si_detail',
			'target_field': 'delivered_qty',
			'target_parent_dt': 'Sales Invoice',
			'target_ref_field': 'quantity', # In Sales Invoice Item
			'source_field': 'quantity', # In Delivery Note Item
			'percent_join_field': 'against_sales_invoice',
			'overflow_type': 'delivery',
			'no_allowance': 1
		}]

		if cint(self.is_return):
			self.status_updater.append({
				'source_dt': 'Delivery Note Item',
				'target_dt': 'Sales Order Item',
				'join_field': 'so_detail',
				'target_field': 'returned_qty',
				'target_parent_dt': 'Sales Order',
				'source_field': '-1 * quantity',
				'second_source_dt': 'Sales Invoice Item',
				'second_source_field': '-1 * quantity',
				'second_join_field': 'so_detail',
				'extra_cond': """ and exists (select name from `tabDelivery Note`
					where name=`tabDelivery Note Item`.parent and is_return=1)""",
				'second_source_extra_cond': """ and exists (select name from `tabSales Invoice`
					where name=`tabSales Invoice Item`.parent and is_return=1 and update_stock=1)"""
			})
	else:
		self.status_updater = [{
			'source_dt': 'Delivery Note Item',
			'target_dt': 'Sales Order Item',
			'join_field': 'so_detail',
			'target_field': 'delivered_qty', # In Sales Order Item
			'target_parent_dt': 'Sales Order',
			'target_parent_field': 'per_delivered',
			'target_ref_field': 'qty', # In Sales Order Item
			'source_field': 'qty', # In Delivery Note Item
			'percent_join_field': 'against_sales_order',
			'status_field': 'delivery_status',
			'keyword': 'Delivered',
			'second_source_dt': 'Sales Invoice Item',
			'second_source_field': 'qty', # In Sales Invoice Item
			'second_join_field': 'so_detail',
			'overflow_type': 'delivery',
			'second_source_extra_cond': """ and exists(select name from `tabSales Invoice`
				where name=`tabSales Invoice Item`.parent and update_stock = 1)"""
		},
		{
			'source_dt': 'Delivery Note Item',
			'target_dt': 'Sales Invoice Item',
			'join_field': 'si_detail',
			'target_field': 'delivered_qty',
			'target_parent_dt': 'Sales Invoice',
			'target_ref_field': 'qty', # In Sales Invoice Item
			'source_field': 'qty', # In Delivery Note Item
			'percent_join_field': 'against_sales_invoice',
			'overflow_type': 'delivery',
			'no_allowance': 1
		}]

		if cint(self.is_return):
			self.status_updater.append({
				'source_dt': 'Delivery Note Item',
				'target_dt': 'Sales Order Item',
				'join_field': 'so_detail',
				'target_field': 'returned_qty',
				'target_parent_dt': 'Sales Order',
				'source_field': '-1 * qty',
				'second_source_dt': 'Sales Invoice Item',
				'second_source_field': '-1 * qty',
				'second_join_field': 'so_detail',
				'extra_cond': """ and exists (select name from `tabDelivery Note`
					where name=`tabDelivery Note Item`.parent and is_return=1)""",
				'second_source_extra_cond': """ and exists (select name from `tabSales Invoice`
					where name=`tabSales Invoice Item`.parent and is_return=1 and update_stock=1)"""
			})

def validate_customer_batch(self):
	for row in self.items:
		if row.batch_no:
			batch_customer = frappe.db.get_value("Batch",row.batch_no,"customer")
			if batch_customer:
				if batch_customer != self.customer:
					frappe.msgprint(_("The batch selected doesn't have <strong>{}</strong> in row {}".format(self.customer,row.idx)))


def cal_qty(self,method):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		total_qty = 0.0
		total_quantity = 0.0
		
		for row in self.items:
			total_qty += row.qty
			total_quantity += row.quantity
		try:
			self.total_qty = total_qty
			self.total_quantity = total_quantity
		except:
			pass
	else:
		total_qty = 0.0
		for row in self.items:
			total_qty += row.qty
		try:
			self.total_qty = total_qty
		except:
			pass
