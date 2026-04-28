from __future__ import unicode_literals
import frappe

def execute():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""")
    frappe.db.sql("""update `tabWork Order` set `produced_quantity`= `produced_qty` where `docstatus` = 1 and status = 'Completed'""")
    work_orders= frappe.db.sql("select `name` from `tabWork Order` where `docstatus` = 1 and status = 'Completed'")
    
    if work_orders:
        for work_order in work_orders:
            qty = frappe.db.get_value("Work Order",work_order[0],"qty")
            production_item = frappe.db.get_value("Work Order",work_order[0],"production_item")
            produced_qty = frappe.db.get_value("Work Order",work_order[0],"produced_qty")
            
            wo_doc = frappe.get_doc("Work Order",work_order[0])
            stock_entry = frappe.db.sql("""select name from `tabStock Entry` where `work_order` = %s and `stock_entry_type` = 'Manufacture'""",work_order[0])
            stock_entry_doc = frappe.get_doc("Stock Entry",stock_entry[0][0])
            lot_no = stock_entry_doc.items[-1].lot_no
            packing_size = stock_entry_doc.items[-1].packing_size
            no_of_packages = stock_entry_doc.items[-1].no_of_packages
            concentration = stock_entry_doc.items[-1].concentration
            batch_yield = stock_entry_doc.items[-1].batch_yield
            batch_no = stock_entry_doc.items[-1].batch_no
            valuation_rate = stock_entry_doc.items[-1].valuation_rate
            bom_yield = frappe.db.get_value("BOM",wo_doc.bom_no,"batch_yield")

            wo_doc.append("finish_item",{
                "item_code": production_item,
                "actual_qty":produced_qty,
                "actual_valuation":valuation_rate,
                "lot_no": lot_no,
                "packing_size": packing_size,
                "no_of_packages": no_of_packages,
                "purity": concentration,
                "batch_yield": batch_yield,
                "batch_no": batch_no,
                "bom_cost_ratio": 100,
                "bom_qty_ratio": 100,
                "bom_qty": qty,
                "bom_yield": bom_yield,
            })
            wo_doc.flags.ignore_validate_update_after_submit = True
            wo_doc.save()
            frappe.db.commit()
        from datetime import datetime, timedelta
        d = datetime.today() + timedelta(hours=5, minutes=0)
        d.strftime('%Y-%m-%d %H:00:00')
        frappe.db.sql("DELETE FROM `tabVersion` WHERE owner='Administrator' and modified > %s",d)
        frappe.db.commit()