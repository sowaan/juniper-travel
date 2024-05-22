# Copyright (c) 2023, Sowaan and contributors
# For license information, please see license.txt

import json, xmltodict
import frappe
from frappe import _
import requests
from frappe.model.document import Document
from frappe.utils.data import getdate
from frappe.utils import flt, now, add_to_date
from datetime import datetime, timedelta


class JuniperSite(Document):
	def before_save(self):
		pass


def get_juniper_site_list():
	sites = frappe.get_all("Juniper Site", fields=['*'])

	if not sites:
		frappe.throw(_("No Juniper sites found. Please create at least one site and try again"))

	return sites

@frappe.whitelist()
def sync_customer_with_scheduler():
	junier_sites = get_juniper_site_list()
	from_date = now() - timedelta(days=30)
	to_date = now()
	for doc in junier_sites:
		sync_customer(doc, from_date, to_date)

@frappe.whitelist()
def sync_supplier_with_scheduler():
	junier_sites = get_juniper_site_list()
	from_date = now() - timedelta(days=30)
	to_date = now()
	for doc in junier_sites:
		sync_supplier(doc, from_date, to_date)

@frappe.whitelist()
def sync_sales_order_with_scheduler():
	junier_sites = get_juniper_site_list()
	from_date = now() - timedelta(days=30)
	to_date = now()
	for doc in junier_sites:
		sync_sales_order(doc, from_date, to_date)

@frappe.whitelist()
def sync_sales_invoice_with_scheduler():
	junier_sites = get_juniper_site_list()
	from_date = now() - timedelta(days=30)
	to_date = now()
	for doc in junier_sites:
		sync_sales_invoice(doc, from_date, to_date)


@frappe.whitelist()
def sync_customer(doc, from_date, to_date):
	doc = json.loads(doc)
	from_date = doc.get("from_date")
	to_date = doc.get("to_date")
	soap_action = doc.get('cus_soap_action')
	user = str(doc.get('user_name'))
	password = str(doc.get('password'))

	url = doc.get('base_url') + doc.get('cus_end_point')
	from_date = getdate(from_date).strftime("%Y%m%d") if from_date else ''
	to_date = getdate(from_date).strftime("%Y%m%d") if to_date else ''
	# structured XML
	payload = f"""<?xml version="1.0" encoding="utf-8"?>
	<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
	<soap:Body>
		<getCustomerList xmlns="http://juniper.es/">
			<user>{user}</user>
			<password>{password}</password>
			<creationDateFrom>{from_date}</creationDateFrom>
      		<creationDateTo>{to_date}</creationDateTo>
		</getCustomerList>
	</soap:Body>
	</soap:Envelope>"""
	headers = {
		'SOAPAction': soap_action,
		'Content-Type': 'text/xml; charset=utf-8'
	}

	try:
		res = requests.request("POST", url, headers=headers, data=payload)
	except requests.exceptions.HTTPError:
		button_label = frappe.bold(_("Get Access Token"))
		frappe.throw(
			(
				"Something went wrong during the people sync. Click on {0} to generate a new one."
			).format(button_label)
		)
	obj = xmltodict.parse(res.text, process_namespaces=False)
	jsonvalue = json.dumps(obj)
	value = json.loads(jsonvalue)
	response = value.get("soap:Envelope").get("soap:Body").get("getCustomerListResponse").get("getCustomerListResult").get("wsResult")
	cus_list = response.get("Customers").get("Customer") if response.get("Customers") else response.get("Customers")
	
	if cus_list:
		for cus in cus_list:
			set_customer(cus)


