import frappe
from frappe.utils import flt
from frappe import _
from pypika.terms import ExistsCriterion
from erpnext.manufacturing.doctype.production_plan.production_plan import (
    ProductionPlan as _ProductionPlan,
)
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
from frappe.utils import now_datetime


class ProductionPlan(_ProductionPlan):
    def get_production_items(self):
        item_dict = {}
        for d in self.po_items:
            item_details = {
                "production_item": d.item_code,
                "use_multi_level_bom": d.include_exploded_items,
                "sales_order": d.sales_order,
                "sales_order_item": d.sales_order_item,
                "material_request": d.material_request,
                "material_request_item": d.material_request_item,
                "bom_no": d.bom_no,
                "description": d.description,
                "stock_uom": d.stock_uom,
                "company": self.company,
                "fg_warehouse": d.warehouse,
                "production_plan": self.name,
                "production_plan_item": d.name,
                "product_bundle_item": d.product_bundle_item,
                "planned_start_date": d.planned_start_date,
                "project": self.project,
            }

            key = (d.item_code, d.sales_order, d.warehouse, d.name)
            if not d.sales_order:
                key = (d.name, d.item_code, d.warehouse, d.name)

            if not item_details["project"] and d.sales_order:
                item_details["project"] = frappe.get_cached_value(
                    "Sales Order", d.sales_order, "project"
                )

            if self.get_items_from == "Material Request":
                item_details.update({"qty": d.planned_qty})
                item_dict[(d.item_code, d.name, d.warehouse)] = item_details
            else:
                item_details.update(
                    {
                        "qty": flt(item_dict.get(key, {}).get("qty"))
                        + (flt(d.planned_qty) - flt(d.ordered_qty))
                    }
                )
                item_dict[key] = item_details

        return item_dict

    @frappe.whitelist()
    def get_open_sales_orders(self):
        """Pull sales orders  which are pending to deliver based on criteria selected"""
        open_so = get_sales_orders(self)
        if open_so:
            self.add_so_in_table(open_so)
        else:
            frappe.msgprint(_("Sales orders are not available for production"))

    @frappe.whitelist()
    def get_items(self):
        if self.get_items_from == "Sales Order":
            if self.based_on_sample == 1:
                get_so_items_for_sample(self)
            else:
                get_so_items(self)
        elif self.get_items_from == "Material Request":
            get_mr_items(self)


