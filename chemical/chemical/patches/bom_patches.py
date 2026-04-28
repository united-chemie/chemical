from __future__ import unicode_literals
import frappe

def execute():
    frappe.db.sql("""SET SQL_SAFE_UPDATES = 0""")
    bom_name = frappe.db.sql("select `name` from `tabBOM` where `docstatus` <> 2")
    if bom_name:
        for bom in bom_name:
            bom_doc = frappe.get_doc("BOM",bom[0])
            if bom_doc.additional_cost:
                for additional_cost in bom_doc.additional_cost:
                    if not additional_cost.qty:
                        additional_cost.db_set("qty",bom_doc.quantity)
                        additional_cost.db_set("amount",bom_doc.quantity * additional_cost.rate)
                    if not additional_cost.uom:
                        additional_cost.db_set("uom","FG QTY")
                for child in bom_doc.additional_cost:
                    child.db_update()
                frappe.db.commit()

            volume_quantity = frappe.db.get_value("BOM",bom[0],'volume_quantity')
            volume_rate = frappe.db.get_value("BOM",bom[0],'volume_rate')
            volume_amount = frappe.db.get_value("BOM",bom[0],'volume_amount')

            etp_qty = frappe.db.get_value("BOM",bom[0],'etp_qty')
            etp_rate = frappe.db.get_value("BOM",bom[0],'etp_rate')
            etp_amount = frappe.db.get_value("BOM",bom[0],'etp_amount')
            # uom_doc = frappe.new_doc("UOM")
            # uom_doc.uom_name = 'FG QTY'
            # uom_doc.save()
            if etp_qty:
                doc = frappe.get_doc("BOM",bom[0])
                doc.append("additional_cost",{
                    "description" : "Volume",
                    "qty" : etp_qty,
                    "rate" : etp_rate,
                    "amount" : etp_amount,
                    "uom" : "FG QTY"
                }) 
                doc.flags.ignore_validate_update_after_submit = True
                doc.save()
                frappe.db.commit()

            if volume_quantity:
                doc = frappe.get_doc("BOM",bom[0])
                doc.append("additional_cost",{
                    "description" : "Volume",
                    "qty" : volume_quantity,
                    "rate" : volume_rate,
                    "amount" : volume_amount,
                    "uom" : "Volume"
                }) 
                doc.flags.ignore_validate_update_after_submit = True
                doc.save()
                frappe.db.commit()
                #frappe.db.sql("""insert into `tabBOM Additional Cost` (`qty`,`rate`,`amount`) select `volume_quantity`,`volume_rate`,`volume_amount` from `tabBOM` where `parent`= %s """,d[0])

        from datetime import datetime, timedelta
        d = datetime.today() + timedelta(hours=5, minutes=0)
        d.strftime('%Y-%m-%d %H:00:00')
        frappe.db.sql("DELETE FROM `tabVersion` WHERE owner='Administrator' and modified > %s",d)
        frappe.db.commit()