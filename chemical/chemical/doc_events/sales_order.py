import frappe
from frappe.utils import flt
from chemical.api import cal_rate_qty, quantity_price_to_qty_rate

def onload(self,method):
    quantity_price_to_qty_rate(self)

def validate(self,method):
    cal_rate_qty(self)
