# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions
from collections import defaultdict

def execute(filters=None):
	if not filters:
		filters = {}

	conditions = get_conditions(filters)
	data = []

	master = get_master(conditions,filters)
	received_or_consumed = get_received_or_consumed(conditions,filters)
	received_date_wise_qty = get_received_date_wise_qty(conditions,filters)
	issued_date_wise_qty = get_issued_date_wise_qty(conditions,filters)
	return_date_wise_qty = get_return_date_wise_qty(conditions,filters)
	transfer_to_pqc_date_wise_qty = get_transfer_to_pqc_date_wise_qty(conditions,filters)
	transfer_from_pqc_date_wise_qty = get_transfer_from_pqc_date_wise_qty(conditions,filters)
	if filters.get('project'):
		transfer_from_date_wise_qty = get_transfer_from_date_wise_qty(conditions,filters)
		transfer_to_date_wise_qty = get_transfer_to_date_wise_qty(conditions,filters)
	else:
		transfer_from_date_wise_qty = None
		transfer_to_date_wise_qty = None

	received_dates = frappe.db.sql("""select posting_date, p.project from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Material Receipt' %s group by 1 order by 1"""%(conditions),filters, as_dict=1)

	consumed_dates = frappe.db.sql("""select posting_date, p.project from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Material Issue' %s group by 1 order by 1"""%(conditions),filters, as_dict=1)

	return_dates = frappe.db.sql("""select posting_date, p.project from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Material Return' %s group by 1 order by 1"""%(conditions),filters, as_dict=1)
	
	transfer_from_pqc_dates = frappe.db.sql("""select posting_date, p.project, p.stock_entry_type from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type IN ('Transfer From PQC') %s group by 1 order by 1"""%(conditions),filters, as_dict=1)

	transfer_to_pqc_dates = frappe.db.sql("""select posting_date, p.project, p.stock_entry_type from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type IN ('Transfer To PQC') %s group by 1 order by 1"""%(conditions),filters, as_dict=1)
	
	if filters.get('project'):
		transfer_from_dates = frappe.db.sql("""select posting_date, p.project, p.stock_entry_type from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
			where p.docstatus = 1 and stock_entry_type IN ('Transfer From PQC') %s group by 1 order by 1"""%(conditions),filters, as_dict=1)

		transfer_to_dates = frappe.db.sql("""select posting_date, p.project, p.stock_entry_type from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
			where p.docstatus = 1 and stock_entry_type IN ('Transfer To Project', 'Transfer To PQC') %s group by 1 order by 1"""%(conditions),filters, as_dict=1)
	else:
		transfer_to_dates = None
		transfer_from_dates = None

	columns = get_column(filters,conditions, received_dates, consumed_dates, return_dates, transfer_to_dates, transfer_from_dates,transfer_from_pqc_dates, transfer_to_pqc_dates)

	if filters.get("warehouse"):
		filters.warehouse = frappe.parse_json(filters.get('warehouse'))

	for i in master:
		row={}
		row["item_name1"] = i.item_name
		row["item_code1"] = i.item_code
		row.update(i)
		row["received"] = 0
		row["consumed"] = 0
		row['return'] = 0
		row['transfer_from'] = 0
		row['transfer_to'] = 0
		row['transfer_from_pqc'] = 0
		row['transfer_to_pqc'] = 0
		for r in received_or_consumed:
			if r.item_code == i.item_code and r.stock_entry_type == "Material Receipt":
				if filters.get("warehouse"):
					if r.t_warehouse in filters.warehouse:
						row["received"] += r.qty
				else:
					row["received"] += r.qty
			elif r.item_code == i.item_code and r.stock_entry_type == "Material Return":
				if filters.get("warehouse"):
					if r.s_warehouse in filters.warehouse:
						row["return"] += r.qty
				else:
					row["return"] += r.qty			
			elif r.item_code == i.item_code and r.stock_entry_type == "Material Issue":
				if filters.get("warehouse"):
					if r.s_warehouse in filters.warehouse:
						row["consumed"] += r.qty
				else:
					row["consumed"] += r.qty
			
			elif r.item_code == i.item_code and r.stock_entry_type == "Transfer From PQC":
				if filters.get("warehouse"):
					if r.s_warehouse in filters.warehouse:
						row["transfer_from_pqc"] += r.qty
				else:
					row["transfer_from_pqc"] += r.qty
			elif r.item_code == i.item_code and r.stock_entry_type == "Transfer To PQC":
				if filters.get("warehouse"):
					if r.s_warehouse in filters.warehouse:
						row["transfer_to_pqc"] += r.qty
				else:
					row["transfer_to_pqc"] += r.qty
			elif r.item_code == i.item_code and r.stock_entry_type == "Transfer To Project":
				if filters.get("warehouse"):
					if r.s_warehouse in filters.warehouse:
							if r.project == filters.get('project'):
								row["transfer_to"] += r.qty
							else:
								row['transfer_from'] += r.qty
					else:
						if r.project == filters.get('project'):
							row["transfer_to"] += r.qty
						else:
							row['transfer_from'] += r.qty
						
		row["balance"] = (row.get("received")+row.get('transfer_from')+row.get('transfer_from_pqc')) - (row.get("consumed")+row.get('return')+row.get('transfer_to')-row.get('transfer_to_pqc'))
		# row["balance"] = (row.get("received")) - (row.get("consumed")+row.get('return')+row.get('transfer_to'))

		for d in received_date_wise_qty:
			if d.item_code == i.item_code:
				key = "recev_" + frappe.scrub(str(d.posting_date))
				row[key] = d.qty

		for d in return_date_wise_qty:
			if d.item_code == i.item_code:
				key = "return_" + frappe.scrub(str(d.posting_date))
				row[key] = d.qty
		
		for d in transfer_from_pqc_date_wise_qty:
			if d.item_code == i.item_code:
				key = "transfer_from_pqc_" + frappe.scrub(str(d.posting_date))
				row[key] = d.qty

		for d in transfer_to_pqc_date_wise_qty:
			if d.item_code == i.item_code:
				key = "transfer_to_pqc_" + frappe.scrub(str(d.posting_date))
				row[key] = d.qty

		
		
		for d in issued_date_wise_qty:
			if d.item_code == i.item_code:
				key = "consum_" + frappe.scrub(str(d.posting_date))
				row[key] = d.qty

		if filters.get('project'):
			for d in transfer_from_date_wise_qty:
				if d.item_code == i.item_code:
					key = "transfer_from_" + frappe.scrub(str(d.posting_date))
					row[key] = d.qty

			for d in transfer_to_date_wise_qty:
				if d.item_code == i.item_code:
					if d.stock_entry_type == "Transfer To PQC":
						key = "transfer_to_" + frappe.scrub(str(d.posting_date))
						row[key] = d.qty

			for d in transfer_to_date_wise_qty:
				if d.item_code == i.item_code:
					if d.stock_entry_type == "Transfer To Project":
						if d.project == filters.get('project'):
							key = "transfer_to_" + frappe.scrub(str(d.posting_date))
							row[key] = d.qty
						else:
							key = "transfer_from_" + frappe.scrub(str(d.posting_date))
							row[key] = d.qty

		
		data.append(row)

	# data = []

	return columns, data

