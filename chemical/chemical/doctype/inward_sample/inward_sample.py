# -*- coding: utf-8 -*-
# Copyright (c) 2018, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import db,_
from frappe.model.document import Document
# from finbyzerp.finbyzerp.doc_events.naming_series import before_naming as naming_series 
from frappe.model.mapper import get_mapped_doc

class InwardSample(Document):
    @frappe.whitelist()
    def onclick_update_price(self):
        if self.item_price:
            if db.exists("Item Price" ,{ "item_code":self.item_code ,"price_list":self.price_list}):
                item_price = frappe.get_doc("Item Price",{"item_code":self.item_code, "price_list":self.price_list})
                item_price.price_list_rate = self.item_price
                if self.link_to == "Supplier" and self.price_list == "Standard Buying":
                    item_price.supplier = self.party
                elif self.link_to == "Customer" and self.price_list == "Standard Selling":
                    item_price.customer = self.party
                item_price.save()
            else:
                item_price = frappe.new_doc("Item Price")
                item_price.price_list = self.price_list
                item_price.item_code = self.item_code
                item_price.price_list_rate = self.item_price
                if self.link_to == "Supplier" and self.price_list == "Standard Buying":
                    item_price.supplier = self.party
                elif self.link_to == "Customer" and self.price_list == "Standard Selling":
                    item_price.customer = self.party
                item_price.save()
            frappe.msgprint("Item Price Updated")
        # if self.link_to == "Supplier":
        # if frappe.db.exists("Purchase Price" ,{ "product_name":self.item_code , "price_list":self.price_list}):
            # purchase_price = frappe.get_doc("Purchase Price",{"product_name":self.item_code,"price_list":self.price_list})
            # purchase_price.price = self.item_price
            # purchase_price.price_list = self.price_list
            # purchase_price.supplier = self.party
            # purchase_price.save()
            #purchase_price.run_method('on_update_after_submit')

        # else:
        # if self.item_price != 0.00:
        # 	purchase_price = frappe.new_doc("Purchase Price")
        # 	purchase_price.ref_no = self.outward_reference
        # 	purchase_price.product_name = self.item_code
        # 	purchase_price.supplier_ref_no = self.ref_no
        # 	purchase_price.supplier_product_name = self.item_code
        # 	purchase_price.date = self.price_date or self.date
        # 	purchase_price.price = self.item_price
        # 	purchase_price.price_list = self.price_list
        # 	purchase_price.link_to = self.link_to
        # 	purchase_price.party = self.party
        # 	purchase_price.party_name = self.party_name

        # 	purchase_price.save()
        # 	# self.db_set('purchase_price', purchase_price.name)
        # 	purchase_price.submit()
        # #frappe.db.commit()
        # frappe.msgprint(_("Purchase Price Updated"))

    def before_save(self):
        if self.link_to == "Customer" and self.party and self.item_code:
            ref_code = frappe.db.get_value("Item Customer Detail", {'parent': self.item_code, 'customer_name': self.party}, 'ref_code')
            self.customer_item_name = ref_code

        
    # def before_naming(self):
    # 	naming_series(self, 'save')

@frappe.whitelist()
def make_quality_inspection(source_name, target_doc=None):
    doclist = get_mapped_doc("Inward Sample", source_name, {
        "Inward Sample": {
            "doctype": "Quality Inspection",
            "field_map": {
                "product_name": "item_code",
                "doctype": "reference_type",
                "name": "reference_name",
            },
        }
    }, target_doc)
    
    doclist.inspection_type = "Incoming"  # Example: Set inspection type
    item_doc = frappe.db.get_value("Item", doclist.item_code, "quality_inspection_template", as_dict=1)
    doclist.quality_inspection_template = item_doc.quality_inspection_template if item_doc else None
    doclist.set("inspected_by", frappe.session.user)

    return doclist

