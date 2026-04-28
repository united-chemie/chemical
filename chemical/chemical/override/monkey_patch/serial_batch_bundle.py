import frappe


def create_batch(self):
	from erpnext.stock.doctype.batch.batch import make_batch

	dct = {}

	if hasattr(self, 'voucher_detail_no'):
		if self.voucher_type == "Stock Entry":
			data = frappe.get_doc("Stock Entry Detail", self.voucher_detail_no)
		else:
			data = frappe.get_doc(f"{self.voucher_type} Item", self.voucher_detail_no)
				
		dct.update({
			"lot_no": data.get("lot_no"),
			"packaging_material": data.get("packaging_material"),
			"packing_size": data.get("packing_size"),
			"no_of_packages": data.get("no_of_packages"),
			"batch_yield": data.get("batch_yield"),
			"concentration": data.get("concentration")
		})
	
	dct.update({
		"item": self.get("item_code"),
		"reference_doctype": self.get("voucher_type"),
		"reference_name": self.get("voucher_no"),
	})
	

	return make_batch(frappe._dict(dct))