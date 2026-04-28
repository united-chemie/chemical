# -*- coding: utf-8 -*-
# Copyright (c) 2021, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ManufacturingConsumption(Document):

	def on_submit(self):
		self.create_stock_entry()
	
	def on_cancel(self):
		self.cancel_stock_entry()

	def create_stock_entry(self):
		main_dict={}
		for row in self.manufacturing_consumption_details:
			if (row.work_order,row.work_order_qty) in main_dict.keys():
				main_dict[row.work_order,row.work_order_qty].append({'item_code':row.item_code,'batch_no':row.batch_no ,'quantity':row.quantity,'s_warehouse':row.s_warehouse})
			else:
				main_dict[row.work_order,row.work_order_qty]=[{'item_code':row.item_code,'batch_no':row.batch_no,'quantity':row.quantity,'s_warehouse':row.s_warehouse}]

		if main_dict:
			for work_order,value in main_dict.items():
				se_doc = frappe.new_doc("Stock Entry")
				se_doc.reference_doctype = self.doctype
				se_doc.reference_name =  self.name
				se_doc.company = self.company
				se_doc.posting_date = self.posting_date
				se_doc.posting_time =  self.posting_time
				se_doc.set_posting_time = 1
				se_doc.stock_entry_type = "Material Transfer for Manufacture"
				se_doc.bom_no = frappe.db.get_value("Work Order",work_order[0],'bom_no')
				se_doc.work_order = work_order[0]
				se_doc.from_warehouse = self.source_warehouse
				se_doc.from_bom = 1
				se_doc.fg_completed_qty = work_order[1]
				se_doc.fg_completed_quantity = work_order[1]
				for v in value:
					se_doc.append("items",{
						'item_code': v['item_code'],
						's_warehouse': v['s_warehouse'] or self.source_warehouse,
						't_warehouse': frappe.db.get_value("Work Order",work_order[0],'wip_warehouse'),
						'quantity': v['quantity'],
						'batch_no': v['batch_no']
					})
				se_doc.save(ignore_permissions=True)
				se_doc.submit()

	def cancel_stock_entry(self):
		se_list = frappe.get_list("Stock Entry",{'reference_doctype': self.doctype,'reference_name':self.name})
		for row in se_list:
			doc = frappe.get_doc("Stock Entry",row.name)
			doc.flags.ignore_permissions = True
			try:
				doc.cancel()
			except Exception as e:
				raise e
			doc.db_set('reference_doctype','')
			doc.db_set('reference_name','')


				

@frappe.whitelist()
def get_required_qty(work_order,item_code):
	if work_order and item_code:
		required_qty = frappe.db.get_value("Work Order Item",{'parent':work_order,'item_code':item_code},'required_qty')
		return required_qty

