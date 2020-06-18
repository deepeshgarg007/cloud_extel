from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, add_months, add_days, flt, today, get_first_day, get_last_day, date_diff, rounded
from erpnext.accounts.utils import get_fiscal_year, get_account_currency
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import get_accounting_dimensions

def post_tds_gl_entries(payment_entry, method):
	for d in payment_entry.get("deductions"):
		gl_entries = []
		if payment_entry.party_type == 'Customer':
			account_fiscal_year_map = frappe._dict(frappe.get_all('TDS Accounts', fields=['fiscal_year', 'tds_account'],
				filters={'parent': payment_entry.company}, as_list=1))

			gross_tds_account = frappe.db.get_value('Company', payment_entry.company, 'gross_tds_account')
			booked_invoices = []

			for invoice in payment_entry.get('references'):
				if invoice.reference_name not in booked_invoices:
					doc = frappe.get_doc('Sales Invoice', invoice.reference_name)
					for item in doc.get('items'):
						service_start_date = getdate(item.start_date)
						service_end_date = getdate(item.end_date)

						if item.enable_deferred_revenue:
							no_of_months = (service_end_date.year - service_start_date.year) * 12 + \
								(service_end_date.month - service_start_date.month)

							for i in range(no_of_months):
								fiscal_year = get_fiscal_year(date=add_months(service_start_date, i))[0]

								tds_account = account_fiscal_year_map.get(fiscal_year)

								tds_amount_to_consider = d.amount * (item.amount /doc.net_total)

								amount = tds_amount_to_consider / no_of_months

								gl_entries.append(
									payment_entry.get_gl_dict({
										"account": tds_account,
										"against": payment_entry.party,
										"debit": amount,
										"debit_in_account_currency": amount,
										"cost_center": item.cost_center
									}, payment_entry.party_account_currency, item=item)
								)

								gl_entries.append(
									payment_entry.get_gl_dict({
										"account": d.account,
										"against": payment_entry.party,
										"credit": amount,
										"credit_in_account_currency": amount,
										"cost_center": item.cost_center
									}, payment_entry.party_account_currency, item=item)
								)
						else:
							amount = d.amount * (item.amount/doc.net_total)
							fiscal_year = get_fiscal_year(date=payment_entry.posting_date)[0]
							tds_account = account_fiscal_year_map.get(fiscal_year)

							gl_entries.append(
								payment_entry.get_gl_dict({
									"account": tds_account,
									"against": payment_entry.party,
									"debit": amount,
									"debit_in_account_currency": amount,
									"cost_center": item.cost_center
								}, payment_entry.party_account_currency, item=item)
							)

							gl_entries.append(
								payment_entry.get_gl_dict({
									"account": d.account,
									"against": payment_entry.party,
									"credit": amount,
									"credit_in_account_currency": amount,
									"cost_center": item.cost_center
								}, payment_entry.party_account_currency, item=item)
							)

					booked_invoices.append(invoice.reference_name)

					make_gl_entries(gl_entries)

def reverse_provision_entry(doc, method):
	gl_entries = []
	provision_account = frappe.db.get_value('Company', doc.company, 'provision_account')

	for item in doc.get('items'):
		gl_entries.append(doc.get_gl_dict({
			"account": provision_account,
			"against": doc.customer,
			"credit": item.base_net_amount,
			"credit_in_account_currency": item.base_net_amount,
			"cost_center": item.cost_center,
			"voucher_detail_no": item.name,
			"posting_date": doc.posting_date
		}, item=item))

		gl_entries.append(doc.get_gl_dict({
			"account": item.income_account,
			"against": doc.customer,
			"debit": item.base_net_amount,
			"debit_in_account_currency": item.base_net_amount,
			"cost_center": item.cost_center,
			"voucher_detail_no": item.name,
			"posting_date": doc.posting_date
		}, item=item))

	make_gl_entries(gl_entries, merge_entries=True)

