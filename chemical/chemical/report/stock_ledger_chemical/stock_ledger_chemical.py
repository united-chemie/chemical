# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils import cint, flt
from erpnext.stock.utils import update_included_uom_in_report, is_reposting_item_valuation_in_progress
from frappe import _
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

def execute(filters=None):
	is_reposting_item_valuation_in_progress()
	include_uom = filters.get("include_uom")
	columns = get_columns(filters)
	items = get_items(filters)
	sl_entries = get_stock_ledger_entries(filters, items)
	item_details = get_item_details(items, sl_entries, include_uom)
	opening_row = get_opening_balance(filters, columns)
	precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))

	data = []
	conversion_factors = []
	if opening_row:
		data.append(opening_row)

	actual_qty = stock_value = 0

	available_serial_nos = {}

	item_ware_house_in_qty = {}
	
	for sle in sl_entries:
		item_detail = item_details[sle.item_code]

		concentration = sle.concentration or 100
		
		if item_detail.maintain_as_is_stock:
			if not item_ware_house_in_qty.get(sle.item_code):
				item_ware_house_in_qty[sle.item_code] = {}
			
			if not item_ware_house_in_qty.get(sle.item_code, {}).get(sle.warehouse):
				item_ware_house_in_qty[sle.item_code][sle.warehouse] = 0
			
			item_ware_house_in_qty[sle.item_code][sle.warehouse] += (flt(sle.actual_qty) * flt(concentration))/100

			sle.update({
				'as_is_qty': flt(sle.actual_qty),
				'actual_qty': (flt(sle.actual_qty) * flt(concentration))/100,
				'incoming_rate': (flt(sle.incoming_rate) * 100)/flt(concentration),
				'valuation_rate': (flt(sle.valuation_rate) * 100)/flt(concentration),
				'as_is_balance_qty': flt(sle.qty_after_transaction),
				'qty_after_transaction': item_ware_house_in_qty[sle.item_code][sle.warehouse]
			})
		else:
			sle.update({
				'as_is_qty': flt(sle.actual_qty),
				'actual_qty': flt(sle.actual_qty),
				'incoming_rate': flt(sle.incoming_rate),
				'valuation_rate': flt(sle.valuation_rate),
				'as_is_balance_qty': flt(sle.qty_after_transaction)
			})

		if filters.get("batch_no") or (filters.get("item_code") and filters.get("warehouse")):
			actual_qty += sle.actual_qty
			stock_value += sle.stock_value_difference

			if sle.voucher_type == 'Stock Reconciliation' and not sle.actual_qty:
				actual_qty = sle.qty_after_transaction
				stock_value = sle.stock_value

			sle.update({
				"qty_after_transaction": actual_qty,
				"stock_value": stock_value
			})

		sle.update({
			"in_qty": max(sle.actual_qty, 0),
			"out_qty": min(sle.actual_qty, 0),
			"as_is_in_qty":max(sle.as_is_qty, 0),
			"as_is_out_qty":min(sle.as_is_qty, 0),
		})
		if item_detail.maintain_as_is_stock:
			if sle.get('out_qty'):
				sle.update({
					"outgoing_rate":flt(flt(sle.get('stock_value_difference')) / flt(sle.get('out_qty')) * 100) / flt(concentration) if sle.get('stock_value_difference') else 0
				})
			else:
				sle.update({
					"outgoing_rate":0
				})

			if sle.get('as_is_out_qty'):
				sle.update({
					"as_is_outgoing_rate":flt(sle.get('stock_value_difference')) / flt(sle.get('as_is_out_qty')) if sle.get('stock_value_difference') else 0
				})
			else:
				sle.update({
					"as_is_outgoing_rate":0
				})

		else:
			if sle.get('out_qty'):
				sle.update({
					"outgoing_rate":flt(sle.get('stock_value_difference')) / flt(sle.get('out_qty')) if sle.get('stock_value_difference') else 0
				})
			else:
				sle.update({
					"outgoing_rate":0
				})

			if sle.get('as_is_out_qty'):
				sle.update({
					"as_is_outgoing_rate":flt(sle.get('stock_value_difference')) / flt(sle.get('as_is_out_qty')) if sle.get('stock_value_difference') else 0
				})
			else:
				sle.update({
					"as_is_outgoing_rate":0
				})
				
		if sle.serial_no:
			update_available_serial_nos(available_serial_nos, sle)

		data.append(sle)

		if include_uom:
			conversion_factors.append(item_detail.conversion_factor)

	update_included_uom_in_report(columns, data, include_uom, conversion_factors)
	return columns, data

