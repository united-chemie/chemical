import frappe
from erpnext.stock.utils import get_stock_balance, get_incoming_rate
from erpnext.stock.doctype.batch.batch import get_batch_qty

def on_submit(self, method):
	update_valuation_rate_for_batch_no(self)

def on_cancel(self, method):
	update_valuation_rate_for_batch_no(self)

def update_valuation_rate_for_batch_no(self):
	for row in self.items:
		if not row.batch_no: continue

		valuation_rate = row.valuation_rate if self.docstatus == 1 else row.current_valuation_rate
		if valuation_rate is None:
			continue

		frappe.db.set_value("Batch", row.batch_no, 'valuation_rate', valuation_rate)