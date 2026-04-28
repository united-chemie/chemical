import frappe
from frappe.utils import flt, cint
from chemical.api import purchase_cal_rate_qty, quantity_price_to_qty_rate
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt
import re


def before_validate(self,method):
	quantity_price_to_qty_rate(self)
	
def before_submit(self, method):
	pr_update_status_updater_args(self)

def before_cancel(self, method):
	pr_update_status_updater_args(self)
	PurchaseReceipt.delete_auto_created_batches = delete_auto_created_batches

def t_validate(self,method):
	cal_total(self)

def pr_update_status_updater_args(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		self.status_updater = [{
			'source_dt': 'Purchase Receipt Item',
			'target_dt': 'Purchase Order Item',
			'join_field': 'purchase_order_item',
			'target_field': 'received_qty', # In Purchase Order Item
			'target_parent_dt': 'Purchase Order',
			'target_parent_field': 'per_received',
			'target_ref_field': 'quantity', # In Purchase Order Item
			'source_field': 'quantity', #In Purchase Receipt Item
			'percent_join_field': 'purchase_order',
			'second_source_dt': 'Purchase Invoice Item',
			'second_source_field': 'quantity',  # In Purchase Invoice Item
			'second_join_field': 'po_detail',
			'overflow_type': 'receipt',
			'second_source_extra_cond': """ and exists(select name from `tabPurchase Invoice`
				where name=`tabPurchase Invoice Item`.parent and update_stock = 1)"""
		},
		{
			'source_dt': 'Purchase Receipt Item',
			'target_dt': 'Material Request Item',
			'join_field': 'material_request_item',
			'target_field': 'received_qty',
			'target_parent_dt': 'Material Request',
			'target_parent_field': 'per_received',
			'target_ref_field': 'quantity',
			'source_field': 'quantity',
			'percent_join_field': 'material_request'
		}]

		if cint(self.is_return):
			self.status_updater.append({
				'source_dt': 'Purchase Receipt Item',
				'target_dt': 'Purchase Order Item',
				'join_field': 'purchase_order_item',
				'target_field': 'returned_qty',
				'source_field': '-1 * quantity',
				'second_source_dt': 'Purchase Invoice Item',
				'second_source_field': '-1 * quantity',
				'second_join_field': 'po_detail',
				'extra_cond': """ and exists (select name from `tabPurchase Receipt`
					where name=`tabPurchase Receipt Item`.parent and is_return=1)""",
				'second_source_extra_cond': """ and exists (select name from `tabPurchase Invoice`
					where name=`tabPurchase Invoice Item`.parent and is_return=1 and update_stock=1)"""
			})
	else: 
		self.status_updater = [{
			'source_dt': 'Purchase Receipt Item',
			'target_dt': 'Purchase Order Item',
			'join_field': 'purchase_order_item',
			'target_field': 'received_qty', # In Purchase Order Item
			'target_parent_dt': 'Purchase Order',
			'target_parent_field': 'per_received',
			'target_ref_field': 'qty', # In Purchase Order Item
			'source_field': 'qty', #In Purchase Receipt Item
			'percent_join_field': 'purchase_order',
			'second_source_dt': 'Purchase Invoice Item',
			'second_source_field': 'qty',  # In Purchase Invoice Item
			'second_join_field': 'po_detail',
			'overflow_type': 'receipt',
			'second_source_extra_cond': """ and exists(select name from `tabPurchase Invoice`
				where name=`tabPurchase Invoice Item`.parent and update_stock = 1)"""
		},
		{
			'source_dt': 'Purchase Receipt Item',
			'target_dt': 'Material Request Item',
			'join_field': 'material_request_item',
			'target_field': 'received_qty',
			'target_parent_dt': 'Material Request',
			'target_parent_field': 'per_received',
			'target_ref_field': 'qty',
			'source_field': 'qty',
			'percent_join_field': 'material_request'
		}]

		if cint(self.is_return):
			self.status_updater.append({
				'source_dt': 'Purchase Receipt Item',
				'target_dt': 'Purchase Order Item',
				'join_field': 'purchase_order_item',
				'target_field': 'returned_qty',
				'source_field': '-1 * qty',
				'second_source_dt': 'Purchase Invoice Item',
				'second_source_field': '-1 * qty',
				'second_join_field': 'po_detail',
				'extra_cond': """ and exists (select name from `tabPurchase Receipt`
					where name=`tabPurchase Receipt Item`.parent and is_return=1)""",
				'second_source_extra_cond': """ and exists (select name from `tabPurchase Invoice`
					where name=`tabPurchase Invoice Item`.parent and is_return=1 and update_stock=1)"""
			})
	# self.update_qty()
def cal_total(self):
	if not frappe.db.get_value("Company", self.company, "maintain_as_is_new"):
		doc_items = frappe.get_doc({"doctype":"Purchase Receipt Item"}) 
		total_quantity = 0
		total_supplier_qty=0
		total_supplier_quantity = 0
		total_packages = 0
		for d in self.items:
			total_quantity = total_quantity + flt(d.quantity)
			if hasattr(doc_items, "supplier_qty"):
				total_supplier_qty = total_supplier_qty + flt(d.supplier_qty)
				total_supplier_quantity = total_supplier_quantity + flt(d.supplier_quantity)
				total_packages = total_packages + (d.no_of_packages)
		
		self.total_quantity = total_quantity
		if hasattr(self, "total_supplier_qty"):
			self.total_supplier_qty = total_supplier_qty
			self.total_supplier_quantity = total_supplier_quantity
			self.total_packages = total_packages
	else:
		pass

def delete_auto_created_batches(self):
	pass