def get_column(filters,conditions, received_date, consumed_date, return_date, transfer_to_date, transfer_from_date, transfer_from_pqc_dates,transfer_to_pqc_dates):
	columns = [
		{
			"fieldname": "item_code1",
			"label": _("SAP Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 90
		},
		{
			"fieldname": "item_name1",
			"label": _("Material Description"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "uom",
			"label": _("Unit"),
			"fieldtype": "Data",
			"width": 60
		},
	]

	if filters.get('project'):
		for d in get_return_date_wise_qty(conditions, filters):
			# is_project = bool(filters.get('project'))
			if d.project == filters.get('project'):
				columns.append({
					"fieldname": "recev_" + frappe.scrub(str(d.posting_date)),
					"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
					"fieldtype": "Link",
					"options": "PMT",
					"width": 100
				})
	else:
		for d in received_date:
			# is_project = bool(filters.get('project'))
			# if d.project in filters.get('project') or (not is_project):
			columns.append({
				"fieldname": "recev_" + frappe.scrub(str(d.posting_date)),
				"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
				"fieldtype": "Link",
				"options": "PMT",
				"width": 100
			})

	columns +=  [
		{
			"fieldname": "received",
			"label": _("Material Received"),
			"fieldtype": "Float",
			"width": 130
		},
	]
	
	if filters.get('project'):
		for d in get_return_date_wise_qty(conditions, filters):
			# is_project = bool(filters.get('project'))
			if d.project == filters.get('project'):
				columns.append({
					"fieldname": "return_" + frappe.scrub(str(d.posting_date)),
					"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
					"fieldtype": "Float",
					"width": 100
				})
	else:
		for d in return_date:
			# is_project = bool(filters.get('project'))
			# if d.project in filters.get('project') or (not is_project) :
			columns.append({
				"fieldname": "return_" + frappe.scrub(str(d.posting_date)),
				"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
				"fieldtype": "Float",
				"width": 100
			})

	columns += [{
			"fieldname": "return",
			"label": _("Material Return"),
			"fieldtype": "Float",
			"width": 140
	}]

	if filters.get('project'):
		for d in get_issued_date_wise_qty(conditions, filters):
			# is_project = bool(filters.get('project'))
			if d.project == filters.get('project'):
				columns.append({
					"fieldname": "consum_" + frappe.scrub(str(d.posting_date)),
					"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
					"fieldtype": "Link",
					"options": "PMT",
					"width": 100
				})
	else:
		for d in consumed_date:
			# is_project = bool(filters.get('project'))
			# if d.project in filters.get('project') or (not is_project) :
				columns.append({
				"fieldname": "consum_" + frappe.scrub(str(d.posting_date)),
				"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
				"fieldtype": "Link",
				"options": "PMT",
				"width": 100
			})

	columns +=[{
		"fieldname": "consumed",
		"label": _("Material Consumed"),
		"fieldtype": "Float",
		"width": 140
	}]

	if filters.get('project'):
		for d in transfer_from_date:
			columns.append({
				"fieldname": "transfer_from_" + frappe.scrub(str(d.posting_date)),
				"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
				"fieldtype": "Float",
				"width": 100
			})
		
		for d in transfer_to_date:
			if d.stock_entry_type == 'Transfer To Project':
				if d.project != filters.get('project'):
					columns.append({
						"fieldname": "transfer_from_" + frappe.scrub(str(d.posting_date)),
						"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
						"fieldtype": "Float",
						"width": 100
					})

		columns += [{
				"fieldname": "transfer_from",
				"label": _("Transfer From"),
				"fieldtype": "Float",
				"width": 140
		}]


	if filters.get('project'):
		for d in transfer_to_date:
			if d.stock_entry_type == 'Transfer To PQC':
				columns.append({
					"fieldname": "transfer_to_" + frappe.scrub(str(d.posting_date)),
					"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
					"fieldtype": "Float",
					"width": 100
				})
			elif d.stock_entry_type == 'Transfer To Project':
				if d.project == filters.get('project'):
					columns.append({
						"fieldname": "transfer_to_" + frappe.scrub(str(d.posting_date)),
						"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
						"fieldtype": "Float",
						"width": 100
					})


		columns += [{
				"fieldname": "transfer_to",
				"label": _("Transfer To"),
				"fieldtype": "Float",
				"width": 140
		}]
	if filters.get('project'):
		for d in transfer_from_pqc_dates:
			if d.project == filters.get('project'):
				columns.append({
					"fieldname": "transfer_from_pqc_" + frappe.scrub(str(d.posting_date)),
					"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
					"fieldtype": "Float",
					"width": 100
				})
	else:
		for d in transfer_from_pqc_dates:
			columns.append({
				"fieldname": "transfer_from_pqc_" + frappe.scrub(str(d.posting_date)),
				"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
				"fieldtype": "Float",
				"width": 100
			})
	columns += [{
			"fieldname": "transfer_from_pqc",
			"label": _("Transfer From PQC"),
			"fieldtype": "Float",
			"width": 140
	}]

	if filters.get('project'):
		for d in transfer_to_pqc_dates:
			if d.project == filters.get('project'):
				columns.append({
					"fieldname": "transfer_to_pqc_" + frappe.scrub(str(d.posting_date)),
					"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
					"fieldtype": "Float",
					"width": 100
				})
	else:
		for d in transfer_to_pqc_dates:
			columns.append({
				"fieldname": "transfer_to_pqc_" + frappe.scrub(str(d.posting_date)),
				"label": _(frappe.utils.get_datetime(d.posting_date).strftime("%d-%m-%y")),
				"fieldtype": "Float",
				"width": 100
			})
	columns += [{
				"fieldname": "transfer_to_pqc",
				"label": _("Transfer To PQC"),
				"fieldtype": "Float",
				"width": 140
		}]

	columns += [{
			"fieldname": "balance",
			"label": _("Balance"),
			"fieldtype": "Float",
			"width": 100
	}]	

	return columns

def get_master(conditions, filters):
	master = {}
	qty = {}
	data = frappe.db.sql("""select item_code,c.item_name, c.uom, c.qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 %s group by 1 order by 1"""%(conditions), filters, as_dict=1)
	# data = frappe.db.sql("""select item_code,c.item_name, c.uom from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
	# 	where p.docstatus = 1 %s group by 1 order by 1"""%(conditions), filters, as_dict=1)

	return data


def get_received_or_consumed(conditions, filters):
	# data= frappe.db.sql("""select SUM(c.qty) as qty, stock_entry_type, item_code, c.t_warehouse, c.s_warehouse from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
	# 	where p.docstatus = 1 %s group by 2,3,4,5
	# 	"""%(conditions), filters, as_dict=1)
	data= frappe.db.sql("""select c.qty, p.project, stock_entry_type, item_code, c.t_warehouse, c.s_warehouse from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 %s 
		"""%(conditions), filters, as_dict=1)
	return data

def get_received_date_wise_qty(conditions, filters):
	warehouse = get_receipt_warehouse(filters)
	data= frappe.db.sql("""select item_code, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Material Receipt' %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

def get_issued_date_wise_qty(conditions, filters):
	warehouse = get_issue_warehouse(filters)
	data= frappe.db.sql("""select item_code, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Material Issue' %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

def get_return_date_wise_qty(conditions, filters):
	warehouse = get_issue_warehouse(filters)
	data= frappe.db.sql("""select item_code, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Material Return' %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

def get_transfer_to_pqc_date_wise_qty(conditions, filters):
	warehouse = get_issue_warehouse(filters)
	data= frappe.db.sql("""select item_code, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Transfer To PQC' %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

def get_transfer_from_pqc_date_wise_qty(conditions, filters):
	warehouse = get_issue_warehouse(filters)
	data= frappe.db.sql("""select item_code, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type = 'Transfer From PQC' %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

# def get_transfer_from_date_wise_qty(conditions, filters):
# 	warehouse = get_issue_warehouse(filters)
# 	data= frappe.db.sql("""select item_code, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
# 		where p.docstatus = 1 and stock_entry_type IN ('Transfer From Project', 'Transfer From PQC') %s %s group by 1,2 order by 1,2
# 		"""%(conditions, warehouse), filters, as_dict=1)
# 	return data

def get_transfer_from_date_wise_qty(conditions, filters):
	warehouse = get_issue_warehouse(filters)
	data= frappe.db.sql("""select item_code, p.project, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type IN ('Transfer From PQC') %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

def get_transfer_to_date_wise_qty(conditions, filters):
	warehouse = get_issue_warehouse(filters)
	data= frappe.db.sql("""select item_code, p.project, p.stock_entry_type, posting_date,SUM(c.qty) as qty from `tabStock Entry` p inner join `tabStock Entry Detail` c on p.name = c.parent
		where p.docstatus = 1 and stock_entry_type IN ('Transfer To Project', 'Transfer To PQC') %s %s group by 1,2 order by 1,2
		"""%(conditions, warehouse), filters, as_dict=1)
	return data

def get_receipt_warehouse(filters):
	conditions = ''
	if filters.get("warehouse"):
		filters.warehouse = frappe.parse_json(filters.get('warehouse'))
		conditions += " and c.t_warehouse in %(warehouse)s"

	return conditions

def get_issue_warehouse(filters):
	conditions = ''
	if filters.get("warehouse"):
		filters.warehouse = frappe.parse_json(filters.get('warehouse'))
		conditions += " and c.s_warehouse in %(warehouse)s"

	return conditions


def get_conditions(filters):
	conditions = ""
	if filters.get("item_code"):
		filters.item_code = filters.get('item_code')
		conditions += " and c.item_code = %(item_code)s"
	if filters.get("from_date"):
		filters.from_date = filters.get('from_date')
		conditions += " and p.posting_date >= %(from_date)s"
	if filters.get("to_date"):
		filters.to_date = filters.get('to_date')
		conditions += " and p.posting_date <= %(to_date)s"
	if filters.get("company"):
		filters.company = filters.get('company')
		conditions += " and p.company = %(company)s"
	if filters.get("project"):
		# filters.project = frappe.parse_json(filters.get('project'))
		filters.project = filters.get('project')
		# conditions += " and p.project in %(project)s"
		conditions += " and %(project)s IN (p.project, p.target_project)"
		# conditions += "and p.project IN %(project)s OR p.target_project IN %(project)s"
	if filters.get("pmt"):
		filters.pmt = frappe.parse_json(filters.get('pmt'))
		conditions += " and p.pmt in %(pmt)s"
	if filters.get("ke_store"):
		filters.ke_store = frappe.parse_json(filters.get('ke_store'))
		conditions += " and p.ke_store in %(ke_store)s"
	if filters.get("sto"):
		filters.sto = frappe.parse_json(filters.get('sto'))
		conditions += " and p.sto in %(sto)s"
	teams = get_teams()
	if teams:
		filters.teams = frappe.parse_json(teams)
		# conditions += " and p.teams in %(teams)s"
		conditions += " and p.team in {}".format(tuple(teams))
	return conditions


@frappe.whitelist()
def get_teams():
	conditions = []
	user = frappe.session.user
	teams = frappe.db.sql("select for_value from `tabUser Permission` where allow = 'Team' and user = '{}'".format(user))
	for d in teams:
		conditions.append(d[0])
	return conditions

def team_query(doctype, txt, searchfield, start, page_len, filters):
	conditions = []
	roles = frappe.get_roles(frappe.session.user)
	if "Team Leader" in roles:
		return frappe.db.sql("""select t.name from `tabTeam` t inner join `tabUser Permission` up on t.name = up.for_value and '{user}' = up.user
			where t.name like %(txt)s
			order by
				t.idx desc,
				t.name
			limit %(start)s, %(page_len)s""".format(**{
				"user": frappe.session.user
			}), {
				'txt': "%%%s%%" % txt,
				'_txt': txt.replace("%", ""),
				'start': start,
				'page_len': page_len
			})
	return frappe.db.sql("""select t.name from `tabTeam` t left join `tabUser Permission` up on t.name = up.for_value and '{user}' = up.user
			where t.name like %(txt)s
			order by
				t.idx desc,
				t.name
			limit %(start)s, %(page_len)s""".format(**{
				"user": frappe.session.user
			}), {
				'txt': "%%%s%%" % txt,
				'_txt': txt.replace("%", ""),
				'start': start,
				'page_len': page_len
			})




# # Copyright (c) 2013, Hardik Gadesha and contributors
# # For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe
# from frappe import _


# def execute(filters=None):
# 	stock_entries = get_all_stock_entries(get_filters_dict(filters))
# 	# columns = get_report_columns(stock_entries)
# 	# data = get_columns_data(stock_entries)
# 	columns  = [{
# 			"fieldname": "test",
# 			"label": _("test"),
# 			"fieldtype": "Data",
# 			"width": 60
# 	}]
# 	data = [{'test':len(stock_entries)}]

# 	return columns, data


# def get_report_columns(stock_entries):
# 	columns  = {
# 			"fieldname": "test",
# 			"label": _("test"),
# 			"fieldtype": "Data",
# 			"width": 60
# 	}
	
# 	return [columns]

# def get_columns_data(stock_entries):
# 	data = []
# 	for stock_entry in stock_entries:
# 		data.append(stock_entry)
	
# 	return data

# def get_all_stock_entries(filters):

# 	stock_entries = frappe.get_all(
# 		doctype='Stock Entry',
# 		fields = ['name'],
# 		filters=filters
# 	)

# 	return stock_entries

# def get_filters_dict(filters):
# 	new_filters = {'posting_date': ('between', [filters.get('from_date'), filters.get('to_date')])}
# 	# 'pmt': filters.get('pmt'),
# 	# 'ke_store': filters.get('ke_store'),
# 	# 'sto':filters.get('sto')
# 	if filters.get('team'):
# 		new_filters['team'] = ('IN', filters.get('team'))
# 	if filters.get('ke_store'):
# 		new_filters['ke_store'] = filters.get('ke_store')
# 	if filters.get('sto'):
# 		new_filters['sto'] = filters.get('sto')
# 	if filters.get('pmt'):
# 		new_filters = filters.get('pmt')


# 	return new_filters