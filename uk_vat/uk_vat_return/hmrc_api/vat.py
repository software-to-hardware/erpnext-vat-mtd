# -*- coding: utf-8 -*-
# Copyright (c) 2020 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

import frappe
from uk_vat.uk_vat_return.doctype.hmrc_authorisations.hmrc_authorisations import get_session

accept_header = { "Accept": "application/vnd.hmrc.1.0+json" }

def is_company_vat_enabled(company):

    if not frappe.db.get_single_value("HMRC API Settings", "enable"):
        return false

    enabled_count = frappe.db.sql("""
                select count(name) `tabHMRC Authorisations` a
                where 
                    a.company = %s and
                    a.authorisation_status = "Authorised"
                """, company)[0][0]

    return enabled_count > 0

def get_vrn(company):
    tax_id = frappe.db.get_value("Company", company, "tax_id")
    if not tax_id.upper().startswith("GB"):
        frappe.throw("Company Tax ID setting is invalid. Should be GB followed by 9 digits.")
    return tax_id[2:]

def get_open_obligations(company):
    oauth = get_session(company)
    vrn = get_vrn(company)
    api_base = frappe.db.get_single_value("HMRC API Settings", "api_base")
    response = oauth.get(
        api_base+"/organisations/vat/%s/obligations?status=O" % vrn,
        headers=accept_header).json()
    if "obligations" not in response:
        frappe.throw("Message from HMRC: " + response["message"], 
                     "Error retrieving obligations")
    return response["obligations"]

def submit_return(company, vat_return):
    oauth = get_session(company)
    vrn = get_vrn(company)
    api_base = frappe.db.get_single_value("HMRC API Settings", "api_base")    
    response = oauth.post(api_base+"/organisations/vat/%s/returns" % vrn,
            headers = accept_header, json = vat_return)
    
    return response.json(), response.headers

