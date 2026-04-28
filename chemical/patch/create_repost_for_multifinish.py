import frappe
import datetime as dt

def execute():
    create_repost_entries()

def create_repost_entries():
    acc_forzen_date = frappe.db.get_single_value("Accounts Settings", "acc_frozen_upto")
    period_closing_date = frappe.db.get_value("Period Closing Voucher", {'docstatus': 1}, 'posting_date', order_by = 'creation')
    posting_date = max(acc_forzen_date, period_closing_date)

    stock_entry_data = frappe.db.sql(f"""
        SELECT 
            sle.name, se.name as stock_entry, se.company
        FROM `tabStock Entry` as se 
        JOIN `tabStock Entry Detail` as sei on se.name = sei.parent
        JOIN `tabStock Ledger Entry` as sle on sle.voucher_detail_no = sei.name and sle.voucher_no = se.name 
        WHERE se.posting_date > '{posting_date}' and sei.is_finished_item = 1 and se.stock_entry_type in ('Manufacture', 'Repack') and sei.docstatus = 1 and sle.is_cancelled = 0 and recalculate_rate = 0 and sei.batch_no is NOT NULL
    """, as_dict = 1)

    for row in stock_entry_data:
        frappe.db.set_value("Stock Ledger Entry", row.name, "recalculate_rate", 1)
        print(row.stock_entry)
        doc = frappe.new_doc("Repost Item Valuation")
        doc.based_on = "Transaction"
        doc.voucher_type = "Stock Entry"
        doc.voucher_no = row.stock_entry
        doc.company = row.company
        doc.save()
        doc.submit()