import frappe
from erpnext.stock.doctype.batch.batch import Batch as _Batch ,batch_uses_naming_series,get_name_from_hash,_get_batch_prefix,_make_naming_series_key
from frappe.model.naming import make_autoname
from frappe.utils.jinja import render_template
from frappe import _




class Batch(_Batch):
	def autoname(self):
		"""Generate random ID for batch if not specified"""

		if self.batch_id:
			self.name = self.batch_id
			return

		create_new_batch, batch_number_series = frappe.db.get_value(
			"Item", self.item, ["create_new_batch", "batch_number_series"]
		)

		if not create_new_batch:
			frappe.throw(_("Batch ID is mandatory"), frappe.MandatoryError)

		while not self.batch_id:
			if batch_number_series:
				batch_number_series = batch_number_series.replace("posting_date", self.posting_date)
				self.batch_id = make_autoname(batch_number_series, doc=self)
			elif batch_uses_naming_series():
				self.batch_id = self.get_name_from_naming_series()
			else:
				self.batch_id = get_name_from_hash()

			# User might have manually created a batch with next number
			if frappe.db.exists("Batch", self.batch_id):
				self.batch_id = None

		self.name = self.batch_id

	def get_name_from_naming_series(self):
		"""
		Get a name generated for a Batch from the Batch's naming series.
		:return: The string that was generated.
		"""
		naming_series_prefix = _get_batch_prefix()
		# validate_template(naming_series_prefix)
		naming_series_prefix = render_template(str(naming_series_prefix), self.__dict__)
		naming_series_prefix = naming_series_prefix.replace("posting_date", self.posting_date)
		key = _make_naming_series_key(naming_series_prefix)
		name = make_autoname(key)

		return name
