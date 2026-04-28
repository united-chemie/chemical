import frappe
from frappe import msgprint, _
from frappe.utils import flt,today


def before_save(self,method):
    update_item_price_history(self)

def update_item_price_history(self):
    doc = frappe.new_doc("Item Price History")
    doc.date = today()
    doc.item_code = self.item_code
    doc.price = self.price_list_rate
    if self.buying:
        doc.buying = 1
        doc.supplier = self.supplier
    elif self.selling:
        doc.selling = 1
        doc.customer = self.customer
    doc.update_from = self.doctype
    if frappe.db.exists("Item Price",self.name):
        doc.docname = self.name
    doc.save(ignore_permissions=True)