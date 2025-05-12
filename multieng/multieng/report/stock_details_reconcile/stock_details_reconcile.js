// Copyright (c) 2016, Hardik Gadesha and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Details Reconcile"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "100",
			"options": "Company",
			"default": frappe.defaults.get_user_default("company"),
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "100",
			"default": frappe.datetime.month_start()
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "100",
			"default": frappe.datetime.month_end()
		},
		{
			"fieldname":"item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"width": "100",
			"options": "Item"
		},
		{
			"fieldname":"team",
			"label": __("Team"),
			"fieldtype": "MultiSelectList",
			"width": "100",
			"options": "Team",
			get_query: () => {
				return {
					query: "group_multitech.group_multitech.report.stock_detail.stock_detail.team_query",
				};
			},
			get_data: function(txt) {
				return frappe.db.get_link_options('Team', txt);
			}
		},
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"width": "100",
			"options": "Project"
			// get_data: function(txt) {
			// 	return frappe.db.get_link_options('Project', txt);
			// }
		},
		{
			"fieldname":"pmt",
			"label": __("PMT"),
			"fieldtype": "MultiSelectList",
			"width": "100",
			get_data: function(txt) {
				return frappe.db.get_link_options('PMT', txt);
			}
		},
		{
			"fieldname":"ke_store",
			"label": __("KE Store"),
			"fieldtype": "MultiSelectList",
			"width": "100",
			get_data: function(txt) {
				return frappe.db.get_link_options('KE Store', txt);
			}
		},
		{
			"fieldname":"sto",
			"label": __("STO"),
			"fieldtype": "MultiSelectList",
			"width": "100",
			get_data: function(txt) {
				return frappe.db.get_link_options('STO', txt);
			}
		},
		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "MultiSelectList",
			"width": "100",
			get_data: function(txt) {
				return frappe.db.get_link_options('Warehouse', txt);
			}
		},
	]
};
