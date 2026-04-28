import frappe

def on_submit(self, method):
	update_qc(self, method)

def validate(self, method):
	set_details_in_qc(self, method)

def on_cancel(self, method):
	update_qc(self, method)
	
			

def update_qc(self, method):
	if self.reference_type == "Stock Entry":
		if self._action == "submit":
			doc = frappe.get_doc(self.reference_type, self.reference_name)
			for row in doc.items:
				if row.item_code == self.item_code:
					row.db_set("concentration", self.concentration)
					# row.db_set("lot_no", self.lot_no)
					row.db_set("quality_inspection", self.name)
			doc.save()
			meta = frappe.get_meta(self.reference_type)
			if meta.has_field('quality_inspection'):
				doc.db_set("quality_inspection", self.name)

			if self.batch_no:
				meta_batch = frappe.get_meta("Batch")
				batch = frappe.get_doc("Batch", self.batch_no)
				if meta_batch.has_field('quality_inspection'):
					batch.db_set("quality_inspection", self.name)

		elif self._action == "cancel":
			doc = frappe.get_doc(self.reference_type, self.reference_name)
			meta = frappe.get_meta(self.reference_type)
			if meta.has_field('quality_inspection'):
				doc.db_set("quality_inspection", self.name)
			# doc.db_set("quality_inspection", "")
					
			if self.batch_no:
				meta_batch = frappe.get_meta("Batch")
				batch = frappe.get_doc("Batch", self.batch_no)
				if meta_batch.has_field('quality_inspection'):
					batch.db_set("quality_inspection", "")
	
def set_details_in_qc(self, method):
	pass
	# if self.reference_type == "Purchase Receipt":
	# 	row = frappe.get_doc("Purchase Receipt Item", {"name": self.ref_itm, "parent": self.reference_name})
	# 	self.packaging_material = row.packaging_material
	# 	self.concentration = row.concentration
	# 	self.packing_size = row.packing_size
	# 	self.no_of_packages = row.no_of_packages
	# 	self.qty = row.qty
	# 	self.lot_no = row.lot_no
	# 	self.supplier_name = frappe.db.get_value("Purchase Receipt", self.reference_name, "supplier")
			
	
	# if self.reference_type == "Delivery Note":
	# 	doc = frappe.get_doc("Delivery Note", self.reference_name)
	# 	for row in doc.items:
	# 		if row.item_code == self.item_code:
	# 			self.lot_no = row.lot_no
	# 			self.packaging_material = row.packaging_material
	# 			self.concentration = row.concentration
	# 			self.packing_size = row.packing_size
	# 			self.no_of_packages = row.no_of_packages
	# 			self.qty = row.qty
	
	# if self.reference_type == "Stock Entry":
	# 	doc = frappe.get_doc("Stock Entry", self.reference_name)
	# 	for row in doc.items:
	# 		if row.item_code == self.item_code:
	# 			self.lot_no = row.lot_no
	# 			self.packaging_material = row.packaging_material
	# 			# self.concentration = row.concentration
	# 			self.packing_size = row.packing_size
	# 			self.no_of_packages = row.no_of_packages
	# 			self.qty = row.qty
