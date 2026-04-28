import frappe
from frappe import _


def validate(self, method):
    set_batch_serial_check_box(self)


def before_submit(self, method):
    validate_multiple_item_bom(self)


# TODO: Check if needed
def set_batch_serial_check_box(self):
    if self.get("has_batch_no"):
        self.has_batch_no = 0
        self.has_serial_no = 0


# TODO: Check if needed
def validate_multiple_item_bom(self):
    for item in self.finish_item:
        bom = frappe.db.sql(
            """select name from `tabBOM` where item = %s and is_default = 1""",
            item.item_code,
        )
        if not bom:
            frappe.throw(_("Create BOM for Finish Item {}".format(item.item_code)))