def make_gl_entries_on_dn_submit(doc, method):
	gl_entries = []
	provision_account = frappe.db.get_value('Company', doc.company, 'provision_account')
	stock_items = doc.get_stock_items()

	for item in doc.get('items'):
		if item.item_code in stock_items:
			continue

		if item.get('deferred_revenue'):
			debit_account = item.deferred_revenue_account or frappe.db.get_value('Company', doc.company, 'default_deferred_income_account')
		else:
			debit_account = frappe.db.get_value('Item Default', {'company': doc.company}, 'income_account')

		gl_entries.append(doc.get_gl_dict({
			"account": debit_account,
			"against": doc.customer,
			"credit": item.base_net_amount,
			"credit_in_account_currency": item.base_net_amount,
			"cost_center": item.cost_center,
			"voucher_detail_no": item.name,
			"posting_date": doc.posting_date
		}, item=item))

		gl_entries.append(doc.get_gl_dict({
			"account": provision_account,
			"against": doc.customer,
			"debit": item.base_net_amount,
			"debit_in_account_currency": item.base_net_amount,
			"cost_center": item.cost_center,
			"voucher_detail_no": item.name,
			"posting_date": doc.posting_date
		}, item=item))

	make_gl_entries(gl_entries, merge_entries=True)


def post_delivery_note_entries(start_date=None, end_date=None):
	if not start_date:
		start_date = add_months(today(), -1)
	if not end_date:
		end_date = add_days(today(), -1)

	delivery_notes = frappe.db.sql_list('''
		select distinct item.parent
		from `tabDelivery Note Item` item, `tabDelivery Note` p
		where item.start_date<=%s and item.end_date>=%s
		and item.deferred_revenue = 1 and item.parent=p.name
		and item.docstatus = 1 and ifnull(item.amount, 0) > 0
	''', (end_date, start_date)) #nosec

	for delivery_note in delivery_notes:
		doc = frappe.get_doc("Delivery Note", delivery_note)
		book_deferred_income(doc, end_date)

def book_deferred_income(doc, posting_date=None):
	def _book_deferred_income(item):
		start_date, end_date, last_gl_entry = get_booking_dates(doc, item, posting_date=posting_date)
		print(start_date, end_date)
		if not (start_date and end_date): return

		deferred_account = item.deferred_revenue_account or frappe.db.get_value('Company', doc.company, 'default_deferred_income_account')
		income_account = frappe.db.get_value('Item Default', {'company': doc.company}, 'income_account')
		account_currency = get_account_currency(deferred_account)

		against, project = doc.customer, doc.project
		credit_account, debit_account = income_account, deferred_account

		total_days = date_diff(item.end_date, item.start_date) + 1
		total_booking_days = date_diff(end_date, start_date) + 1

		amount, base_amount = calculate_monthly_amount(doc, item, last_gl_entry,
			start_date, end_date, total_days, total_booking_days, account_currency)

		make_gl_entries_for_dn(doc, credit_account, debit_account, against,
			amount, base_amount, end_date, project, account_currency, item)

		# Returned in case of any errors because it tries to submit the same record again and again in case of errors

		if getdate(end_date) < getdate(posting_date) and not last_gl_entry:
			_book_deferred_income(item)

	for item in doc.get('items'):
		if item.get('deferred_revenue'):
			_book_deferred_income(item)

def get_booking_dates(doc, item, posting_date=None):
	if not posting_date:
		posting_date = add_days(today(), -1)

	last_gl_entry = False

	deferred_account = item.deferred_revenue_account or frappe.db.get_value('Company', doc.company, 'default_deferred_income_account')

	prev_gl_entry = frappe.db.sql('''
		select name, posting_date from `tabGL Entry` where company=%s and account=%s and
		voucher_type=%s and voucher_no=%s and voucher_detail_no=%s
		order by posting_date desc limit 1
	''', (doc.company, deferred_account, doc.doctype, doc.name, item.name), as_dict=True)

	if prev_gl_entry:
		start_date = getdate(add_days(prev_gl_entry[0].posting_date, 1))
	else:
		start_date = item.start_date

	end_date = get_last_day(start_date)
	if end_date >= item.end_date:
		end_date = item.end_date
		last_gl_entry = True
	# elif item.stop_date and end_date >= item.stop_date:
	# 	end_date = item.stop_date
	# 	last_gl_entry = True

	if end_date > getdate(posting_date):
		end_date = posting_date

	if getdate(start_date) <= getdate(end_date):
		return start_date, end_date, last_gl_entry
	else:
		return None, None, None

