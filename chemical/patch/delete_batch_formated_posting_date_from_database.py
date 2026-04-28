import frappe


def execute():    
    if frappe.db.sql("SHOW COLUMNS FROM `tabBatch` LIKE 'formatted_posting_date'"):
        frappe.db.sql("ALTER TABLE `tabBatch` DROP COLUMN `formatted_posting_date`")