def get_so_items_for_sample(self):
    so_list = [d.sales_order for d in self.get("sales_orders", []) if d.sales_order]
    if not so_list:
        frappe.msgprint(_("Please enter Sales Orders in the above table"))
        return []
    item_condition = ""
    if self.item_code:
        item_condition = ' and so_item.item_code = "{0}"'.format(
            frappe.db.escape(self.item_code)
        )
    # -----------------------	custom added code  ------------#

    if self.as_per_projected_qty == 1:  # condition 1
        sample_list = [
            [d.outward_sample, d.quantity, d.projected_qty]
            for d in self.get("finish_items", [])
            if d.outward_sample
        ]
        if not sample_list:
            frappe.msgprint(_("Please Get Finished Items."))
            return []
        item_details = frappe._dict()

        for sample, quantity, projected_qty in sample_list:  # changes here
            if projected_qty < 0:
                sample_doc = frappe.get_doc("Outward Sample", sample)
                for row in sample_doc.details:
                    bom_no = frappe.db.exists(
                        "BOM",
                        {
                            "item": row.item_code,
                            "is_active": 1,
                            "is_default": 1,
                            "docstatus": 1,
                        },
                    )

                    if bom_no:
                        bom = frappe.get_doc(
                            "BOM",
                            {
                                "item": row.item_code,
                                "is_active": 1,
                                "is_default": 1,
                                "docstatus": 1,
                            },
                        )
                        item_details.setdefault(
                            row.item_code,
                            frappe._dict(
                                {
                                    "planned_qty": 0.0,
                                    "bom_no": bom.name,
                                    "item_code": row.item_code,
                                    "concentration": bom.concentration,
                                }
                            ),
                        )

                        item_details[row.item_code].planned_qty += (
                            flt(abs(projected_qty))
                            * flt(row.quantity)
                            * flt(row.concentration)
                        ) / (flt(sample_doc.total_qty) * flt(bom.concentration))

        items = [values for values in item_details.values()]

    elif self.as_per_actual_qty == 1:  # condition 2

        sample_list = [
            [d.outward_sample, d.quantity, d.actual_qty]
            for d in self.get("finish_items", [])
            if d.outward_sample
        ]
        if not sample_list:
            frappe.msgprint(_("Please Get Finished Items."))
            return []
        item_details = frappe._dict()
        for sample, quantity, actual_qty in sample_list:
            diff = actual_qty - quantity  # changes here
            if diff < 0:
                sample_doc = frappe.get_doc("Outward Sample", sample)

                for row in sample_doc.details:
                    bom_no = frappe.db.exists(
                        "BOM",
                        {
                            "item": row.item_code,
                            "is_active": 1,
                            "is_default": 1,
                            "docstatus": 1,
                        },
                    )
                    if bom_no:
                        bom = frappe.get_doc(
                            "BOM",
                            {
                                "item": row.item_code,
                                "is_active": 1,
                                "is_default": 1,
                                "docstatus": 1,
                            },
                        )
                        item_details.setdefault(
                            row.item_code,
                            frappe._dict(
                                {
                                    "planned_qty": 0.0,
                                    "bom_no": bom.name,
                                    "item_code": row.item_code,
                                    "concentration": bom.concentration,
                                }
                            ),
                        )

                        item_details[row.item_code].planned_qty += (
                            flt(abs(diff)) * flt(row.quantity) * (flt(row.concentration) or 100)
                        ) / (flt(sample_doc.total_qty) * (flt(bom.concentration) or 100))

        items = [values for values in item_details.values()]
        
    elif self.based_on_sample == 1:

        sample_list = [
            [d.outward_sample, d.quantity]
            for d in self.get("finish_items", [])
            if d.outward_sample
        ]
        if not sample_list:
            frappe.msgprint(_("Please Get Finished Items."))
            return []
        item_details = frappe._dict()
        for sample, quantity in sample_list:
            sample_doc = frappe.get_doc("Outward Sample", sample)

            for row in sample_doc.details:
                bom_no = frappe.db.exists(
                    "BOM",
                    {
                        "item": row.item_code,
                        "is_active": 1,
                        "is_default": 1,
                        "docstatus": 1,
                    },
                )
                if bom_no:
                    bom = frappe.get_doc(
                        "BOM",
                        {
                            "item": row.item_code,
                            "is_active": 1,
                            "is_default": 1,
                            "docstatus": 1,
                        },
                    )
                    # frappe.msgprint(str(bom.name))

                    item_details.setdefault(
                        row.item_code,
                        frappe._dict(
                            {
                                "planned_qty": 0.0,
                                "bom_no": bom.name,
                                "item_code": row.item_code,
                                "concentration": bom.concentration,
                            }
                        ),
                    )

                    item_details[row.item_code].planned_qty += (
                        flt(quantity) * flt(row.quantity) * ((row.concentration) or 100)
                    ) / (flt(sample_doc.total_qty) * ((bom.concentration)) or 100)

        items = [values for values in item_details.values()]
    else:
        return

    if self.item_code:
        item_condition = ' and so_item.item_code = "{0}"'.format(
            frappe.db.escape(self.item_code)
        )

    packed_items = frappe.db.sql(
        """select distinct pi.parent, pi.item_code, pi.warehouse as warehouse,
			(((so_item.qty - so_item.work_order_qty) * pi.qty) / so_item.qty)
				as pending_qty, pi.parent_item, so_item.name
			from `tabSales Order Item` so_item, `tabPacked Item` pi
			where so_item.parent = pi.parent and so_item.docstatus = 1
			and pi.parent_item = so_item.item_code
			and so_item.parent in (%s) and so_item.qty > so_item.work_order_qty
			and exists (select name from `tabBOM` bom where bom.item=pi.item_code
					and bom.is_active = 1) %s"""
        % (", ".join(["%s"] * len(so_list)), item_condition),
        tuple(so_list),
        as_dict=1,
    )

    add_items_for_sample(self, items + packed_items)
    calculate_total_planned_qty(self)


