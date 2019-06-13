from subprocess import Popen, PIPE
import glob
import os
import json
import requests
import syslog
#from pprint import pprint

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from apiclient.http import MediaFileUpload


SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server()
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)

mountFilesystem = Popen(['sudo mount -o ro /home/pi/piusb.bin /mnt/usbfat32'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

output, error = mountFilesystem.communicate()

if mountFilesystem.returncode == 0:

  syslog.syslog("Filesystem mounted, syncing files")

  syncFiles = Popen(['rsync -Irc --exclude ".*" /mnt/usbfat32/ /home/pi/temp_files/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

  output, error = syncFiles.communicate()

  if syncFiles.returncode == 0:

    syslog.syslog("Files synced, unmounting and processing")

    unmountFilesystem = Popen(['sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

    output, error = unmountFilesystem.communicate()

    if unmountFilesystem.returncode == 0:

      syslog.syslog("Unmount successful, uploading...")

      # *** COMPLETED ***
      list_completed = glob.glob('/home/pi/temp_files/COMPLETED/*.CSV')
      if len(list_completed) != 0:

        # completed_latest = max(list_completed, key=os.path.getctime)
        completed_latest = sorted(list_completed)[-1]
        completed_latest_filename = os.path.basename(completed_latest)

        completed_file = {'name': completed_latest_filename, 'parents': ['1iuLUfvco6cMEo5CmwHj3X-jFis27CgZE']}
        completed_media = MediaFileUpload(completed_latest, mimetype='text/csv')
        completed_upload = service.files().create(body=completed_file, media_body=completed_media, fields='id').execute()
        
        syslog.syslog ('File ID: %s' % (completed_upload.get('id')))      

        syslog.syslog("COMPLETED processed, done")

      else:
        syslog.syslog("No COMPLETED to upload, done")

      # *** TICKET ***
      list_ticket = glob.glob('/home/pi/temp_files/TICKET#/*.CSV')
      if len(list_ticket) != 0:

        # ticket_latest = max(list_ticket, key=os.path.getctime)
        ticket_latest = sorted(list_ticket)[-1]
        ticket_latest_filename = os.path.basename(ticket_latest)

        ticket_file = {'name': ticket_latest_filename, 'parents': ['1KChS1VhzSPdffXQ2u3D4YVt9Bw8mUInl']}
        ticket_media = MediaFileUpload(ticket_latest, mimetype='text/csv')
        ticket_upload = service.files().create(body=ticket_file, media_body=ticket_media, fields='id').execute()
        
        syslog.syslog ('File ID: %s' % (ticket_upload.get('id')))      

        syslog.syslog("TICKET processed, done")
        
      else:
        syslog.syslog("No TICKET# to upload, done")        

    elif syncFiles.returncode == 1:
       syslog.syslog('Cant find %s' % (error))
    else:
       assert syncFiles.returncode > 1
       syslog.syslog('Error occurred: %s' % (error))

  elif syncFiles.returncode == 1:
     syslog.syslog('Cant find %s' % (error))
  else:
     assert syncFiles.returncode > 1
     syslog.syslog('Error occurred: %s' % (error))


elif mountFilesystem.returncode == 1:
  syslog.syslog('Cant find %s' % (error))
else:
	assert mountFilesystem.returncode > 1
	syslog.syslog('Error occurred: %s' % (error))

