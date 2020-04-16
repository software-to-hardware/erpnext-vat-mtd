# -*- coding: utf-8 -*-
# Copyright (c) 2020 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import get_request_site_address
import requests_oauthlib as ro
import datetime
import json

class HMRCAuthorisations(Document):
	pass

def get_redirect_uri():
	return get_request_site_address(True) + "?cmd=erpnext.regional.doctype.hmrc_authorisations.hmrc_authorisations.hmrc_callback"

@frappe.whitelist()
def authorize_access(name):

	client_id = frappe.db.get_single_value("HMRC API Settings", "client_id")
	client_secret = frappe.db.get_single_value("HMRC API Settings", "client_secret")
	auth_base = frappe.db.get_single_value("HMRC API Settings", "auth_base")

	# Generate authorisation request
	scope = ["read:vat", "write:vat"] # TODO: hard coded VAT request
	oauth = ro.OAuth2Session(client_id, redirect_uri=get_redirect_uri(),
							 scope=scope)
	authorization_url, state = oauth.authorization_url(auth_base+'/oauth/authorize')

	# Save state so we can match callback to this record
	frappe.db.set_value("HMRC Authorisations", name, "authorisation_status", "In progress")
	frappe.db.set_value("HMRC Authorisations", name, "oauth_state", state)
	frappe.db.commit()

	return { "url": authorization_url }

@frappe.whitelist()
def hmrc_callback(code=None, state=None,
                  error=None, error_description=None, error_code=None):

	# Retrieve authorisation document from state
	name = frappe.db.sql("""
				select name from `tabHMRC Authorisations` a
				where a.oauth_state = %s""", state)[0][0]

	if error:
		frappe.db.set_value("HMRC Authorisations", name, "oauth_refresh_token",
							None)
		frappe.db.set_value("HMRC Authorisations", name, "authorisation_status",
							"Authorisation failed")
		frappe.db.set_value("HMRC Authorisations", name, "authorised_services",
							None)
		frappe.db.set_value("HMRC Authorisations", name, "last_authorised_date",
							None)
		frappe.db.commit()
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/desk#Form/HMRC Authorisations/{0}".format(name)
		frappe.msgprint("HMRC authorisation was NOT successful. %s" % error_description)
		return

	client_id = frappe.db.get_single_value("HMRC API Settings", "client_id")
	client_secret = frappe.db.get_single_value("HMRC API Settings", "client_secret")
	api_base = frappe.db.get_single_value("HMRC API Settings", "api_base")

	scope = ["read:vat", "write:vat"] # TODO: hard coded VAT request
	oauth = ro.OAuth2Session(client_id, redirect_uri=get_redirect_uri())

	token = oauth.fetch_token(
			api_base+'/oauth/token',
			authorization_response = "https://doesntmatter/?code=%s" % code,
			client_id=client_id,
			client_secret = client_secret,
			include_client_id=True)

	frappe.db.set_value("HMRC Authorisations", name, "oauth_token", json.dumps(token))
	frappe.db.set_value("HMRC Authorisations", name, "authorisation_status", 
					        "Authorised")
	frappe.db.set_value("HMRC Authorisations", name, "authorised_services", 
					        " ".join(token["scope"]))
	frappe.db.set_value("HMRC Authorisations", name, "last_authorised_date", 
					    datetime.datetime.now())
	frappe.db.commit()

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/desk#Form/HMRC Authorisations/{0}".format(name)
	frappe.msgprint("HMRC authorisation successful!")

def get_session(company):

	name, token_string = frappe.db.sql("""
				select name, oauth_token from `tabHMRC Authorisations` a
				where 
					a.company = %s and
					a.authorisation_status = "Authorised"
				""", company)[0]
	token = json.loads(token_string)

	client_id = frappe.db.get_single_value("HMRC API Settings", "client_id")
	client_secret = frappe.db.get_single_value("HMRC API Settings", "client_secret")
	api_base = frappe.db.get_single_value("HMRC API Settings", "api_base")
	auth_base = frappe.db.get_single_value("HMRC API Settings", "auth_base")
	extra = {
		'client_id': client_id,
		'client_secret': client_secret,
	}

	def token_updater(token):
		frappe.db.set_value("HMRC Authorisations", name, "oauth_token",
			json.dumps(token))
		frappe.db.commit()

	return ro.OAuth2Session(client_id,
						token=token,
						auto_refresh_kwargs=extra,
						auto_refresh_url=api_base+'/oauth/token',
						token_updater=token_updater)