def get_so_items(self):
    # Check for empty table or empty rows
    if not self.get("sales_orders") or not self.get_so_mr_list(
        "sales_order", "sales_orders"
    ):
        frappe.throw(
            _("Please fill the Sales Orders table"), title=_("Sales Orders Required")
        )

    so_list = self.get_so_mr_list("sales_order", "sales_orders")

    bom = frappe.qb.DocType("BOM")
    so_item = frappe.qb.DocType("Sales Order Item")

    items_subquery = frappe.qb.from_(bom).select(bom.name).where(bom.is_active == 1)
    items_query = (
        frappe.qb.from_(so_item)
        .select(
            so_item.parent,
            so_item.item_code,
            so_item.warehouse,
            (
                (so_item.qty - so_item.work_order_qty - so_item.delivered_qty)
                * so_item.conversion_factor
            ).as_("pending_qty"),
            so_item.description,
            so_item.name,
            so_item.bom_no,
        )
        .distinct()
        .where(
            (so_item.parent.isin(so_list))
            & (so_item.docstatus == 1)
            & (so_item.qty > so_item.work_order_qty)
        )
    )
    if self.from_delivery_date and self.to_delivery_date:
        items_query = items_query.where(
            (so_item.delivery_date >= self.from_delivery_date)
            & (so_item.delivery_date <= self.to_delivery_date)
        )

    if self.item_code and frappe.db.exists("Item", self.item_code):
        items_query = items_query.where(so_item.item_code == self.item_code)
        items_subquery = items_subquery.where(
            self.get_bom_item_condition() or bom.item == so_item.item_code
        )

    items_query = items_query.where(ExistsCriterion(items_subquery))
    items = items_query.run(as_dict=True)

    pi = frappe.qb.DocType("Packed Item")

    packed_items_query = (
        frappe.qb.from_(so_item)
        .from_(pi)
        .select(
            pi.parent,
            pi.item_code,
            pi.warehouse.as_("warehouse"),
            (((so_item.qty - so_item.work_order_qty) * pi.qty) / so_item.qty).as_(
                "pending_qty"
            ),
            pi.parent_item,
            pi.description,
            so_item.name,
        )
        .distinct()
        .where(
            (so_item.parent == pi.parent)
            & (so_item.docstatus == 1)
            & (pi.parent_item == so_item.item_code)
            & (so_item.parent.isin(so_list))
            & (so_item.qty > so_item.work_order_qty)
            & (
                ExistsCriterion(
                    frappe.qb.from_(bom)
                    .select(bom.name)
                    .where((bom.item == pi.item_code) & (bom.is_active == 1))
                )
            )
        )
    )

    if self.item_code:
        packed_items_query = packed_items_query.where(
            so_item.item_code == self.item_code
        )

    packed_items = packed_items_query.run(as_dict=True)

    all_items = items + packed_items
    new_items = []

    for item in all_items:
        bom_quantity = frappe.get_value("BOM", item.get("bom_no"), "quantity")
        if bom_quantity:
            # Calculate the number of rows needed based on BOM quantity
            pending_qty = item.get("pending_qty")
            while pending_qty > 0:
                qty_to_add = min(pending_qty, bom_quantity)
                new_item = item.copy()
                new_item["pending_qty"] = qty_to_add
                new_items.append(new_item)
                pending_qty -= qty_to_add
        else:
            new_items.append(item)

    self.add_items(new_items)
    # self.add_items(items + packed_items)
    self.calculate_total_planned_qty()


