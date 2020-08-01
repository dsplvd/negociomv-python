from subprocess import Popen, PIPE
import glob
import os
import json

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from apiclient.http import MediaFileUpload

import os

def file_get_contents(filename):
  if os.path.exists(filename):
    fp = open(filename, "r")
    content = fp.read()
    fp.close()
    return content


homePath = os.path.expanduser("~")
completedFolder = file_get_contents(homePath + '/completed-folder').rstrip()
ticketFolder = file_get_contents(homePath + '/ticket-folder').rstrip()

SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('../token.pickle'):
    with open('../token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            '../credentials.json', SCOPES)
        creds = flow.run_local_server()
    # Save the credentials for the next run
    with open('../token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)

print "COMPLETED FOLDER CONTAINTS:"

qString = "'{}' in parents".format(completedFolder)

results = service.files().list(
    pageSize=10, fields="nextPageToken, files(id, name)", q=qString).execute()
items = results.get('files', [])

if not items:
    print('No files found.')
else:
    print('Files:')
    for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))

print "TICKET FOLDER CONTAINS"

qString = "'{}' in parents".format(ticketFolder)

results = service.files().list(
    pageSize=10, fields="nextPageToken, files(id, name)", q=qString).execute()
items = results.get('files', [])

if not items:
    print('No files found.')
else:
    print('Files:')
    for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))