@frappe.whitelist()
def sync_supplier(doc):
	doc = json.loads(doc)
	from_date = doc.get("sup_from_date")
	to_date = doc.get("sup_to_date")
	soap_action = doc.get('sup_soap_action')
	user = str(doc.get('user_name'))
	password = str(doc.get('password'))

	url = doc.get('base_url') + doc.get('sup_endpoint')
	sup_from_date = getdate(from_date).strftime("%Y%m%d") if from_date else ''
	sup_to_date = getdate(to_date).strftime("%Y%m%d") if to_date else ''
 
	# structured XML
	payload = f"""<?xml version="1.0" encoding="utf-8"?>
	<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
	<soap:Body>
		<getSupplierList xmlns="http://juniper.es/">
			<user>{user}</user>
			<password>{password}</password>
			<creationDateFrom>{sup_from_date}</creationDateFrom>
      		<creationDateTo>{sup_to_date}</creationDateTo>
		</getSupplierList>
	</soap:Body>
	</soap:Envelope>"""
	headers = {
		'SOAPAction': soap_action,
		'Content-Type': 'text/xml; charset=utf-8'
	}

	try:
		res = requests.request("POST", url, headers=headers, data=payload)
	except requests.exceptions.HTTPError:
		button_label = frappe.bold(_("Get Access Token"))
		frappe.throw(
			(
				"Something went wrong during the people sync. Click on {0} to generate a new one."
			).format(button_label)
		)
	obj = xmltodict.parse(res.text, process_namespaces=False)
	jsonvalue = json.dumps(obj)
	value = json.loads(jsonvalue)
	sup_list = value.get("soap:Envelope").get("soap:Body").get("getSupplierListResponse").get("getSupplierListResult").get("wsResult").get("Suppliers").get("Supplier")
	# print(sup_list, "check")
	# print(cus_list[0].get("General").get("CustomerGroup") , "check")
	for sup in sup_list:
		set_supplier(sup)


@frappe.whitelist()
def sync_sales_order(doc):
	doc = json.loads(doc)
	sales_from_date = doc.get("sales_from_date")
	sale_to_date = doc.get("sale_to_date")
	soap_action = doc.get('sale_soap_action')
	user = str(doc.get('user_name'))
	password = str(doc.get('password'))

	url = doc.get('base_url') + doc.get('sale_endpoint')
	sale_from_date = getdate(sales_from_date).strftime("%Y%m%d") if sales_from_date else ''
	sale_to_date = getdate(sale_to_date).strftime("%Y%m%d") if sale_to_date else ''
	booking_code = doc.get('booking_code') if doc.get('booking_code') else ''
 
	# structured XML
	payload = f"""<?xml version="1.0" encoding="utf-8"?>
		<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
		<soap:Body>
			<getBookings xmlns="http://juniper.es/">
			<user>{user}</user>
			<password>{password}</password>
			<BookingDateFrom>{sale_from_date}</BookingDateFrom>
      		<BookingDateTo>{sale_to_date}</BookingDateTo>
			<BookingCode>{booking_code}</BookingCode>
			</getBookings>
		</soap:Body>
		</soap:Envelope>"""
	headers = {
		'SOAPAction': soap_action,
		'Content-Type': 'text/xml; charset=utf-8'
	}

	try:
		res = requests.request("POST", url, headers=headers, data=payload)
	except requests.exceptions.HTTPError:
		button_label = frappe.bold(_("Get Access Token"))
		frappe.throw(
			(
				"Something went wrong during the people sync. Click on {0} to generate a new one."
			).format(button_label)
		)
	obj = xmltodict.parse(res.text, process_namespaces=False)
	jsonvalue = json.dumps(obj)
	value = json.loads(jsonvalue)
	order_list = value.get("soap:Envelope").get("soap:Body").get("getBookingsResponse").get("getBookingsResult").get("wsResult").get("Bookings").get("Booking")
	# print(order_list, "Order List Check \n\n\n")
	if isinstance(order_list, dict):
		order_list = [order_list]
	for order in order_list:
		if order.get("@Status") == "OK":
			set_booking(order)