def update_available_serial_nos(available_serial_nos, sle):
	serial_nos = get_serial_nos(sle.serial_no)
	key = (sle.item_code, sle.warehouse)
	if key not in available_serial_nos:
		available_serial_nos.setdefault(key, [])

	existing_serial_no = available_serial_nos[key]
	for sn in serial_nos:
		if sle.actual_qty > 0:
			if sn in existing_serial_no:
				existing_serial_no.remove(sn)
			else:
				existing_serial_no.append(sn)
		else:
			if sn in existing_serial_no:
				existing_serial_no.remove(sn)
			else:
				existing_serial_no.append(sn)

	sle.balance_serial_no = '\n'.join(existing_serial_no)

def get_columns(filters):
	columns = [
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Datetime", "width": 95},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 130},	
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 100},	
		{"label": _("In Qty"), "fieldname": "in_qty", "fieldtype": "Float", "width": 80, "convertible": "qty"},
		{"label": _("Out Qty"), "fieldname": "out_qty", "fieldtype": "Float", "width": 80, "convertible": "qty"},
		{"label": _("Balance Qty"), "fieldname": "qty_after_transaction", "fieldtype": "Float", "width": 100, "convertible": "qty"},
		{"label": _("Incoming Rate"), "fieldname": "incoming_rate", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency", "convertible": "rate"},
		{"label": _("Outgoing Rate"), "fieldname": "outgoing_rate", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency", "convertible": "rate"},
		{"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency", "convertible": "rate"},
		{"label": _("Balance Value"), "fieldname": "stock_value", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency"},
		{"label": _("Batch"), "fieldname": "batch_no", "fieldtype": "Link", "options": "Batch", "width": 120},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data","width": 100},
	]
	if filters.get('sales_lot_no'):
		columns +=[
			{"label": _("Sales Lot No"), "fieldname": "sales_lot_no", "fieldtype": "Data", "width": 80},
		] 
	columns += [
		{"label": _("Concentration"), "fieldname": "concentration", "fieldtype": "Percent","width": 100},
		]
	if filters.get('show_as_is'):
		columns += [
			{"label": _("As Is In Qty"), "fieldname": "as_is_in_qty", "fieldtype": "Float","width": 100},
			{"label": _("As Is Out Qty"), "fieldname": "as_is_out_qty", "fieldtype": "Float","width": 100},
		{"label": _("As Is Outgoing Rate"), "fieldname": "as_is_outgoing_rate", "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency", "convertible": "rate"},
			{"label": _("As Is Balance Qty"), "fieldname": "as_is_balance_qty", "fieldtype": "Float","width": 100},
		]
	columns += [
		{"label": _("Particular"), "fieldname": "particular", "fieldtype": "Data","width": 150},
		{"label": _("Voucher Type"), "fieldname": "voucher_type", "width": 110},
		{"label": _("Voucher #"), "fieldname": "voucher_no", "fieldtype": "Dynamic Link", "options": "voucher_type", "width": 100},
	]
	if filters.get('show_party'):
		columns +=[
			{"label": _("Party Type"), "fieldname": "party_type", "fieldtype": "Data", "width": 80,"align":"center"},
			{"label": _("Party"), "fieldname": "party", "fieldtype": "Data", "width": 140,"align":"left"},
		]
	
	columns +=[
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 110},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 100},
		{"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 100}
	]

	return columns

def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ''
	if items:
		item_conditions_sql = 'and sle.item_code in ({})'\
			.format(', '.join([frappe.db.escape(i) for i in items]))
	
	show_party_select = show_party_join = ''
	if filters.get('show_party'):
		#show_party_join += " Left JOIN `tabStock Entry` as se on se.name = sle.voucher_no"
		show_party_select += ", se.party_type, se.party"

	show_sales_lot_no = show_sales_lot_no_join = ''
	if filters.get('sales_lot_no'):
		show_sales_lot_no_join += " Left JOIN `tabSales Invoice Item` as sii on sii.parent = sle.voucher_no"
		show_sales_lot_no += ", sii.lot_no as sales_lot_no"

	return frappe.db.sql("""select concat_ws(" ", sle.posting_date, sle.posting_time) as date,
			sle.item_code, sle.warehouse, sle.actual_qty, sle.qty_after_transaction, sle.incoming_rate, sle.valuation_rate,
			sle.stock_value, sle.voucher_type, sle.voucher_no, sle.batch_no, sle.serial_no, sle.company, sle.project, sle.stock_value_difference,
			b.lot_no, b.concentration,IFNULL(pr.supplier, IFNULL(pi.supplier,IFNULL(dn.customer,IFNULL(si.customer,se.stock_entry_type)))) as particular
			{show_party_select}{show_sales_lot_no}
		from `tabStock Ledger Entry` sle 
		left join `tabBatch` as b on sle.batch_no = b.name
		LEFT JOIN `tabPurchase Receipt` as pr on pr.name = sle.voucher_no
		LEFT JOIN `tabPurchase Invoice` as pi on pi.name = sle.voucher_no
		LEFT JOIN `tabDelivery Note` as dn on dn.name = sle.voucher_no
		LEFT JOIN `tabSales Invoice` as si on si.name = sle.voucher_no
		LEFT JOIN `tabStock Entry` as se on se.name = sle.voucher_no{show_sales_lot_no_join}
		where
			sle.is_cancelled = 0 and sle.posting_date between %(from_date)s and %(to_date)s
			{sle_conditions}
			{item_conditions_sql}
			order by sle.posting_date asc, sle.posting_time asc, sle.creation asc"""\
		.format(
			show_party_select = show_party_select,
			show_sales_lot_no = show_sales_lot_no,
			show_sales_lot_no_join = show_sales_lot_no_join,
			sle_conditions=get_sle_conditions(filters),
			item_conditions_sql = item_conditions_sql
		), filters, as_dict=1)

def get_items(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))

	items = []
	if conditions:
		items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
			.format(" and ".join(conditions)), filters)
	return items

