import frappe
from datetime import datetime

def execute():
    meta = frappe.get_meta("Batch")
    if "formatted_posting_date" not in meta._valid_columns:
        create_duplicate_posting_date_field_for_batch()
    validate_posting_date_format()
    update_formatted_posting_date()

def create_duplicate_posting_date_field_for_batch():
    doc = frappe.new_doc("Custom Field")
    doc.dt = "Batch"
    doc.label = "Posting Date"
    doc.fieldname = "formatted_posting_date"
    doc.insert_after = "posting_date"
    doc.fieldtype = "Datetime"
    doc.read_only = 1
    doc.save(ignore_permissions=True)


def validate_posting_date_format():
    lst = frappe.db.sql("""select name,posting_date from `tabBatch` where posting_date IS NOT NULL and posting_date != '' """,as_dict=1)

    res = []
    for row in lst:
        try:
            po_date = datetime.strptime(row.posting_date, "%y%m%d")
        except:
            res += [print(row.name, "Date Format is not Matched")]

    if res:
        print(res)
        frappe.throw("All Date Formates are not same")

# def update_formatted_posting_date():
#     frappe.db.sql("""
#         Update `tabBatch`
#         set formatted_posting_date = CONVERT(STR_TO_DATE(posting_date,"%y%m%d"), DATETIME)
#         where posting_date IS NOT NULL and posting_date != ''
#     """)
    # frappe.throw("the remaining number of batches are {}".format(len(frappe.db.get_all("Batch",{'posting_date':['in',['',None]]}))))

