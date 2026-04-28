# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns, data = [], []
	columns = get_columns(filters)
	columns, data = get_data(filters,columns)
	return columns, data

def get_data(filters,columns):
	opening_data, closing_data = get_opening_closing_data(filters)
	sle_data,columns,work_order_map,columns_list = get_sle_data(filters,columns)
	data = get_item_details(filters,sle_data, opening_data, closing_data,work_order_map,columns_list)
	return columns, data

def get_opening_closing_data(filters):
	conditions = get_sle_conditions(filters)
	opening_data = frappe.db.sql("""
		select sle.item_code, CASE WHEN (i.maintain_as_is_stock = 1) THEN sum((sle.actual_qty * bt.concentration)/100) ELSE sum(sle.actual_qty) END AS opening_stock
		from `tabStock Ledger Entry` as sle
		LEFT JOIN `tabItem` as i ON sle.item_code = i.name
		LEFT JOIN `tabBatch` as bt ON bt.name = sle.batch_no
		where sle.posting_date < '{}' and sle.docstatus = 1 and sle.warehouse NOT LIKE '%Jobwork Out%' {}
		group by sle.item_code
	""".format(filters.from_date,conditions),as_dict=1)

	closing_data = frappe.db.sql("""
		select sle.item_code, CASE WHEN (i.maintain_as_is_stock = 1 AND bt.concentration !=0) THEN sum((sle.actual_qty * bt.concentration)/100) ELSE sum(sle.actual_qty) END AS closing_stock
		from `tabStock Ledger Entry` as sle
		LEFT JOIN `tabItem` as i ON sle.item_code = i.name
		LEFT JOIN `tabBatch` as bt ON bt.name = sle.batch_no
		where sle.posting_date <= '{}' and sle.docstatus = 1 and sle.warehouse NOT LIKE '%Jobwork Out%' {}
		group by sle.item_code
	""".format(filters.to_date, conditions),as_dict=1)

	return opening_data,closing_data

def get_sle_data(filters,columns):
	conditions = get_sle_conditions(filters)
	sle_data = frappe.db.sql("""
		select sle.item_code, sle.actual_qty, sle.voucher_type, sle.voucher_no, i.item_group,
			i.maintain_as_is_stock, bt.concentration, se.stock_entry_type, se.name, se.work_order
		from `tabStock Ledger Entry` as sle
		LEFT JOIN `tabItem` as i ON sle.item_code = i.name
		LEFT JOIN `tabBatch` as bt ON bt.name = sle.batch_no
		LEFT JOIN `tabStock Entry` as se ON se.name = sle.voucher_no
		where sle.posting_date BETWEEN '{}' and '{}' {}
	""".format(filters.from_date,filters.to_date, conditions),as_dict=1)

	columns_list = []
	work_order_map = {}

	if filters.get('show_production_items'):
		wo_conditions = get_work_order_conditions(filters)
		work_order_data = frappe.db.sql("""
			select woi.item_code, woi.consumed_qty, wo.production_item
			from `tabWork Order` as wo
			JOIN `tabWork Order Item` as woi on woi.parent = wo.name
			JOIN `tabStock Entry` as se on se.work_order = wo.name
			where wo.docstatus = 1 and se.posting_date BETWEEN '{}' and '{}'
			and se.docstatus = 1 and se.purpose = 'Manufacture' {}
		""".format(filters.from_date,filters.to_date,wo_conditions),as_dict=1)

		for wo in work_order_data:
			if wo.production_item not in columns_list:
				columns_list.append(wo.production_item)
				columns += [{"label": _(wo.production_item), "fieldname": wo.production_item, "fieldtype": "Data", "width": 120},]

			work_order_map.setdefault(wo.item_code, frappe._dict({
					wo.production_item: 0.0,
				}))
			work_order_dict = work_order_map[wo.item_code]

			if not work_order_dict.get(wo.production_item):
				work_order_dict[wo.production_item] = flt(wo.consumed_qty)
			else:
				work_order_dict[wo.production_item] += flt(wo.consumed_qty)
		columns += [
				# {"label": _("Total outward"), "fieldname": "total_outward", "fieldtype": "Float", "width": 100},
				{"label": _("Closing Stock"), "fieldname": "closing_stock", "fieldtype": "Float", "width": 120},			
		]
	sle_details = []
	sle_map = {}
	for sle in sle_data:
		# if filters.get('show_production_items'):
		# 	work_order_dict = work_order_map.get(sle.item_code)
		# 	if work_order_dict:
		# 		sle[list(work_order_dict.keys())[0]] = work_order_dict.get(list(work_order_dict.keys())[0])
		if sle.maintain_as_is_stock and sle.concentration:
			sle.actual_qty = flt(sle.actual_qty * sle.concentration / 100)
		if sle.voucher_type in ["Purchase Receipt", "Purchase Invoice"] and sle.actual_qty >0:
			sle.received = sle.actual_qty
		if sle.voucher_type in ["Delivery Note", "Sales Invoice"] and sle.actual_qty < 0:
			sle.sales = sle.actual_qty
		if sle.voucher_type == "Stock Entry" and sle.actual_qty > 0 and sle.stock_entry_type in ["Manufacture","Repack"]:
			sle.production = sle.actual_qty
		if sle.voucher_type == "Stock Entry" and sle.actual_qty < 0 and sle.stock_entry_type in ["Manufacture","Repack"]:
			sle.captive_consumption = abs(sle.actual_qty)
		if sle.voucher_type == "Stock Entry" and sle.stock_entry_type == "Receive Jobwork Return" and sle.actual_qty > 0 and not sle.name.find('HJF') > 0:
			sle.unprocessed_return = abs(sle.actual_qty)
		if sle.voucher_type == "Stock Entry" and sle.stock_entry_type == "Receive Jobwork Return" and sle.actual_qty > 0 and sle.name.find('HJF') > 0:
			sle.processed_return = abs(sle.actual_qty)
		if sle.voucher_type == "Stock Entry" and sle.stock_entry_type == "Send to Jobwork" and sle.actual_qty < 0:
			sle.sent_to_job_work = abs(sle.actual_qty)
		if sle.voucher_type == "Stock Entry" and sle.stock_entry_type == "Material Receipt" and sle.actual_qty > 0:
			sle.receipt = sle.actual_qty
		if sle.voucher_type == "Stock Entry" and sle.stock_entry_type == "Send Jobwork Finish" and sle.actual_qty < 0:
			sle.send_jobwork_finish = abs(sle.actual_qty)
		if sle.voucher_type == "Stock Entry" and sle.stock_entry_type == "Receive Jobwork Raw Material" and sle.actual_qty > 0:
			sle.receive_jobwork_raw_material = abs(sle.actual_qty)
	return sle_data,columns,work_order_map,columns_list

