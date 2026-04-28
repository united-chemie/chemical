# -*- coding: utf-8 -*-
# Copyright (c) 2018, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from chemical.comments_api import creation_comment,status_change_comment,cancellation_comment,delete_comment

class OutwardTracking(Document):
	def before_save(self):
		if self.link_to == "Customer" and self.party:
			for row in self.sample_items:
				if row.item:
					ref_code = frappe.db.get_value("Item Customer Detail", {'parent': row.item, 'customer_name': self.party}, 'ref_code')
					row.product_name = ref_code
	

	def on_submit(self):
		creation_comment(self)

	def before_update_after_submit(self):
		status_change_comment(self)

	def on_cancel(self):
		cancellation_comment(self)

	def on_trash(self):
		delete_comment(self)