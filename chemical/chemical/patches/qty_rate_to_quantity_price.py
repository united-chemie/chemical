from __future__ import unicode_literals
import frappe

def execute():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""")
    frappe.db.sql("""update `tabPurchase Order Item` set `quantity` = `qty`""")
    frappe.db.sql("""update `tabPurchase Receipt Item` set `quantity` = `qty`""")
    frappe.db.sql("""update `tabPurchase Invoice Item` set `quantity` = `qty`""")
    frappe.db.sql("""update `tabSales Order Item` set `quantity` = `qty`""")
    frappe.db.sql("""update `tabSales Invoice Item` set `quantity` = `qty`""")
    frappe.db.sql("""update `tabDelivery Note Item` set `quantity` = `qty`""")
    frappe.db.sql("""update `tabStock Entry Detail` set `quantity` = `qty`""")


    frappe.db.sql("""update `tabPurchase Order Item` set `price` = `rate`""")
    frappe.db.sql("""update `tabPurchase Receipt Item` set `price` = `rate`""")
    frappe.db.sql("""update `tabPurchase Invoice Item` set `price` = `rate`""")
    frappe.db.sql("""update `tabSales Order Item` set `price` = `rate`""")
    frappe.db.sql("""update `tabSales Invoice Item` set `price` = `rate`""")
    frappe.db.sql("""update `tabDelivery Note Item` set `price` = `rate`""")
    frappe.db.sql("""update `tabStock Entry Detail` set `price` = `basic_rate`""")
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 1""")