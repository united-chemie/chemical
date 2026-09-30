import frappe
from erpnext.stock.doctype.quality_inspection.quality_inspection import QualityInspection as _QualityInspection # type: ignore


def get_template_details(template):
	if not template:
		return []

	fields = [
		"specification",
		"value",
		"acceptance_formula",
		"numeric",
		"formula_based_criteria",
		"min_value",
		"max_value",
	]
	if frappe.get_meta("Item Quality Inspection Parameter").has_field("method"):
		fields.append("method")

	return frappe.get_all(
		"Item Quality Inspection Parameter",
		fields=fields,
		filters={"parenttype": "Quality Inspection Template", "parent": template},
		order_by="idx",
	)


class QualityInspection(_QualityInspection):
	def validate(self):
		super().validate()
		self.set_method_in_readings()

	def on_update(self):
		super().on_update()
		self.set_method_in_readings(update_db=True)

	@frappe.whitelist()
	def get_item_specification_details(self):
		if not self.quality_inspection_template:
			self.quality_inspection_template = frappe.db.get_value(
				"Item", self.item_code, "quality_inspection_template"
			)

		if not self.quality_inspection_template:
			return

		self.set("readings", [])
		parameters = get_template_details(self.quality_inspection_template)
		for d in parameters:
			child = self.append("readings", {})
			child.update(d)
			child.status = "Accepted"
			child.parameter_group = frappe.get_value(
				"Quality Inspection Parameter", d.specification, "parameter_group"
			)
			if d.get("method"):
				child.method = d.get("method")
			elif frappe.get_meta("Quality Inspection Parameter").has_field("method"):
				method_val = frappe.db.get_value(
					"Quality Inspection Parameter", d.specification, "method"
				)
				if method_val:
					child.method = method_val

	def set_method_in_readings(self, update_db=False):
		if not self.quality_inspection_template or not self.readings:
			return

		template_parameters = get_template_details(self.quality_inspection_template)
		if not template_parameters:
			return

		# If counts match by row index, map 1-to-1
		if len(template_parameters) == len(self.readings):
			for reading, param in zip(self.readings, template_parameters):
				method_val = param.get("method")
				if method_val:
					reading.method = method_val
					if update_db and getattr(reading, "name", None):
						frappe.db.set_value(
							"Quality Inspection Reading",
							reading.name,
							"method",
							method_val,
							update_modified=False,
						)
		else:
			# Fallback: match by specification
			param_map = {}
			for param in template_parameters:
				if param.get("method") and param.specification not in param_map:
					param_map[param.specification] = param.get("method")

			for reading in self.readings:
				method_val = param_map.get(reading.specification)
				if method_val:
					reading.method = method_val
					if update_db and getattr(reading, "name", None):
						frappe.db.set_value(
							"Quality Inspection Reading",
							reading.name,
							"method",
							method_val,
							update_modified=False,
						)

	def set_child_row_reference(self):
		if self.child_row_reference:
			return
		if self.reference_type == "Inward Sample":
			return
		if not (self.reference_type and self.reference_name):
			return

		doctype = self.reference_type + " Item"
		if self.reference_type == "Stock Entry":
			doctype = "Stock Entry Detail"
   
		if self.reference_type == "Outward Sample":
				doctype = 'Outward Sample Detail'
    
		child_doc = frappe.qb.DocType(doctype)
		qi_doc = frappe.qb.DocType("Quality Inspection")

		child_row_references = (
			frappe.qb.from_(child_doc)
			.left_join(qi_doc)
			.on(child_doc.name == qi_doc.child_row_reference)
			.select(child_doc.name)
			.where(
				(child_doc.item_code == self.item_code)
				& (child_doc.parent == self.reference_name)
				& (child_doc.docstatus < 2)
				& (qi_doc.name.isnull())
			)
			.orderby(child_doc.idx)
		).run(pluck=True)

		if len(child_row_references):
			self.child_row_reference = child_row_references[0]
	def update_qc_reference(self,remove_reference=False):
		quality_inspection = self.name if self.docstatus == 1 else ""

		if self.reference_type == "Job Card":
			if self.reference_name:
				frappe.db.sql(
					f"""
					UPDATE `tab{self.reference_type}`
					SET quality_inspection = %s, modified = %s
					WHERE name = %s and production_item = %s
				""",
					(quality_inspection, self.modified, self.reference_name, self.item_code),
				)
		elif self.reference_type == "Inward Sample":
			if self.reference_name:
				frappe.db.sql(
					f"""
					UPDATE `tab{self.reference_type}`
					SET quality_inspection = %s, modified = %s
					WHERE name = %s
				""",
					(quality_inspection, self.modified, self.reference_name),
				)

		else:
			args = [quality_inspection, self.modified, self.reference_name, self.item_code]
			doctype = self.reference_type + " Item"

			if self.reference_type == "Stock Entry":
				doctype = "Stock Entry Detail"

			if self.reference_type == "Outward Sample":
				doctype = 'Outward Sample Detail'

			if self.reference_type == "Inward Sample":
				doctype = 'Inward Sample'
				
			

			if self.reference_type and self.reference_name:
				conditions = ""
				if self.batch_no and self.docstatus == 1:
					conditions += " and t1.batch_no = %s"
					args.append(self.batch_no)

				if self.ref_item:
					conditions += " and t1.name = %s"
					args.append(self.ref_item)
				
				if self.docstatus == 2:  # if cancel, then remove qi link wherever same name
					conditions += " and t1.quality_inspection = %s"
					args.append(self.name)
				

				frappe.db.sql(
					f"""
					UPDATE
						`tab{doctype}` t1, `tab{self.reference_type}` t2
					SET
						t1.quality_inspection = %s, t2.modified = %s
					WHERE
						t1.parent = %s
						and t1.item_code = %s
						and t1.parent = t2.name
						{conditions}
				""",
					args,
				)