def get_item_details(filters,sle_data,opening_data,closing_data,work_order_map,columns_list):
	item_map = {}
	opening_map = {}
	closing_map = {}
	data = []
	qty_dict = {}
	sle_list = []
	for sle in sle_data:
		item_map.setdefault(sle.item_code,frappe._dict({
			"received":0.0 , "receipt":0.0, "sales":0.0,"production":0.0, "captive_consumption":0.0,\
			"unprocessed_return":0.0, "processed_return":0.0,\
			"sent_to_job_work":0.0, "send_jobwork_finish":0.0, "receive_jobwork_raw_material":0.0,\
			"opening_stock":0.0,"closing_stock":0.0
		}))
		item_map[sle.item_code].received += flt(sle.received)
		item_map[sle.item_code].receipt += flt(sle.receipt)
		item_map[sle.item_code].sales += flt(sle.sales)
		item_map[sle.item_code].production += flt(sle.production)
		item_map[sle.item_code].captive_consumption += flt(sle.captive_consumption)
		item_map[sle.item_code].unprocessed_return += flt(sle.unprocessed_return)
		item_map[sle.item_code].processed_return += flt(sle.processed_return)
		item_map[sle.item_code].sent_to_job_work += flt(sle.sent_to_job_work)
		item_map[sle.item_code].send_jobwork_finish += flt(sle.send_jobwork_finish)
		item_map[sle.item_code].receive_jobwork_raw_material += flt(sle.receive_jobwork_raw_material)

	for opening in opening_data:
		opening_map.setdefault(opening.item_code,frappe._dict({
			"opening_stock":0.0
		}))
		opening_dict = opening_map[opening.item_code]
		opening_dict.opening_stock += flt(opening.opening_stock)

		if opening.item_code not in item_map:
			item_map[opening.item_code] = frappe._dict({
			"received":0.0 , "receipt":0.0, "sales":0.0,"production":0.0, "captive_consumption":0.0,\
			"unprocessed_return":0.0, "processed_return":0.0,\
			"sent_to_job_work":0.0, "send_jobwork_finish":0.0, "receive_jobwork_raw_material":0.0,\
			"opening_stock":0.0,"closing_stock":0.0
		})
	for closing in closing_data:
		closing_map.setdefault(closing.item_code,frappe._dict({
			"closing_stock":0.0
		}))
		closing_dict = closing_map[closing.item_code]
		closing_dict.closing_stock += flt(closing.closing_stock)
		
		if closing.item_code not in item_map:
			item_map[closing.item_code] = frappe._dict({
			"received":0.0 , "receipt":0.0, "sales":0.0,"production":0.0, "captive_consumption":0.0,\
			"unprocessed_return":0.0, "processed_return":0.0,\
			"sent_to_job_work":0.0, "send_jobwork_finish":0.0, "receive_jobwork_raw_material":0.0,\
			"opening_stock":0.0,"closing_stock":0.0
		})
	for item,value in item_map.items():
		try:
			opening_dict = opening_map[item]
			opening_stock = opening_dict.opening_stock
		except KeyError:
			opening_stock = 0.0
		try:
			closing_dict = closing_map[item]
			closing_stock = closing_dict.closing_stock
		except KeyError:
			closing_stock = 0.0

		dict_work_order = {
			"item_code":item,
			"received":flt(value.received,2),
			"receipt":flt(value.receipt,2),
			"sales":flt(value.sales,2),
			"production":flt(value.production,2),
			"captive_consumption":flt(value.captive_consumption,2),
			"unprocessed_return":flt(value.unprocessed_return,2),
			"processed_return":flt(value.processed_return,2),
			"sent_to_job_work":flt(value.sent_to_job_work,2),
			"send_jobwork_finish":flt(value.send_jobwork_finish,2),
			"receive_jobwork_raw_material":flt(value.receive_jobwork_raw_material,2),
			"opening_stock":flt(opening_stock,2),
			"closing_stock":flt(closing_stock,2),
		}

		if filters.get('show_production_items'):
			pro_value = 0
			work_order_dict = work_order_map.get(item)
			if work_order_dict:
				for col in columns_list:
					dict_work_order.update({col:flt(work_order_dict.get(col),2)})
		data.append(dict_work_order)
	
	
	return data

