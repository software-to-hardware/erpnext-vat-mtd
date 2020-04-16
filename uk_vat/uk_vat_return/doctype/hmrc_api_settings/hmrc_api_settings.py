# -*- coding: utf-8 -*-
# Copyright (c) 2020 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import uuid

import requests_oauthlib as ro
from oauthlib.oauth2 import BackendApplicationClient 

class HMRCAPISettings(Document):

	def before_save(self):

		# Generate installation guid for HMRC API
		if self.installation_guid is None or len(self.installation_guid) < 5:
			self.installation_guid = str(uuid.uuid4())

@frappe.whitelist()
def test_api(name):

	client_id = frappe.db.get_single_value("HMRC API Settings", "client_id")
	client_secret = frappe.db.get_single_value("HMRC API Settings", "client_secret")
	api_base = frappe.db.get_single_value("HMRC API Settings", "api_base")

	# Attempt to get a backend token with the supplied client secret. If this
	# is successful, the secrets are probably good.
	client = BackendApplicationClient(client_id=client_id)
	oauth = ro.OAuth2Session(client=client)
	token = oauth.fetch_token(
		token_url=api_base+'/oauth/token',
		client_id=client_id,
		client_secret=client_secret,
		include_client_id=True)

	return "Success"
