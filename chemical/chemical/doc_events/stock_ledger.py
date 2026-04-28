import frappe
from erpnext.stock.stock_ledger import update_entries_after

def build(self):
	from erpnext.controllers.stock_controller import future_sle_exists

	if self.args.get("sle_id"):
		update_entries_after.process_sle_against_current_timestamp(self)
		if not future_sle_exists(self.args):
			update_entries_after.update_bin(self)
	else:
		entries_to_fix = update_entries_after.get_future_entries_to_fix(self)

		i = 0
		try:
			while i < len(entries_to_fix):
				sle = entries_to_fix[i]
				i += 1

				self.process_sle(sle)

				if sle.dependant_sle_voucher_detail_no:
					entries_to_fix = update_entries_after.get_dependent_entries_to_fix(self,entries_to_fix, sle)

			self.update_bin()
		except:
			frappe.log_error(f"Did not found any entry for the {self.item_code}")

	if self.exceptions:
		self.raise_exceptions()
