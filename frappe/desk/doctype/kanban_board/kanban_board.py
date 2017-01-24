# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe import _
from frappe.model.document import Document


class KanbanBoard(Document):
	def validate(self):
		for column in self.columns:
			if not column.column_name:
				frappe.msgprint(frappe._("Column Name cannot be empty"), raise_exception=True)


@frappe.whitelist()
def add_column(board_name, column_title):
	'''Adds new column to Kanban Board'''
	doc = frappe.get_doc("Kanban Board", board_name)
	for col in doc.columns:
		if column_title == col.column_name:
			frappe.throw(_("Column <b>{0}</b> already exist.").format(column_title))

	doc.append("columns", dict(
		column_name=column_title
	))
	doc.save()
	return doc.columns


@frappe.whitelist()
def archive_restore_column(board_name, column_title, status):
	'''Set column's status to status'''
	doc = frappe.get_doc("Kanban Board", board_name)
	for col in doc.columns:
		if column_title == col.column_name:
			col.status = status

	doc.save()
	return doc.columns


@frappe.whitelist()
def update_doc(doc):
	'''Updates the doc when card is edited'''
	doc = json.loads(doc)

	try:
		to_update = doc
		doctype = doc['doctype']
		docname = doc['name']
		doc = frappe.get_doc(doctype, docname)
		doc.update(to_update)
		doc.save()
	except:
		return {
			'doc': doc,
			'exc': frappe.utils.get_traceback()
		}
	return doc


@frappe.whitelist()
def update_order(board_name, order):
	'''Save the order of cards in columns'''
	board = frappe.get_doc('Kanban Board', board_name)
	doctype = board.reference_doctype
	fieldname = board.field_name
	order_dict = json.loads(order)

	updated_cards = []
	for col_name, cards in order_dict.iteritems():
		order_list = []
		for card in cards:
			column = frappe.get_value(
				doctype,
				{'name': card},
				fieldname
			)
			if column != col_name:
				frappe.set_value(doctype, card, fieldname, col_name)
				updated_cards.append(dict(
					name=card,
					column=col_name
				))

		for column in board.columns:
			if column.column_name == col_name:
				column.order = json.dumps(cards)

	board.save()
	return board, updated_cards


@frappe.whitelist()
def quick_kanban_board(doctype, board_name, field_name):
	'''Create new KanbanBoard quickly with default options'''
	doc = frappe.new_doc('Kanban Board')
	options = frappe.get_value('DocField', dict(
            parent=doctype,
            fieldname=field_name
        ), 'options')

	columns = []
	if options:
		columns = options.split('\n')

	for column in columns:
		if not column:
			continue
		doc.append("columns", dict(
			column_name=column
		))

	doc.kanban_board_name = board_name
	doc.reference_doctype = doctype
	doc.field_name = field_name
	doc.save()
	return doc


@frappe.whitelist()
def update_column_order(board_name, order):
	'''Set the order of columns in Kanban Board'''
	board = frappe.get_doc('Kanban Board', board_name)
	order = json.loads(order)
	old_columns = board.columns
	new_columns = []

	for col in order:
		for column in old_columns:
			if col == column.column_name:
				new_columns.append(column)
				old_columns.remove(column)

	new_columns.extend(old_columns)

	board.columns = []
	for col in new_columns:
		board.append("columns", dict(
			column_name=col.column_name,
			status=col.status,
			order=col.order,
			indicator=col.indicator,
		))

	board.save()
	return board

@frappe.whitelist()
def set_indicator(board_name, column_name, indicator):
	'''Set the indicator color of column'''
	board = frappe.get_doc('Kanban Board', board_name)

	for column in board.columns:
		if column.column_name == column_name:
			column.indicator = indicator
	
	board.save()
	return board