@frappe.whitelist()
def sync_sales_invoice(doc):
	doc = json.loads(doc)
	invoice_from_date = doc.get("invoice_from_date")
	invoice_to_date = doc.get("invoice_to_date")
	soap_action = doc.get('invoice_soap_action')
	user = str(doc.get('user_name'))
	password = str(doc.get('password'))

	url = doc.get('base_url') + doc.get('invoice_endpoint')
	invoice_number = doc.get('invoice_number')
	invoice_id = doc.get('invoice_id')
	from_date = getdate(invoice_from_date).strftime("%Y%m%d") if invoice_from_date else ''
	to_date = getdate(invoice_to_date).strftime("%Y%m%d") if invoice_to_date else ''
	# structured XML
	payload = f"""<?xml version="1.0" encoding="utf-8"?>
		<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
		<soap:Body>
			<GetInvoices xmlns="http://juniper.es/">
				<user>{user}</user>
				<password>{password}</password>
				<InvoiceNumber>{invoice_number}</InvoiceNumber>
				<IdInvoice>{invoice_id}</IdInvoice>
				<InvoiceDateFrom>{from_date}</InvoiceDateFrom>
				<InvoiceDateTo>{to_date}</InvoiceDateTo>
			</GetInvoices>
		</soap:Body>
		</soap:Envelope>"""
	headers = {
		'SOAPAction': soap_action,
		'Content-Type': 'text/xml; charset=utf-8'
	}
	print(url, headers, payload, "Check Headers payload \n\n\n\n\n")
	try:
		res = requests.request("POST", url, headers=headers, data=payload)
	except requests.exceptions.HTTPError:
		button_label = frappe.bold(_("Get Access Token"))
		frappe.throw(
			(
				"Something went wrong during the people sync. Click on {0} to generate a new one."
			).format(button_label)
		)
	obj = xmltodict.parse(res.text, process_namespaces=False)
	jsonvalue = json.dumps(obj)
	value = json.loads(jsonvalue)
	print(value, "Check \n\n\n\n\n")
	invoice = value.get("soap:Envelope").get("soap:Body").get("GetInvoicesResponse").get("GetInvoicesResult").get("wsResult").get("Invoices").get("Invoice")
	# order_list = value.get("soap:Envelope").get("soap:Body").get("getBookingsResponse").get("getBookingsResult").get("wsResult").get("Bookings").get("Booking")
	# set_booking(order_list)
	for inv in invoice:
		# if float(inv.get("@TotalInvoiceAmount")) > 0:
		set_sales_invoice(inv, doc)


def set_customer(customer):
	gen = customer.get("General")
	cont = customer.get("Contact")
	cust_doc = {}
	customerGroup = {}
	print(gen.get("Name"), gen.get("CustomerGroup"), "Checnking Customer")
	if gen.get("CustomerGroup"):
		customerGroupName = frappe.db.exists("Customer Group", {"customer_group_name": gen.get("CustomerGroup").get("#text")})
		if not customerGroupName:
			cus_group = frappe.get_doc({
				"doctype": "Customer Group",
				"customer_group_name": gen.get("CustomerGroup").get("#text")
			})
			cus_group.save()
			customerGroup = cus_group
		else:
			customerGroup = frappe.get_doc("Customer Group", customerGroupName)
	customerName = frappe.db.exists("Customer", {"custom_customer_id": customer.get("@Id")})
	if not customerName:
		cust_doc = frappe.get_doc({
			"doctype": "Customer",
			"custom_customer_id": customer.get("@Id"),
			"customer_name": gen.get("Name") if gen.get("Name") else "Name is not available",
		})
		cust_doc.customer_group = customerGroup.name if gen.get("CustomerGroup") else "Juniper"
		if cont:
			cust_doc.custom_address = f""""address_title": {cont.get("AddressNumber")}, \n "address_line1": {cont.get("Address")}, \n "city": {cont.get("City").get("#text")}, \n "county": {cont.get("Country")}, \n "pincode": {cont.get("@ZIP")}, \n "email_id": {cont.get("Email")}, \n "phone": {cont.get("Phone1")}, \n "fax": {cont.get("Fax")}"""
			cust_doc.custom_contact = f""""first_name": {cont.get("ContactName")},\n "company_name": {cont.get("CompanyName")}"""
			cust_doc.save()

			
			# address = frappe.get_doc({
			# 	"doctype": "Address",
				
			# })
			# address.append("links", {
			# 		"link_doctype": "Customer",
			# 		"link_name": cust_doc.name
			# 	})
			# address.save()
			# contact = frappe.get_doc({
			# 	"doctype": "Contact",
				
			# })
			# contact.append("links", {
			# 		"link_doctype": "Customer",
			# 		"link_name": cust_doc.name
			# 	})
			# contact.save()
		return cust_doc
	else:
		return frappe.get_doc("Customer", customerName)


