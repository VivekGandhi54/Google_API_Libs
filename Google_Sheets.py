
# Object Spreadsheet creates an instance referring to a Google spreadsheet
# Each spreadsheet consists of multiple sheets, but has only one url,
# 	different gid (Sheet ID)
# Default Scope allows unlimited access
# Delete token.js from dir if changing scope

# --------------------------------------------------------------------------

import os
import pyodbc
import webbrowser
from httplib2 import Http
from __future__ import print_function
from googleapiclient import discovery
from googleapiclient.discovery import build
from oauth2client import file, client, tools

# ==========================================================================

class Spreadsheet(object):
	SCOPE = 'https://www.googleapis.com/auth/spreadsheets'  #Full access
	SPREADSHEET_ID = None   #url = .../d/<SPREADSHEET_ID>/...
	SERVICE = None
	SHEETS = []

	# ----------------------------------------------------------------------
	# Spreadsheet object constructor

	def __init__(self, id):
		self.SPREADSHEET_ID = id
		credenialPath = 'C:\\Users\\vgand\\Desktop\\MyStuff\\Personal Stuff\\Credentials\\Google API Credentials\\'

		store = file.Storage(credentialPath + 'token.pickle')
		creds = store.get()

		if not creds or creds.invalid:
			flow = client.flow_from_clientsecrets(credentialPath + 'credentials.json', self.SCOPE)
			creds = tools.run_flow(flow, store)

		self.SERVICE = build('sheets', 'v4', http = creds.authorize(Http()))

		request = self.SERVICE.spreadsheets().get(spreadsheetId = self.SPREADSHEET_ID)
		response = request.execute()
		self.SHEETS = response['sheets']

	# ----------------------------------------------------------------------
	#Request general spreadsheet data

	def getData(self):
		request = self.SERVICE.spreadsheets().get(spreadsheetId = self.SPREADSHEET_ID)
		response = request.execute()

		return response

	# ----------------------------------------------------------------------
	#return list of all Sheets in Spreadsheet

	def getSheets(self):
		sheetData = self.getData()['sheets']
		retVal = []

		for sheet in sheetData:
			retVal.append(Sheet(sheet['properties']['title'], self.SPREADSHEET_ID))

		return retVal

# ==========================================================================

#Sheets extends from Spreadsheets. Each spreadsheet can have multiple sheets
class Sheet(Spreadsheet):
	NAME = None
	SHEET_ID = None

	# ----------------------------------------------------------------------
	#Constructor, also initializes parent Spreadsheet class

	def __init__(self, name, idVal):
		if idVal.count('/') != 0:	#strips the spreadsheet id from the url
			idVal = idVal.split('/d/')[1].split('/')[0]

		Spreadsheet.__init__(self, idVal)
		self.NAME = name

		for sheet in self.SHEETS:
			if sheet['properties']['title'] == self.NAME:
				self.SHEET_ID = sheet['properties']['sheetId']

	# ----------------------------------------------------------------------
	#Returns MxN array with data in rectangular range '<sheet name>!<top left cell>:<bottom right cell>'

	def read(self, rangeVal):
		sheet = self.SERVICE.spreadsheets()

		result = sheet.values().get(spreadsheetId = self.SPREADSHEET_ID,
									range = rangeVal).execute()

		values = result.get('values', [])

		if not values:
			return -1

		return values

	# ----------------------------------------------------------------------
	# Write MxN data array to rectangular range '<sheet name>!<top left cell>:<bottom right cell>'

	def write(self, values, rangeVal, **kwargs):
		valueInpOpt = 'USER_ENTERED' #Default

		if 'value_input_option' in kwargs:
			valueInpOpt = kwargs['value_input_option']

		values_inp = []

		for row in values:
			row_str = [str(i) for i in row]
			values_inp.append(row_str)

		body = {'values': values_inp}

		sheet = self.SERVICE.spreadsheets()

		result = sheet.values().update(	spreadsheetId = self.SPREADSHEET_ID,
										range = rangeVal,
										valueInputOption = valueInpOpt,
										body = body).execute()

		return result

	# ----------------------------------------------------------------------
	# Write Database table to Google Sheet

	def DBToSheet(self, table):
		self.purge()

		data = table.readAll()
		inputData = [[None for x in range(len(table.COLS))] for x in range((len(data) + 1))]

		for col in table.COLS.keys():

			colName = table.COLS[col][3]
			inputData[0][col] = colName
			rowNum = 1

			for row in data:
				inputData[rowNum][col] = row[colName]
				rowNum += 1

		inpRange = self.NAME + '!A1:'
		inpRange += chr(64 + len(inputData[0])) + str(len(inputData))

		self.write(inputData, inpRange)

	# ----------------------------------------------------------------------
	# Open spreadsheet in default browser. Opens to correct sheet

	def open(self):
		url = 'https://docs.google.com/spreadsheets/d/' + self.SPREADSHEET_ID + '/edit#gid=' + str(self.SHEET_ID)

		webbrowser.open(url)

	# ----------------------------------------------------------------------
	# Clear entire spreadsheet. Get dimensions from properties

	def purge(self):
		inpRange = self.NAME + '!A1:'
		request = self.SERVICE.spreadsheets().get(spreadsheetId = self.SPREADSHEET_ID)
		response = request.execute()

		for sheet in response['sheets']:
			if sheet['properties']['title'] == self.NAME:
				gridProperties = sheet['properties']['gridProperties']
				rowCount = gridProperties['rowCount']

				columnCount = gridProperties['columnCount']
				colCharVal = self.colNumToLetter(columnCount)

				inpRange += colCharVal + str(rowCount)

		request = self.SERVICE.spreadsheets().values().clear(	spreadsheetId = self.SPREADSHEET_ID,
																range = inpRange,
																body = {})

		response = request.execute()

	# ----------------------------------------------------------------------
	# 1 -> A
	# 26 -> Z
	# 27 -> AA
	# 28 -> AB

	def colNumToLetter(self, columnCount):
		colCharVal = ''

		while columnCount > 0:
			colCharVal = chr(65 + (columnCount - 1)%26) + colCharVal
			columnCount = int((columnCount - (columnCount - 1)%26)/26)

		return colCharVal

# ==========================================================================
