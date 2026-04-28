import frappe


def execute():
    if frappe.db.exists("Custom Field", {"dt": "Batch", "fieldname": "formatted_posting_date"}):
        custom_field_name = frappe.db.get_value("Custom Field", {"dt": "Batch", "fieldname": "formatted_posting_date"}, "name")
        frappe.delete_doc("Custom Field", custom_field_name)