def set_supplier(supplier, zone=None):
	supplierName = supplier.get("Name") or supplier.get("SupplierName")
	country = zone.get("country", "") if zone else ''
	# if supplier.get("SupplierGroup"):
	# 	if supplier.get("SupplierGroup").get("#text"):
	# 		sup_group = frappe.get_doc({
	# 			"doctype": "Supplier Group",
	# 			"supplier_group_name": supplier.get("SupplierGroup").get("#text")
	# 		})
	# 		sup_group.save()
	supplierListName = frappe.db.exists("Supplier", {"supplier_name": supplierName})
	print(supplierName, country, supplierListName, "supplierName \n\n\n\n")
	if not supplierListName:
		sup_doc = frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": supplierName,
			"country": country
		})

		# if supplier.get("SupplierGroup"):
		# 	if supplier.get("SupplierGroup").get("#text"):
		# 		sup_doc.supplier_group = supplier.get("SupplierGroup").get("#text")
		sup_doc.insert(ignore_permissions=True)
		return sup_doc
	else:
		return frappe.get_doc("Supplier", supplierListName)

		
	# if cont:
	# 	address = frappe.get_doc({
	# 		"doctype": "Address",
	# 		"address_title": cont.get("AddressNumber"),
	# 		"address_line1": cont.get("Address"),
	# 		"city": cont.get("City").get("#text"),
	# 		"county": cont.get("Country"),
	# 		"pincode": cont.get("@ZIP"),
	# 		"email_id": cont.get("Email"),
	# 		"phone": cont.get("Phone1"),
	# 		"fax": cont.get("Fax")
	# 	})
	# 	address.append("links", {
	# 			"link_doctype": "Customer",
	# 			"link_name": customer.name
	# 		})
	# 	address.save()
	# 	contact = frappe.get_doc({
	# 		"doctype": "Contact",
	# 		"first_name": cont.get("ContactName"),
	# 		"company_name": cont.get("CompanyName"),
	# 		"address": address.name,
	# 	})
	# 	contact.append("links", {
	# 			"link_doctype": "Customer",
	# 			"link_name": customer.name
	# 		})
	# 	contact.save()


def set_booking(order):
	line = order.get("Lines").get("Line") if order.get("Lines") else order.get("Lines")
	if isinstance(line, dict):
		line = [line]
		
	if isinstance(line, list):
		sales_order = set_sales_order(order, line)
		set_purchase_invoice(line, sales_order)


def set_sales_order(order, line):
	item = {}
	customer = order.get("Customer")
	invoice_customer = order_customer(customer)
	default_session = frappe.defaults.get_defaults()
	taxes_and_charges = get_default_tax_template()
	# Get default company from the session
	default_company = default_session.get("company")
	salesOrderName = frappe.db.exists("Sales Order", {"custom_sales_order_code": order.get("@BookingCode")})
	if not salesOrderName:
		so = frappe.get_doc({
			"doctype": "Sales Order",
			"company": default_company,
			"customer": invoice_customer.name,
			"custom_sales_order_id": order.get("@Id"),
			"transaction_date": order.get("@BookingDate"),
			"delivery_date": order.get("@BookingDate"),
			"currency": line[0].get("SellCurrency"),
			"custom_sales_order_code": order.get("@BookingCode")
		})
		for li in line:
			paxes = li.get("Paxes").get("Pax")
			if isinstance(paxes, dict):
				paxes = [paxes]
			item = order_item(li)
			sell_rate_condition = li.get("Zone").get("country") == "Saudi Arabia"
			item_tax = flt(li.get("SellingPrice")) * (15 / 100) if sell_rate_condition else 0
			so.append("items", {
				"item_code": item.item_code,
				"item_name": item.item_name,
				"rate": flt(li.get("SellingPrice")) - item_tax,
				"qty": 1
			})

			if isinstance(paxes, list):
				for pax in paxes:
					so.append("custom_passenger", {
						"pax_id": pax.get("@Id"),
						"name1": pax.get("Name"),
						"surname": pax.get("LastName"),
					})

			if item_tax > 0:
				for tax in taxes_and_charges.taxes:
					so.append("taxes", {
						"charge_type": tax.charge_type,
						"account_head": tax.account_head,
						"description": tax.description,
						"tax_amount": item_tax
					})

		so.set_missing_values()
		so.insert(ignore_permissions=True)
		return so
	else:
		return frappe.get_doc("Sales Order", salesOrderName)