def get_item_details(items, sl_entries, include_uom):
	item_details = {}
	if not items:
		items = list(set([d.item_code for d in sl_entries]))

	if not items:
		return item_details

	cf_field = cf_join = ""
	if include_uom:
		cf_field = ", ucd.conversion_factor"
		cf_join = "left join `tabUOM Conversion Detail` ucd on ucd.parent=item.name and ucd.uom=%s" \
			% frappe.db.escape(include_uom)

	res = frappe.db.sql("""
		select
			item.name, item.item_name, item.description, item.item_group, item.maintain_as_is_stock, item.stock_uom {cf_field}
		from
			`tabItem` item
			{cf_join}
		where
			item.name in ({item_codes})
	""".format(cf_field=cf_field, cf_join=cf_join, item_codes=','.join(['%s'] *len(items))), items, as_dict=1)

	for item in res:
		item_details.setdefault(item.name, item)

	return item_details

def get_sle_conditions(filters):
	conditions = []
	if filters.get("warehouse"):
		warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
		if warehouse_condition:
			conditions.append(warehouse_condition)
	if filters.get("voucher_no"):
		conditions.append("sle.voucher_no=%(voucher_no)s")
	if filters.get("batch_no"):
		conditions.append("sle.batch_no=%(batch_no)s")
	if filters.get("company"):
		conditions.append("sle.company=%(company)s")
	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_opening_balance(filters, columns):
	if not (filters.item_code and filters.warehouse and filters.from_date):
		return

	from erpnext.stock.stock_ledger import get_previous_sle
	last_entry = get_previous_sle({
		"item_code": filters.item_code,
		"warehouse_condition": get_warehouse_condition(filters.warehouse),
		"posting_date": filters.from_date,
		"posting_time": "00:00:00"
	})
	# opening_actual_qty = frappe.db.sql("""
	# 	Select 
	# 		sum(sle.actual_qty)*bt.concentration
	# 	from 
	# 		`tabStock Ledger Entry` sle left join `tabBatch` as b on sle.batch_no = b.name
	# 	where sle.company = %(company)s and
	# 		sle.posting_date between %(from_date)s and %(to_date)s
	# 		{sle_conditions}
	# 		{item_conditions_sql}
	# 		order by sle.posting_date asc, sle.posting_time asc, sle.creation asc"""\
	# 	.format(
	# 		show_party_select = show_party_select,
	# 		show_party_join = show_party_join,
	# 		sle_conditions=get_sle_conditions(filters),
	# 		item_conditions_sql = item_conditions_sql
	# 	), filters, as_dict=1)		
	# """)
	row = {
		"item_code": _("'Opening'"),
		"qty_after_transaction": last_entry.get("qty_after_transaction", 0),
		"valuation_rate": last_entry.get("valuation_rate", 0),
		"stock_value": last_entry.get("stock_value", 0)
	}

	return row

def get_warehouse_condition(warehouse):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	if warehouse_details:
		return " exists (select name from `tabWarehouse` wh \
			where wh.lft >= %s and wh.rgt <= %s and warehouse = wh.name)"%(warehouse_details.lft,
			warehouse_details.rgt)

	return ''

def get_item_group_condition(item_group):
	item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
	if item_group_details:
		return "item.item_group in (select ig.name from `tabItem Group` ig \
			where ig.lft >= %s and ig.rgt <= %s and item.item_group = ig.name)"%(item_group_details.lft,
			item_group_details.rgt)

	return ''

@frappe.whitelist()
def show_party_hidden():
	doc = frappe.get_doc({"doctype":"Stock Entry"})
	if hasattr(doc,'party'):
		return 1
	else:
		return 0