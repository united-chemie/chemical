import frappe
from frappe import msgprint, _
from frappe.utils import flt, cint, nowdate, cstr, now_datetime
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from chemical.api import cal_rate_qty, quantity_price_to_qty_rate

def onload(self,method):
    quantity_price_to_qty_rate(self)

def si_before_submit(self,method):
	validate_customer_batch(self)

#added	
def before_submit(self, method):
	update_item_price_history(self)
	override_si_status_updater_args()

def before_cancel(self, method):
	delete_item_price_history(self)
	override_si_status_updater_args()

def on_trash(self, method):
	delete_item_price_history(self)

def override_si_status_updater_args():
	SalesInvoice.update_status_updater_args = si_update_status_updater_args

def validate_customer_batch(self):
	for row in self.items:
		if row.batch_no:
			batch_customer = frappe.db.get_value("Batch",row.batch_no,"customer")
			if batch_customer:
				if batch_customer != self.customer:
					frappe.msgprint(_("The batch selected doesn't have <strong>{}</strong> in row {}".format(self.customer,row.idx)))

def before_validate(self,method):
	# sales invoice return quantity not working on validate
	cal_rate_qty(self)

def validate(self,method):
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

def si_update_status_updater_args(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		if cint(self.update_stock):
			self.status_updater.append({
				'source_dt':'Sales Invoice Item',
				'target_dt':'Sales Order Item',
				'target_parent_dt':'Sales Order',
				'target_parent_field':'per_delivered',
				'target_field':'delivered_qty', # In Sales Order Item
				'target_ref_field':'quantity', # In Sales Order Item
				'source_field':'quantity', # In Sales Invoice Item
				'join_field':'so_detail',
				'percent_join_field':'sales_order',
				'status_field':'delivery_status',
				'keyword':'Delivered',
				'second_source_dt': 'Delivery Note Item',
				'second_source_field': 'quantity', # In Delivery Note Item
				'second_join_field': 'so_detail',
				'overflow_type': 'delivery',
				'extra_cond': """ and exists(select name from `tabSales Invoice`
					where name=`tabSales Invoice Item`.parent and update_stock = 1)"""
			})

			if cint(self.is_return):
				self.status_updater.append({
					'source_dt': 'Sales Invoice Item',
					'target_dt': 'Sales Order Item',
					'join_field': 'so_detail',
					'target_field': 'returned_qty',
					'target_parent_dt': 'Sales Order',
					'source_field': '-1 * quantity',
					'second_source_dt': 'Delivery Note Item',
					'second_source_field': '-1 * quantity',
					'second_join_field': 'so_detail',
					'extra_cond': """ and exists (select name from `tabSales Invoice` where name=`tabSales Invoice Item`.parent and update_stock=1 and is_return=1)"""
				})
	else:
		if cint(self.update_stock):
			self.status_updater.append({
				'source_dt':'Sales Invoice Item',
				'target_dt':'Sales Order Item',
				'target_parent_dt':'Sales Order',
				'target_parent_field':'per_delivered',
				'target_field':'delivered_qty', # In Sales Order Item
				'target_ref_field':'qty', # In Sales Order Item
				'source_field':'qty', # In Sales Invoice Item
				'join_field':'so_detail',
				'percent_join_field':'sales_order',
				'status_field':'delivery_status',
				'keyword':'Delivered',
				'second_source_dt': 'Delivery Note Item',
				'second_source_field': 'qty', # In Delivery Note Item
				'second_join_field': 'so_detail',
				'overflow_type': 'delivery',
				'extra_cond': """ and exists(select name from `tabSales Invoice`
					where name=`tabSales Invoice Item`.parent and update_stock = 1)"""
			})

			if cint(self.is_return):
				self.status_updater.append({
					'source_dt': 'Sales Invoice Item',
					'target_dt': 'Sales Order Item',
					'join_field': 'so_detail',
					'target_field': 'returned_qty',
					'target_parent_dt': 'Sales Order',
					'source_field': '-1 * qty',
					'second_source_dt': 'Delivery Note Item',
					'second_source_field': '-1 * qty',
					'second_join_field': 'so_detail',
					'extra_cond': """ and exists (select name from `tabSales Invoice` where name=`tabSales Invoice Item`.parent and update_stock=1 and is_return=1)"""
				})

def update_item_price_history(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		if self.items:
			for item in self.items:
				if item.item_code:
					doc = frappe.new_doc("Item Price History")
					doc.date = self.posting_date
					doc.item_code = item.item_code
					doc.price = item.price
					doc.customer = self.customer
					doc.selling = 1
					doc.update_from = self.doctype
					doc.docname = self.name
					doc.save(ignore_permissions=True)
	else:
		if self.items:
			for item in self.items:
				if item.item_code:
					doc = frappe.new_doc("Item Price History")
					doc.date = self.posting_date
					doc.item_code = item.item_code
					doc.price = item.rate
					doc.customer = self.customer
					doc.selling = 1
					doc.update_from = self.doctype
					doc.docname = self.name
					doc.save(ignore_permissions=True)

def delete_item_price_history(self):
	while frappe.db.exists("Item Price History",{"update_from":self.doctype,"docname":self.name}):
		doc = frappe.get_doc("Item Price History",{"update_from":self.doctype,"docname":self.name})
		doc.db_set('docname','')
		doc.delete()