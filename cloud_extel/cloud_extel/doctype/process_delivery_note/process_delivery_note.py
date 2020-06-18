# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from cloud_extel.cloud_extel.deferred_tds import post_delivery_note_entries

class ProcessDeliveryNote(Document):
	def on_submit(self):
		post_delivery_note_entries(self.start_date, self.end_date)

