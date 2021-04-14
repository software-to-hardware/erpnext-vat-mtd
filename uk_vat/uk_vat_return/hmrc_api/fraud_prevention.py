# -*- coding: utf-8 -*-
# Copyright (c) 2021 Software to Hardware Ltd. and contributors
# For license information, please see license.txt

import platform
import hashlib
import frappe
import urllib.parse
from datetime import datetime, timezone
import uuid
import json

DEVICE_ID_COOKIE = "Gov-Client-Device-ID"

def get_fraud_prevention_headers():

    utc_now = datetime.now(timezone.utc).isoformat()[0:23] + "Z"

    h = {}
    h["Gov-Client-Connection-Method"] = "WEB_APP_VIA_SERVER"
    h["Gov-Client-Browser-Do-Not-Track"] = str(
        bool(frappe.request.headers.get("DNT"))).lower()
    h["Gov-Vendor-License-IDs"] = "{}={}".format(
        "ERPNext", hashlib.sha256(b"OPEN SOURCE").hexdigest())
    h["Gov-Vendor-Product-Name"] = "ERPNext-MTD-VAT-Module"
    h["Gov-Vendor-Version"] = "erpnext-mtd-module=1.0&{}={}".format(
        platform.system(), platform.release()
    )

    # Get or generate and store client device ID
    client_device_id = frappe.request.cookies.get(DEVICE_ID_COOKIE)
    if not client_device_id:
        client_device_id = str(uuid.uuid4())
        frappe.local.cookie_manager.set_cookie(DEVICE_ID_COOKIE,
            client_device_id)
    h["Gov-Client-Device-ID"] = client_device_id

    # Client address
    # In production this should come from your proxy front end
    if frappe.db.get_single_value("HMRC API Settings", "gov_ip_headers"):
        for hdr in ("Gov-Client-Public-IP", "Gov-Client-Public-IP-Timestamp",
                    "Gov-Client-Public-Port", "Gov-Vendor-Public-IP",
                    "Gov-Vendor-Forwarded"):
            h[hdr] = frappe.get_request_header(hdr)
    else:
        h["Gov-Client-Public-IP"] = frappe.request.remote_addr
        h["Gov-Client-Public-IP-Timestamp"] = utc_now
        h["Gov-Client-Public-Port"] = ""
        h["Gov-Vendor-Forwarded"] = ""
        h["Gov-Vendor-Public-IP"] = ""

    # Headers from this application
    h["Gov-Client-User-IDs"] = "frappe={}".format(
        urllib.parse.quote(frappe.session.user))

    # Headers from client javascript
    chdr = json.loads(frappe.request.form["fraud_prevention"])
    h["Gov-Client-Browser-JS-User-Agent"] = chdr.get("UA")
    tzoffset_minutes = chdr.get("TimezoneOffsetMinutes")
    if tzoffset_minutes is not None:
        tzoffset_minutes = int(tzoffset_minutes)
        h["Gov-Client-Timezone"] = "UTC{}{:02d}:{:02d}".format(
            "-" if tzoffset_minutes >= 0 else "+", # Direction is ok
            abs(tzoffset_minutes) // 60,
            abs(tzoffset_minutes) % 60
        )
    h["Gov-Client-Window-Size"] = "width={}&height={}".format(
        chdr["WindowWidth"], chdr["WindowHeight"]
    )
    h["Gov-Client-Screens"] = "width={}&height={}&scaling-factor={}&colour-depth={}".format(
        chdr["ScreenWidth"], chdr["ScreenHeight"], chdr["ScreenScalingFactor"],
        chdr["ScreenColorDepth"]
    )

    h["Gov-Client-Browser-Plugins"] = chdr["Plugins"]

    # Suggested method does not work. If GOV wants these then GOV can tell us
    # how they want us to get them.
    h["Gov-Client-Local-IPs"] = ""
    h["Gov-Client-Local-IPs-Timestamp"] = ""

    # We don't use multi-factor.
    h["Gov-Client-Multi-Factor"] = ""

    return h

@frappe.whitelist()
def http_header_feedback():
    return frappe.request.headers

