
import io
import os
import pickle
from httplib2 import Http
from __future__ import print_function
from googleapiclient.discovery import build
from oauth2client import file, client, tools
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# ==========================================================================

class Drive(object):
	#If modifying these scopes, delete the file token.json.
	SCOPES = ['https://www.googleapis.com/auth/drive']    #Full access
	SERVICE = None

	DOWNLOADS_FOLDER = 'C:\\Users\\vgand\\Downloads\\'
	CREDENTIAL_PATH = 'C:\\Users\\vgand\\Desktop\\MyStuff\\Personal Stuff\\Credentials\\Google API Credentials\\'

	# ----------------------------------------------------------------------
	# Constructor

	def __init__(self):

		# Location of 'token.pickel' and/or 'credentials.json'

		store = file.Storage(CREDENTIAL_PATH + 'token.pickle')
		creds = store.get()

		if not creds or creds.invalid:
			flow = client.flow_from_clientsecrets(CREDENTIAL_PATH + 'credentials.json', self.SCOPES)
			creds = tools.run_flow(flow, store)

		self.SERVICE = build('drive', 'v3', http = creds.authorize(Http()))

	# ----------------------------------------------------------------------
	# returns files = [{'id':<id>, 'name':<name>}, <file 2>, ... <file n>]

	def searchDrive(self):
		files = []
		page_token = None

		query = 'mimeType = "application/vnd.google-apps.folder"'
		query = 'name = "Final.pdf"'

		while True:
			response = self.SERVICE.files().list(	q = query,
													spaces = 'drive',
													fields = 'nextPageToken, files(id, name)',
													pageToken = page_token).execute()

			for file in response.get('files', []):
				files.append(file)

			page_token = response.get('nextPageToken', None)

			if page_token is None:
				break

		return files

	# ----------------------------------------------------------------------
	#returns byte file

	def downloadFile(self, file_id):
		request = self.SERVICE.files().get_media(fileId = file_id)
		byte_io = io.BytesIO()
		downloader = MediaIoBaseDownload(byte_io, request)
		done = False

		while not done:
			status, done = downloader.next_chunk()
			print("Download %d%%." % int(status.progress() * 100))

		return byte_io.getvalue()

	# ----------------------------------------------------------------------
	#saves binary file
	#kwargs['data_type']

	def save(self, file, location, **kwargs):
		if 'data_type' in kwargs.items():
			location = str(location) + '.' + str(kwargs['data_type'])

		f = open(location, 'wb')
		f.write(file)
		f.close()

	# ----------------------------------------------------------------------

	def download(file):
		file_id = file['id']
		file_name = file['name']

		file_bytes = self.downloadFile(file_id)
		self.save(file_bytes, DOWNLOADS_FOLDER + file_name)

	# ----------------------------------------------------------------------

	def createFolder(self, name):
		file_metadata = {	'name': name,
							'mimeType': 'application/vnd.google-apps.folder' }

		folder = self.SERVICE.files().create(	body = file_metadata,
												fields = 'id').execute()

		return folder['id']

	# ----------------------------------------------------------------------

	def insertFileToFolder(self, filePath, **kwargs):
		folders = []
		mimetype = 'image/jpeg'

		if kwargs is not None:
			if 'mimetype' in kwargs.keys():
				mimetype = kwargs['mimetype']
			if type(kwargs['folders']) is list:
				folders = kwargs['folders']
			else:
				folders.append(kwargs['folders'])

		fileName = filePath.split('/')
		fileName = fileName[len(fileName) - 1]

		file_metadata = {
			'name': fileName,
			'parents': folders
		}

		media = MediaFileUpload(	filePath,
									mimetype = mimetype,
									resumable = True)
	
		file = self.SERVICE.files().create(body = file_metadata,
											media_body = media,
											fields = 'id').execute()
	
		return file['id']

	# ----------------------------------------------------------------------
	# Get fields for a file
	# Possible fields = 'kind', 'id', 'name', 'mimeType'

	def getField(self, file_id, file_field = None):

		return self.SERVICE.files().get(fileId = file_id,
										fields = file_field).execute()

	# ----------------------------------------------------------------------
	# Change parent tree for file_id to new parent

	def moveTo(self, file_id, parent):
		previous_parents = ','.join(self.getField(file_id, 'parents')['parents'])

		file = self.SERVICE.files().update(	fileId = file_id,
											addParents = parent,
											removeParents = previous_parents,
											fields = 'id, parents').execute()

		return file

	# ----------------------------------------------------------------------
	def test(self, file_id, file_fields = ''):
		response =  self.SERVICE.files().get(fileId = file_id,
											fields = None).execute()

		print(response)
		return response

# ==========================================================================