def calculate_monthly_amount(doc, item, last_gl_entry, start_date, end_date, total_days, total_booking_days, account_currency):
	amount, base_amount = 0, 0

	if not last_gl_entry:
		total_months = (item.end_date.year - item.start_date.year) * 12 + \
			(item.end_date.month - item.start_date.month) + 1

		prorate_factor = flt(date_diff(item.end_date, item.start_date)) \
			/ flt(date_diff(get_last_day(item.end_date), get_first_day(item.start_date)))

		actual_months = rounded(total_months * prorate_factor, 1)

		already_booked_amount, already_booked_amount_in_account_currency = get_already_booked_amount(doc, item)
		base_amount = flt(item.base_net_amount / actual_months, item.precision("base_net_amount"))

		if base_amount + already_booked_amount > item.base_net_amount:
			base_amount = item.base_net_amount - already_booked_amount

		if account_currency==doc.company_currency:
			amount = base_amount
		else:
			amount = flt(item.net_amount/actual_months, item.precision("net_amount"))
			if amount + already_booked_amount_in_account_currency > item.net_amount:
				amount = item.net_amount - already_booked_amount_in_account_currency

		if not (get_first_day(start_date) == start_date and get_last_day(end_date) == end_date):
			partial_month = flt(date_diff(end_date, start_date)) \
				/ flt(date_diff(get_last_day(end_date), get_first_day(start_date)))

			base_amount = rounded(partial_month, 1) * base_amount
			amount = rounded(partial_month, 1) * amount
	else:
		already_booked_amount, already_booked_amount_in_account_currency = get_already_booked_amount(doc, item)
		base_amount = flt(item.base_net_amount - already_booked_amount, item.precision("base_net_amount"))
		if account_currency==doc.company_currency:
			amount = base_amount
		else:
			amount = flt(item.net_amount - already_booked_amount_in_account_currency, item.precision("net_amount"))

	return amount, base_amount

def get_already_booked_amount(doc, item):
	total_credit_debit, total_credit_debit_currency = "debit", "debit_in_account_currency"

	gl_entries_details = frappe.db.sql('''
		select sum({0}) as total_credit, sum({1}) as total_credit_in_account_currency, voucher_detail_no
		from `tabGL Entry` where company=%s and account=%s and voucher_type=%s and voucher_no=%s and voucher_detail_no=%s
		group by voucher_detail_no
	'''.format(total_credit_debit, total_credit_debit_currency),
		(doc.company, item.get('deferred_revenue_account'), doc.doctype, doc.name, item.name), as_dict=True)

	already_booked_amount = gl_entries_details[0].total_credit if gl_entries_details else 0

	if doc.currency == doc.company_currency:
		already_booked_amount_in_account_currency = already_booked_amount
	else:
		already_booked_amount_in_account_currency = gl_entries_details[0].total_credit_in_account_currency if gl_entries_details else 0

	return already_booked_amount, already_booked_amount_in_account_currency

def make_gl_entries_for_dn(doc, credit_account, debit_account, against,
	amount, base_amount, posting_date, project, account_currency, item):

	print(credit_account, debit_account)

	if amount == 0: return

	gl_entries = []
	gl_entries.append(
		doc.get_gl_dict({
			"account": credit_account,
			"against": against,
			"credit": base_amount,
			"credit_in_account_currency": amount,
			"cost_center": item.cost_center,
			"voucher_detail_no": item.name,
			'posting_date': posting_date,
			'project': project
		}, account_currency, item=item)
	)

	# GL Entry to debit the amount from the expense
	gl_entries.append(
		doc.get_gl_dict({
			"account": debit_account,
			"against": against,
			"debit": base_amount,
			"debit_in_account_currency": amount,
			"cost_center": item.cost_center,
			"voucher_detail_no": item.name,
			'posting_date': posting_date,
			'project': project
		}, account_currency, item=item)
	)

	if gl_entries:
		try:
			make_gl_entries(gl_entries, cancel=(doc.docstatus == 2), merge_entries=True)
			frappe.db.commit()
		except:
			frappe.db.rollback()
			traceback = frappe.get_traceback()
			frappe.log_error(message=traceback)

			frappe.flags.deferred_accounting_error = True
