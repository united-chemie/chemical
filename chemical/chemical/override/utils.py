import frappe
from frappe.utils import flt, cint
import datetime


def se_cal_rate_qty(self):
	for d in self.items:
		if not d.get("ignore_calculation"):
			maintain_as_is_stock = frappe.db.get_value(
				"Item", d.item_code, "maintain_as_is_stock"
			)
			if maintain_as_is_stock:
				if d.get('packing_size') and d.get("no_of_packages") and d.get("concentration"):
					if self.get("is_return"):
						d.no_of_packages = -abs(d.no_of_packages)
					d.qty = (flt(d.packing_size) * flt(d.no_of_packages) * flt(d.concentration)) / 100.0
			else:
				if d.get("packing_size") and d.get("no_of_packages"):
					d.qty = cint(d.packing_size) * cint(d.no_of_packages)
					d.receive_qty = d.packing_size * d.no_of_packages
		else:
			if d.get("packing_size") and d.get("no_of_packages"):
				d.qty = cint(d.packing_size) * cint(d.no_of_packages)

def se_repack_cal_rate_qty(self):
	for d in self.items:
		if not d.get("ignore_calculation"):
			maintain_as_is_stock = frappe.db.get_value(
				"Item", d.item_code, "maintain_as_is_stock"
			)
			if maintain_as_is_stock:
				if d.get('packing_size') and d.get("no_of_packages") and d.get("concentration"):
					if self.get("is_return"):
						d.no_of_packages = -abs(d.no_of_packages)
					d.qty = (flt(d.packing_size) * flt(d.no_of_packages) * flt(d.concentration)) / 100.0
			else:
				if d.get("packing_size") and d.get("no_of_packages"):
					d.qty = d.packing_size * d.no_of_packages
					d.receive_qty = d.packing_size * d.no_of_packages
		else:
			if d.get("packing_size") and d.get("no_of_packages"):
					d.qty = d.packing_size * d.no_of_packages

def cal_actual_valuations(self):
	for row in self.items:
		maintain_as_is_stock = frappe.db.get_value(
			"Item", row.item_code, "maintain_as_is_stock"
		)
		if maintain_as_is_stock:
			concentration = flt(row.concentration) or 100
			row.actual_valuation_rate = flt(
				(flt(row.valuation_rate) * 100) / concentration
			)
		else:
			concentration = flt(row.concentration) or 100
			row.actual_valuation_rate = flt(row.valuation_rate)