def get_sle_conditions(filters):
	conditions = ''
	if filters.get('company'):
		conditions += " AND sle.company = '{}'".format(filters.company)
	if filters.get('item_code'):
		conditions += " AND sle.item_code = '{}'".format(filters.item_code)
	if filters.get('item_group'):
		conditions += " AND i.item_group = '{}'".format(filters.item_group)
	return conditions
	
def get_work_order_conditions(filters):
	conditions = ''
	if filters.get('company'):
		conditions += " AND wo.company = '{}'".format(filters.company)
	if filters.get('item_code'):
		conditions += " AND woi.item_code = '{}'".format(filters.item_code)
	return conditions

def get_columns(filters):
	columns = [
			{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 230},
			{"label": _("Opening Stock"), "fieldname": "opening_stock", "fieldtype": "Float", "width": 120},
			{"label": _("Purchase"), "fieldname": "received", "fieldtype": "Float", "width": 100},
			{"label": _("Receipt"), "fieldname": "receipt", "fieldtype": "Float", "width": 100},
			{"label": _("Production"), "fieldname": "production", "fieldtype": "Float", "width": 100},
			{"label": _("Unprocessed Return"), "fieldname": "unprocessed_return", "fieldtype": "Float", "width": 100},
			{"label": _("Processed Return"), "fieldname": "processed_return", "fieldtype": "Float", "width": 100},
			{"label": _("Sent to Job Work"), "fieldname": "sent_to_job_work", "fieldtype": "Float", "width": 100},
			{"label": _("Send Jobwork Finish"), "fieldname": "send_jobwork_finish", "fieldtype": "Float", "width": 100},
			{"label": _("Receive Jobwork Raw material"), "fieldname": "receive_jobwork_raw_material", "fieldtype": "Float", "width": 100},
			{"label": _("Sales"), "fieldname": "sales", "fieldtype": "Float", "width": 100}
	]
	if filters.get('show_production_items'):
		return columns
	else:
		columns += [
				{"label": _("Captive Consumption"), "fieldname": "captive_consumption", "fieldtype": "Float", "width": 100},
				# {"label": _("Total outward"), "fieldname": "total_outward", "fieldtype": "Float", "width": 100},
				{"label": _("Closing Stock"), "fieldname": "closing_stock", "fieldtype": "Float", "width": 120},
		]
		return columns