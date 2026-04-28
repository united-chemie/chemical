from __future__ import unicode_literals
import frappe

def execute():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""")
    frappe.db.sql("""update `tabStock Entry` set `fg_completed_quantity`= `fg_completed_qty` where `docstatus` = 1""")