def get_mr_items(self):
    # Check for empty table or empty rows
    if not self.get("material_requests") or not self.get_so_mr_list(
        "material_request", "material_requests"
    ):
        frappe.throw(
            _("Please fill the Material Requests table"),
            title=_("Material Requests Required"),
        )

    mr_list = self.get_so_mr_list("material_request", "material_requests")

    bom = frappe.qb.DocType("BOM")
    mr_item = frappe.qb.DocType("Material Request Item")

    items_query = (
        frappe.qb.from_(mr_item)
        .select(
            mr_item.parent,
            mr_item.name,
            mr_item.item_code,
            mr_item.warehouse,
            mr_item.description,
            mr_item.bom_no,
            ((mr_item.qty - mr_item.ordered_qty) * mr_item.conversion_factor).as_(
                "pending_qty"
            ),
        )
        .distinct()
        .where(
            (mr_item.parent.isin(mr_list))
            & (mr_item.docstatus == 1)
            & (mr_item.qty > mr_item.ordered_qty)
            & (
                ExistsCriterion(
                    frappe.qb.from_(bom)
                    .select(bom.name)
                    .where((bom.item == mr_item.item_code) & (bom.is_active == 1))
                )
            )
        )
    )

    if self.item_code:
        items_query = items_query.where(mr_item.item_code == self.item_code)

    items = items_query.run(as_dict=True)
    all_items = items
    new_items = []

    for item in all_items:
        bom_quantity = frappe.get_value("BOM", item.get("bom_no"), "quantity")
        if bom_quantity:
            # Calculate the number of rows needed based on BOM quantity
            pending_qty = item.get("pending_qty")
            while pending_qty > 0:
                qty_to_add = min(pending_qty, bom_quantity)
                new_item = item.copy()
                new_item["pending_qty"] = qty_to_add
                new_items.append(new_item)
                pending_qty -= qty_to_add
        else:
            new_items.append(item)

    self.add_items(new_items)

    self.calculate_total_planned_qty()


def get_sales_orders(self):
    so_filter = item_filter = ""
    if self.from_date:
        so_filter += " and so.transaction_date >= %(from_date)s"
    if self.to_date:
        so_filter += " and so.transaction_date <= %(to_date)s"
    if self.customer:
        so_filter += " and so.customer = %(customer)s"
    if self.project:
        so_filter += " and so.project = %(project)s"
    if self.from_delivery_date:
        item_filter += " and so_item.delivery_date >= %(from_delivery_date)s"
    if self.to_delivery_date:
        item_filter += " and so_item.delivery_date <= %(to_delivery_date)s"

    if self.item_code:
        item_filter += " and so_item.item_code = %(item)s"

    open_so = frappe.db.sql(
        """
		select distinct so.name, so.transaction_date, so.customer, so.base_grand_total
		from `tabSales Order` so, `tabSales Order Item` so_item
		where so_item.parent = so.name
			and so.docstatus = 1 and so.status not in ("Stopped", "Closed","Completed")
			and so.company = %(company)s
			and so_item.qty > so_item.work_order_qty {0} {1}

		""".format(
            so_filter, item_filter
        ),
        {
            "from_date": self.from_date,
            "to_date": self.to_date,
            "customer": self.customer,
            "project": self.project,
            "item": self.item_code,
            "company": self.company,
            "from_delivery_date": self.from_delivery_date,
            "to_delivery_date": self.to_delivery_date,
        },
        as_dict=1,
    )

    return open_so


def add_items_for_sample(self, items):
    # frappe.msgprint("call add")
    self.set("po_items", [])
    for data in items:
        item_details = get_item_details(data.item_code)
        pi = self.append(
            "po_items",
            {
                "include_exploded_items": 1,
                "warehouse": data.warehouse,
                "item_code": data.item_code,
                "description": item_details and item_details.description or "",
                "stock_uom": item_details and item_details.stock_uom or "",
                "bom_no": item_details and item_details.bom_no or "",
                # 'planned_qty': data.pending_qty,
                "concentration": data.concentration,
                "planned_qty": data.planned_qty,
                "pending_qty": data.pending_qty,
                "planned_start_date": now_datetime(),
                "product_bundle_item": data.parent_item,
            },
        )

        if self.get_items_from == "Sales Order":
            pi.sales_order = data.parent
            pi.sales_order_item = data.name

        elif self.get_items_from == "Material Request":
            pi.material_request = data.parent
            pi.material_request_item = data.name


def calculate_total_planned_qty(self):
    self.total_planned_qty = 0
    for d in self.po_items:
        self.total_planned_qty += flt(d.planned_qty)
