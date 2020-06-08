# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from cloud_extel.cloud_extel.deferred_tds import post_grn_entries

class ProcessGRNEntries(Document):
	def on_submit(self):
		post_grn_entries(posting_date=self.posting_date)