def set_purchase_invoice(line, order):
	default_session = frappe.defaults.get_defaults()
	taxes_and_charges = get_default_tax_template()
	# Get default company from the session
	default_company = default_session.get("company")
	for li in line:
		taxes = li.get("CostTaxes").get("Tax")
		paxes = li.get("Paxes").get("Pax")
		if isinstance(paxes, dict):
			paxes = [paxes]

		if isinstance(taxes, dict):
			taxes = [taxes]

		item = {
			"@ProductId": li.get("Productid"),
			"#text": li.get("ServiceName")
		}
		group = {
			"@ProductGroupName": li.get("ProductGroupName"),
			"@ProductGroup": li.get("ProductGroup")
		}
		supplier = set_supplier(li.get("Supplier"), li.get("Zone"))
		item_data = invoice_item(item, group) 
		prInvoiceName = frappe.db.exists("Purchase Invoice", [["Purchase Invoice Item","custom_id_booking_line","=", li.get("@IdBookLine")]])
		if not prInvoiceName:
			pr_invoice = frappe.get_doc({
				"doctype": "Purchase Invoice",
				"supplier": supplier.name,
				"set_posting_time": 1,
				# "custom_booking_date": getdate(order.transaction_date),
				"posting_date": getdate(li.get("BeginTravelDate")),
				"currency": li.get("CostCurrency"),
				"company": default_company,
				"custom_sales_order": order.name
			})
			
			pr_invoice.append("items", {
				"item_code": item_data.name,
				'qty': 1,
				"rate": flt(li.get("CostBaseLine")) - (flt(li.get("CostBaseLine")) * (15/100)) if li.get("Zone").get("country") == "Saudi Arabia" else flt(li.get("CostBaseLine")),
				"custom_booking_code": order.custom_sales_order_code,
				"custom_agency_reference": li.get("@AgencyReference"),
				"custom_item_date": li.get("@LineDate"),
				"custom_id_booking_line": li.get("@IdBookLine"),
				"custom_booking_date": li.get("@BookingDate"),
				"custom_pax_number": li.get("PaxNumber"),
				"custom_begin_travel_date": li.get("BeginTravelDate"),
				"custom_end_travel_date":li.get("EndTravelDate")
			})

			if isinstance(paxes, list):
				for pax in paxes:
					pr_invoice.append("custom_passenger", {
						"pax_id": pax.get("@Id"),
						"name1": pax.get("Name"),
						"surname": pax.get("LastName"),
					})

			if isinstance(taxes, list):
				if li.get("Zone").get("country") == "Saudi Arabia":
					for pr_tax in taxes:
						for tax in taxes_and_charges.taxes:
							pr_invoice.append("taxes", {
								"charge_type": tax.charge_type,
								"account_head": tax.account_head,
								"description": tax.description,
								"tax_amount": flt(li.get("CostBaseLine")) * (15/100)
							})

			pr_invoice.set_missing_values()
			pr_invoice.insert(ignore_permissions=True)
		else:
			return frappe.get_doc("Purchase Invoice", prInvoiceName)



