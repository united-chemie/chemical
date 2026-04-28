from __future__ import unicode_literals
import frappe
from erpnext.stock.get_item_details import get_basic_details

@frappe.whitelist()
def get_approved_outward_sample_list(party):
    return frappe.get_list("Outward Sample",filters={"link_to":"Customer","party":party,"status":"Approved","docstatus":1},fields=["product_name","name","per_unit_price","ref_no","per_unit_price"],ignore_permissions=True)


@frappe.whitelist()
def get_outward_sample_list(party):
    return frappe.get_list("Outward Sample",filters={"link_to":"Customer","party":party,"docstatus":1},fields=["product_name","name","per_unit_price","ref_no","per_unit_price"],ignore_permissions=True)