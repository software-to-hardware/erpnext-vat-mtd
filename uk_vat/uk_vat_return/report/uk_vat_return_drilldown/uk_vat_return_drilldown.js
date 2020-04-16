// Copyright (c) 2020 Software to Hardware Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["UK VAT Return Drilldown"] = {

	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company"
		},
		{
			"fieldname": "period_start_date",
			"label": "Period start date",
			"fieldtype": "Date",
		},
		{
			"fieldname": "period_end_date",
			"label": "Period end date",
			"fieldtype": "Date",
		},

	]
};
