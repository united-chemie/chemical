import frappe

def execute():
    set_valuation_method()
    set_create_new_batch()

def set_valuation_method():
    print("set valuation")
    frappe.db.sql(""" Update `tabItem` SET valuation_method = null """)
    frappe.db.sql(""" Update `tabItem` Set valuation_method = "FIFO" where has_batch_no = 1 """)

def set_create_new_batch():
    print("set valuation")
    frappe.db.sql(""" Update `tabItem` Set create_new_batch = 1 Where has_batch_no = 1 """)
    frappe.db.sql("""
        UPDATE `tabBatch` 
        SET use_batchwise_valuation = 1
        WHERE use_batchwise_valuation = 0
    """)

    frappe.db.set_single_value("Stock Settings", "use_naming_series", 1)
    frappe.db.set_single_value("Stock Settings", "naming_series_prefix", "BTH-{{ posting_date }}-.###")
    frappe.db.set_single_value("Stock Settings", "exact_cost_valuation_for_batch_wise_items", 0)

def create_property_setter():
    if not frappe.db.exists("Property Setter", "Item-valuation_method-default"):
        doc = frappe.new_doc("Property Setter")
        doc.doctype_or_field = "DocField"
        doc.doc_type = "Item"
        doc.field_name = "valuation_method"
        doc.property = "default"
        doc.property_type = "Text"
        doc.value = "FIFO"
        doc.save()

    if not frappe.db.exists("Property Setter", "Item-valuation_method-options"):
        doc = frappe.new_doc("Property Setter")
        doc.doctype_or_field = "DocField"
        doc.doc_type = "Item"
        doc.field_name = "valuation_method"
        doc.property = "default"
        doc.property_type = "Text"
        doc.value = "FIFO\nMoving Average\nLIFO"
        doc.default_value = "FIFO"
        doc.save()
    