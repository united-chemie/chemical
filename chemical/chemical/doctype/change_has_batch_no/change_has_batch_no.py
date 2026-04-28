# -*- coding: utf-8 -*-
# Copyright (c) 2021, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, cint, cstr
from frappe.model.document import Document
import datetime

class ChangeHasBatchNo(Document):
	def validate(self):
		sle_negative = frappe.get_list("Stock Ledger Entry",{'item_code':self.item_code,'actual_qty':('<',0)})
		if sle_negative:
			frappe.throw("Can not change has batch no for Item <b>{}</b>.".format(self.item_code))
		if not frappe.db.get_value("Item",self.item_code,'is_stock_item'):
			frappe.throw("Maintain Stock has to be 1 for item <b>{}</b>.".format(self.item_code))
			
		if self.has_batch_no:
			sle_list = frappe.get_list("Stock Ledger Entry",{'item_code':self.item_code})

			for row in sle_list:
				sle_doc = frappe.get_doc("Stock Ledger Entry",row['name'])
				if sle_doc.voucher_type == "Stock Entry":
					doc = frappe.get_doc(sle_doc.voucher_type + " Detail", sle_doc.voucher_detail_no)
				else:
					doc = frappe.get_doc(sle_doc.voucher_type + " Item", sle_doc.voucher_detail_no)

				batch = frappe.new_doc("Batch")
				batch.item = sle_doc.item_code
				batch.supplier = getattr(self, 'supplier', None)
				batch.lot_no = cstr(doc.lot_no)
				batch.packaging_material = cstr(doc.packaging_material)
				batch.packing_size = cstr(doc.packing_size)
				batch.batch_yield = flt(doc.batch_yield, 3)
				batch.concentration = flt(doc.concentration, 3)
				batch.valuation_rate = flt(sle_doc.incoming_rate)
				batch.price = flt(doc.price,2)
				batch.actual_quantity = flt(doc.qty * flt(doc.conversion_factor))
				batch.reference_doctype = sle_doc.voucher_type
				batch.reference_name = sle_doc.voucher_no
				
				try:
					batch.posting_date = datetime.datetime.strptime(sle_doc.posting_date, "%Y-%m-%d").strftime("%y%m%d")
				except:
					batch.posting_date = sle_doc.posting_date.strftime("%y%m%d")

				frappe.db.set_value("Item", sle_doc.item_code,'has_batch_no',self.has_batch_no)
				batch.insert()

				doc.db_set('batch_no',batch.name)
				sle_doc.db_set('batch_no',batch.name)

		
