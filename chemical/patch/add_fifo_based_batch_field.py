import frappe

def execute():
    if not check_get_batches_based_on_fifo_exists():
        add_get_batches_based_on_fifo()


def add_get_batches_based_on_fifo():
    doc=frappe.new_doc("Custom Field")
    doc.update({"dt":"Stock Entry","label":"Get Batches Based On Fifo","fieldname":"get_batches_based_on_fifo","insert_after":"get_raw_materials","fieldtype":"Check","hidden":1})
    doc.flags.ignore_permission=1
    doc.save()

def check_get_batches_based_on_fifo_exists():
    meta=frappe.get_meta('Stock Entry')
    if "get_batches_based_on_fifo" in meta._valid_columns:
        return True
    return False