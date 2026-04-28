# Copyright (c) 2013, FinByz Tech Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
import re

# function to clean string for names in coloumn
def clean_string(string):
	if string:
		string = string.replace(" ", "_")
		string = string.lower()
		string = re.sub('[^A-Za-z0-9_]+', '', string)
	return string

def execute(filters=None):
	if not filters: filters = {}
	from_date = filters.get("from_date", None)
	to_date = filters.get("to_date", None)

	if from_date and to_date:
		if from_date > to_date:
			frappe.throw(_("From Date cannot be less than To Date"))

	columns, columns_list = get_columns(filters)
	data = get_data(filters,columns_list)
	
	return columns, data

def get_columns(filters):
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "options": "Work Order", "width": 150},
		{"label": _("Date"), "fieldname": "planned_start_date", "fieldtype": "Date", "width": 150},
		# {"label": _("Qty To Manufacture"), "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": _("Manufactured Qty"), "fieldname": "real_produced_qty", "fieldtype": "Float", "width": 100},
		{"label": _("Current Price"), "fieldname": "current_price", "fieldtype": "Float", "width": 100},
		{"label": _("Valuation Price"), "fieldname": "valuation_price", "fieldtype": "Float", "width": 100},
		{"label": _("Concentration"), "fieldname": "concentration", "fieldtype": "Percent", "width": 100},
		# {"label": _("Standard Qty"), "fieldname": "standard_quantity", "fieldtype": "Float", "width": 100},
		# {"label": _("Standard Price"), "fieldname": "standard_price", "fieldtype": "Float", "width": 100},
		{"label": _("Lot No"), "fieldname": "lot_no", "fieldtype": "Data", "width": 120},
		{"label": _("Yield"), "fieldname": "batch_yield", "fieldtype": "Percent", "width": 80},
	]

	# append dynamic columns for item used for Manufacturing
	data = column_query(filters)
	columns_list = []
	if data:
		columns_list.append(frappe._dict({"qty":str(clean_string(data[0][1])) + "_qty","rate":str(clean_string(data[0][1])) + "_rate"}))
		columns.append({"label": _("{} Qty".format(data[0][1])), "fieldname": str(clean_string(data[0][1])) + "_qty", "fieldtype": "Float", "width": 100,"default":0.0})
		columns.append({"label": _("{} Rate".format(data[0][1])), "fieldname": str(clean_string(data[0][1])) + "_rate", "fieldtype": "Currency", "width": 100,"default":0.0})

	for d in data:
		if d[0] != d[1]:
			columns_list.append(frappe._dict({"qty":str(clean_string(d[0])) + "_qty","rate":str(clean_string(d[0])) + "_rate"}))
			columns.append({"label": _("{} Qty".format(d[0])), "fieldname": str(clean_string(d[0])) + "_qty", "fieldtype": "Float", "width": 100,"default":0.0})
			columns.append({"label": _("{} Rate".format(d[0])), "fieldname": str(clean_string(d[0])) + "_rate", "fieldtype": "Currency", "width": 100,"default":0.0})

	# columns += [
	# 	# {"label": _("Concentration / Purity"), "fieldname": "concentration", "fieldtype": "Percent", "width": 100},
	# 	# {"label": _("Valuation Rate"), "fieldname": "valuation_rate", "fieldtype": "Currency", "width": 80},
	# ]

	return columns,columns_list

def get_data(filters,columns_list):
	data = data_query(filters,columns_list)

	return data

def column_query(filters):
	# get production item from filters
	production_item = re.escape(filters.get("production_item", ""))
	conditions = ''
	if filters.get("from_date"):		
		conditions += "AND DATE(wo.planned_start_date) >= '{}' \n".format(str(filters.get("from_date")))
		
	if filters.get("to_date"):
		conditions += "AND DATE(wo.planned_start_date) <= '{}' \n".format(str(filters.get("to_date")))

	if re.escape(filters.get("company","")):
		conditions += "AND wo.company = '{}' \n".format(re.escape(filters.get("company","")))

	# Getting dynamic column name
	column = frappe.db.sql("""SELECT item_code,based_on from `tabWork Order Item` as woi
	LEFT JOIN `tabWork Order` as wo ON woi.parent = wo.name 
	WHERE `production_item` = '{}' {}
	GROUP BY item_code
	ORDER BY woi.idx
	""".format(production_item,conditions)
	)

	return column

def data_query(filters,columns_list):
	# getting data from filters
	production_item = re.escape(filters.get("production_item", ""))
	company = re.escape(filters.get("company", ""))
	from_date = filters.get("from_date", None)
	to_date = filters.get("to_date", None)
	
	# adding where condition according to filters
	condition = 'where wo.docstatus = 1 '
	format_ = '%Y-%m-%d %H:%M:%S'
	if from_date:		
		condition += ' AND ' if condition != '' else 'WHERE '
		condition += "DATE(wo.planned_start_date) >= '{}' \n".format(str(from_date))
		
	if to_date:
		condition += ' AND ' if condition != '' else 'WHERE '
		condition += "DATE(wo.planned_start_date) <= '{}' \n".format(str(to_date))

	if production_item:
		condition += ' AND ' if condition != '' else 'WHERE '
		condition += "wo.production_item = '{}' \n".format(production_item)
	
	if company:
		condition += ' AND ' if condition != '' else 'WHERE '
		condition += "wo.company = '{}' \n".format(company)
	
	# sql query to get data for column
	# wo.standard_quantity,
	# wo.standard_price,
	data = frappe.db.sql("""SELECT 
	wo.planned_start_date, 
	wo.name,
	wo.qty,
	wo.lot_no,
	wo.produced_qty,
	wo.produced_quantity,
	wo.valuation_price,
	wo.concentration,
	wo.batch_yield
	FROM  `tabWork Order Item` as woi
	LEFT JOIN `tabWork Order` as wo ON woi.parent = wo.name 
	{}
	GROUP BY wo.name
	ORDER BY wo.creation desc
	LIMIT {}
	""".format(condition,filters.get("no_of_wo")), as_dict=1)

	# sub query to find transferred quantity of item used for manufacturing
	for item in data:
		name = item.get('name', '')
		produced_quantity = item.get('produced_quantity', 0)
		concentration = item.get('concentration', 0)

		# frappe.msgprint(name)
		sub_data = frappe.db.sql("""
		SELECT 
			woi.item_code,woi.consumed_qty, ip.price_list_rate as rate
		FROM
			`tabWork Order Item` as woi
			LEFT JOIN `tabItem Price` as ip on ip.item_code = woi.item_code and ip.price_list = '{}'
		WHERE
			woi.parent = '{}'""".format(filters.get('price_list'),name),as_dict=1)

		for item_row in sub_data:
			qty_key = str(clean_string(item_row.item_code) + "_qty")
			rate_key = str(clean_string(item_row.item_code) + "_rate")
			item[qty_key] = item_row.consumed_qty or 0
			item[rate_key] = item_row.rate or 0
		
		# calculating real manufacturing quantity
		item['real_produced_qty'] = produced_quantity

		amount = 0
		for column in columns_list:
			if not item.get(column.qty):
				item[column.qty] = 0
			if not item.get(column.rate):
				item[column.rate] = 0
		
			if item.get(column.qty) and item.get(column.rate):
				amount += flt(item[column.qty] * item[column.rate],3)

		item['current_price'] = amount / item.real_produced_qty if amount and item.real_produced_qty else 0
		# item['standard_price'] = amount / item.standard_quantity if amount and item.standard_quantity else 0
	return data
