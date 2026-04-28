from __future__ import unicode_literals
import frappe
from frappe.utils import get_url_to_form,get_fullname

def creation_comment(self):
    if self.doctype in ["Outward Sample","Outward Tracking"]:
        reference_doctype = self.link_to
        reference_name = self.party

    else:
        reference_doctype = "Customer"
        reference_name = self.customer_name if self.doctype == "Ball Mill Data Sheet" else self.customer

    comment_doc = frappe.new_doc("Comment")
    comment_doc.comment_type = "Info"
    comment_doc.comment_email = frappe.session.user
    comment_doc.reference_doctype = reference_doctype
    comment_doc.reference_name = reference_name
    comment_doc.link_doctype = self.doctype
    comment_doc.link_name = self.name
    comment_doc.comment_by = get_fullname(frappe.session.user)
    url = get_url_to_form(self.doctype, self.name)
    comment_doc.content = "Created {} <b><a href='{}'>{}</a></b>".format(self.doctype,url,self.name)

    comment_doc.save(ignore_permissions=True)

def status_change_comment(self):
    docstatus = "Submitted" if self.docstatus == 1 else "Cancelled"
    
    if self.doctype in ["Outward Tracking","Outward Sample"]:
        if self.doctype == "Outward Sample":
            status = self.status
        else:
            status = self.tracking_status
        reference_doctype = self.link_to
        reference_name = self.party

    # elif self.doctype == "Outward Sample":
    #     status = self.status
    #     reference_doctype = self.link_to
    #     reference_name = self.party   

    else:
        status = docstatus
        reference_doctype = "Customer"
        reference_name = self.customer_name if self.doctype == "Ball Mill Data Sheet" else self.customer
    
    getdoc = frappe.get_doc(self.doctype, self.name)
    if self.doctype == "Outward Sample":
        before_status_value = getdoc.status if getdoc.docstatus == 1 else "Cancelled"
    else:
        before_status_value = "Submitted" if getdoc.docstatus == 1 else "Cancelled"

    if status != before_status_value:
        comment_doc = frappe.new_doc("Comment")
        comment_doc.comment_type = "Info"
        comment_doc.comment_email = frappe.session.user
        comment_doc.reference_doctype = reference_doctype
        comment_doc.reference_name = reference_name
        comment_doc.link_doctype = self.doctype
        comment_doc.link_name = self.name
        comment_doc.comment_by = get_fullname(frappe.session.user)
        url = get_url_to_form(self.doctype, self.name)
        comment_doc.content = "Changed value of Status from <b>{}</b> to <b>{}</b> in {} <b><a href='{}'>{}</a></b> ".format(before_status_value,status, self.doctype,url,self.name)    

        comment_doc.save(ignore_permissions=True)

def cancellation_comment(self):
    if self.doctype in ["Outward Tracking", "Ball Mill Data Sheet"]:
        self.tracking_status = "Cancelled"
    elif self.doctype == "Outward Sample":
        self.status = "Rejected"

    status_change_comment(self)

def delete_comment(self,delete_pre_ref=None):
    if self.doctype in ["Outward Sample","Outward Tracking"]:
        reference_doctype = self.link_to
        reference_name = self.party

    elif self.doctype == "Ball Mill Data Sheet":
        reference_doctype = "Customer"
        reference_name = self.customer_name
    else:
        reference_doctype = "Customer"
        reference_name = self.customer
        reference_name = self.customer_name if self.doctype == "Ball Mill Data Sheet" else self.customer
    comment_doc = frappe.new_doc("Comment")
    comment_doc.comment_type = "Info"
    comment_doc.comment_email = frappe.session.user
    comment_doc.reference_doctype = reference_doctype
    comment_doc.reference_name = reference_name
    comment_doc.link_doctype = self.doctype
    comment_doc.link_name = self.name
    comment_doc.comment_by = get_fullname(frappe.session.user)
    url = get_url_to_form(self.doctype, self.name)
    comment_doc.content = "Deleted {} <b><a href='{}'>{}</a></b>".format(self.doctype,url,self.name)
    comment_doc.save(ignore_permissions=True)
    if delete_pre_ref:
        comment_list = frappe.db.get_all("Comment",{"comment_type":"Info","reference_doctype":reference_doctype,
                    "reference_name":reference_name,"link_doctype":self.doctype,"link_name":self.name})
        for comment in comment_list:
            frappe.delete_doc("Comment",comment.name)