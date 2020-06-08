# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "cloud_extel"
app_title = "Cloud Extel"
app_publisher = "Frappe"
app_description = "Custom App for business specific customizations"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "test@example.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/cloud_extel/css/cloud_extel.css"
# app_include_js = "/assets/cloud_extel/js/cloud_extel.js"

# include js, css files in header of web template
# web_include_css = "/assets/cloud_extel/css/cloud_extel.css"
# web_include_js = "/assets/cloud_extel/js/cloud_extel.js"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "cloud_extel.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "cloud_extel.install.before_install"
# after_install = "cloud_extel.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "cloud_extel.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Payment Entry": {
		"on_submit": "cloud_extel.cloud_extel.deferred_tds.post_tds_gl_entries",
	},
	"Purchase Invoice": {
		"on_submit": "cloud_extel.cloud_extel.deferred_tds.validate_purchase_invoice",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"cloud_extel.tasks.all"
	# ],
	# "daily": [
	# 	"cloud_extel.tasks.daily"
	# ],
	# "hourly": [
	# 	"cloud_extel.tasks.hourly"
	# ],
	# "weekly": [
	# 	"cloud_extel.tasks.weekly"
	# ]
	"monthly": [
		"cloud_extel.cloud_extel.deferred_tds.post_grn_entries"
	]
}

# Testing
# -------

# before_tests = "cloud_extel.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "cloud_extel.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "cloud_extel.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

fixtures = [
	{
		"dt": "DocType",
		"filters": [["name", "in", [
			"TDS Accounts",
			"Telecom Circle",
			"City",
			"Zone",
			"Telecom Region",
			"Allowed Revenue Accounts Detail",
			"Allowed Revenue Account"
		]]]
	},
	{
		"dt": "Custom Field",
		"filters": [["name", "in", [
			"Company-tds_settings",
			"Company-accounts",
			"Company-gross_tds_account",
			"Address-cost_center",
			"Address-telecom_circle",
			"Address-telecom_region",
			"Company-provision_account",
			"Purchase Receipt Item-months",
			"Purchase Receipt Item-site",
			"Purchase Order Item-site",
			"Purchase Order Item-months",
			"Purchase Order-purchase_order_type"
		]]]
	},
	{
		"dt": "Custom Script",
		"filters": [["name", "in", [
			"Company-Client",
			"Sales Invoice-Client",
			"Purchase Order-Client"
		]]]
	},
	{
		"dt": "Server Script",
		"filters": [["name", "in", [
			"Income Account Query"
		]]]
	}
]