def set_sales_invoice(invoice, doc):
	default_session = frappe.defaults.get_defaults()

	# Get default company from the session
	default_company = default_session.get("company")
	customer = invoice.get("Customer")
	customer['Name'] = customer.get("CustomerName")
	lines = invoice.get("Lines").get("Line")
	taxes = invoice.get("taxes")
	paxes = invoice.get("PassengerList").get("Passenger") if invoice.get("PassengerList") else invoice.get("PassengerList")
	invoice_customer = order_customer(customer)
	taxes_and_charges = get_default_tax_template()
	if not frappe.db.exists("Sales Invoice", {"custom_invoice_id": invoice.get("@IdInvoice")}):
		if getdate(invoice.get("@DueDate")) >= getdate(invoice.get("@InvoiceDate")):
			si = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": invoice_customer.name,
				"custom_invoice_id": invoice.get("@IdInvoice"),
				"set_posting_time": 1,
				"posting_date": invoice.get("@InvoiceDate"),
				"due_date": invoice.get("@DueDate"),
				"currency": invoice.get("@Currency"),
				"custom_invoice_number": invoice.get("@InvoiceNumber"),
				"custom_invoice_series": invoice.get("@InvoiceSeries"),
				"company": default_company,
			})
			if taxes:
				taxes = taxes.get("tax")
				si.taxes_and_charges = taxes_and_charges.name
			if invoice.get("@CreditInvoice") == "yes":
				si.is_return = 1

			if isinstance(lines, dict):
				lines = [lines]

			if isinstance(paxes, dict):
				paxes = [paxes]

			if isinstance(taxes, dict):
				taxes = [taxes]
			
			if isinstance(lines, list):
				for li in lines:
					item = invoice_item(li.get("Service"), li)
					si.append("items", {
						"item_code": item.item_code,
						"item_name": item.item_name,
						"rate": li.get("@BaseLineAmount"),
						"qty": -1 if invoice.get("@CreditInvoice") == "yes" else 1,
						"custom_booking_code": li.get("@BookingCode"),
						"custom_agency_reference": li.get("@AgencyReference"),
						"custom_item_date": li.get("@LineDate"),
						"custom_id_booking_line": li.get("@IdBookingLine"),
						"custom_booking_date": li.get("@BookingDate"),
						"custom_pax_number": li.get("@PaxNumber"),
						"custom_begin_travel_date": li.get("@BeginTravelDate"),
						"custom_end_travel_date":li.get("@EndTravelDate")
					})

			if isinstance(paxes, list):
				for pax in paxes:
					si.append("custom_passenger", {
						"pax_id": pax.get("paxid"),
						"name1": pax.get("name"),
						"surname": pax.get("surname"),
					})
			
			si.custom_total_pax = invoice.get("@TotalPax")
			si.custom_total_adults = invoice.get("@TotalAdults")
			si.custom_total_childrens = invoice.get("@TotalChildrens")

			if isinstance(taxes, list):
				for in_tax in taxes:
					for tax in taxes_and_charges.taxes:
						si.append("taxes", {
							"charge_type": tax.charge_type,
							"account_head": tax.account_head,
							"description": tax.description,
							"tax_amount": in_tax.get("@total")
						})

			si.set_missing_values()
			si.insert(ignore_permissions=True)
		


def order_customer(customer):
	customerName = frappe.db.exists("Customer", {"custom_customer_id": customer.get("@Id")})
	if not customerName:
		cus_doc = frappe.get_doc({
			"doctype": "Customer",
			"custom_customer_id": customer.get("@Id"),
			"customer_name": customer.get("Name"),
		})
		cus_doc.save()
		return cus_doc
	else:
		return frappe.get_doc("Customer", customerName)

def order_item(item):
	itemName = frappe.db.exists("Item", {"item_code": item.get("Productid")})
	if not itemName:
		item_group = {}
		item_doc = frappe.get_doc({
			"doctype": "Item",
			"item_code": item.get("Productid"),
			"item_name": item.get("ServiceName"),
			"is_stock_item": 0
		})
		customerGroup = frappe.db.exists("Item Group", {"custom_item_group_id": item.get("ProductGroup")})
		if not customerGroup:
			item_group = frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": item.get("ProductGroupName"),
				"custom_item_group_id": item.get("ProductGroup")
			}).save()
		else:
			item_group = frappe.get_doc("Item Group", customerGroup)

		item_doc.item_group = item_group.name
		item_doc.save()
		return item_doc
	else:
		return frappe.get_doc("Item", itemName)


def invoice_item(item, group):
	itemName = frappe.db.exists("Item", {"item_code": item.get("@ProductId")})
	if not itemName:
		item_group = {}
		item_doc = frappe.get_doc({
			"doctype": "Item",
			"item_code": item.get("@ProductId"),
			"item_name": item.get("#text"),
			"is_stock_item": 0
		})
		itemGroup = frappe.db.exists("Item Group", {"custom_item_group_id": group.get("@ProductGroup")})
		if not itemGroup:
			item_group = frappe.get_doc({
				"doctype": "Item Group",
				"item_group_name": group.get("@ProductGroupName"),
				"custom_item_group_id": group.get("@ProductGroup")
			}).save()
		else:
			item_group = frappe.get_doc("Item Group", itemGroup)

		item_doc.item_group = item_group.name
		item_doc.save()
		return item_doc
	else:
		return frappe.get_doc("Item", itemName)


def get_default_tax_template():
    return frappe.get_doc("Sales Taxes and Charges Template", frappe.get_all("Sales Taxes and Charges Template", filters={"is_default": 1})[0].name)