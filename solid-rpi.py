import pyinotify
import sys
import time
import threading
import syslog

from subprocess import Popen, PIPE
import glob
import os
import json
import requests

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from apiclient.http import MediaFileUpload

import RPi.GPIO as GPIO

def ProcessData():
    print("==> Waiting for files...")
    time.sleep(10)
    mountFilesystem = Popen(['mkdir -p /mnt/usbfat32 && mount -o ro /home/pi/piusb.bin /mnt/usbfat32'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
    output, error = mountFilesystem.communicate()
    if mountFilesystem.returncode == 0:
      print("==> Filesystem mounted, syncing files...")
      syncFiles = Popen(['rsync -Irc --exclude ".*" /mnt/usbfat32/ /home/pi/temp_files/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
      output, error = syncFiles.communicate()

      if syncFiles.returncode == 0:

        print("==> Files synced, unmounting and processing...")
        unmountFilesystem = Popen(['umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
        output, error = unmountFilesystem.communicate()

        if unmountFilesystem.returncode == 0:

          print("==> Unmount successful, uploading...")

          # *** COMPLETED ***
          list_completed = glob.glob('/home/pi/temp_files/COMPLETED/*.CSV')
          if len(list_completed) != 0:

            # completed_latest = max(list_completed, key=os.path.getctime)
            completed_latest = sorted(list_completed)[-1]
            completed_latest_filename = os.path.basename(completed_latest)

            completed_file = {'name': completed_latest_filename, 'parents': ['1iuLUfvco6cMEo5CmwHj3X-jFis27CgZE']}
            completed_media = MediaFileUpload(completed_latest, mimetype='text/csv')
            completed_upload = service.files().create(body=completed_file, media_body=completed_media, fields='id').execute()
            
            print ('==> COMPLETED File ID: %s' % (completed_upload.get('id')))      

            print("==> COMPLETED processed, done")

          else:
            print("==> No COMPLETED to upload, done")

          # *** TICKET ***
          list_ticket = glob.glob('/home/pi/temp_files/TICKET#/*.CSV')
          if len(list_ticket) != 0:

            # ticket_latest = max(list_ticket, key=os.path.getctime)
            ticket_latest = sorted(list_ticket)[-1]
            ticket_latest_filename = os.path.basename(ticket_latest)

            ticket_file = {'name': ticket_latest_filename, 'parents': ['1KChS1VhzSPdffXQ2u3D4YVt9Bw8mUInl']}
            ticket_media = MediaFileUpload(ticket_latest, mimetype='text/csv')
            ticket_upload = service.files().create(body=ticket_file, media_body=ticket_media, fields='id').execute()
            
            print ('==> TICKET File ID: %s' % (ticket_upload.get('id')))      

            print("==> TICKET processed, done")
            
          else:
            print("==> No TICKET# to upload, done")        

        elif syncFiles.returncode == 1:
           print('==> Cant find %s' % (error))
        else:
           assert syncFiles.returncode > 1
           print('==> Error occurred: %s' % (error))

      elif syncFiles.returncode == 1:
         print('==> Cant find %s' % (error))
      else:
         assert syncFiles.returncode > 1
         print('==> Error occurred: %s' % (error))


    elif mountFilesystem.returncode == 1:
      print('==> Cant find %s, unmounting...' % (error))
      Popen(['umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
    else:
      assert mountFilesystem.returncode > 1
      print('Error occurred: %s, unmounting...' % (error))
      Popen(['umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

class ModHandler(pyinotify.ProcessEvent):
    count = 0

    def _enable_watchdog(self):
        print('==> Watchdog enabled')
        self.count = 0

    def _upload_files(self):
        print('==> Processing USB Storage, ignoring further modifications...')
        # runCompleteFlow = Popen(['python /home/pi/negociomv-python/complete.py'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
        # output, error = runCompleteFlow.communicate()
        # if runCompleteFlow.returncode == 0:
        #     print('==> Files uploaded successfully')
        #     self.count = 0
        # elif runCompleteFlow.returncode == 1:
        #     print('==> Upload failed: %s ***' % (error))
        #     self.count = 0
        ProcessData()
        # self.count = 0

    def _run_cmd(self):
        print('==> Uploading files..., Watchdog disabled')
        uploadFiles = threading.Thread(target=self._upload_files)
        uploadFiles.start()
        enableWatchdog = threading.Timer(180, self._enable_watchdog)
        enableWatchdog.start()

    # evt has useful properties, including pathname
    def process_IN_MODIFY(self, evt):
        if self.count < 1:
            print('==> Filesystem modified')
            self._run_cmd()
        else:
            print('==> Filesystem modified but ignored')
        self.count +=1

print('*** NEGOCIOMV STARTED ***')

print('==> Restarting modem...')
   
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)
   
GPIO.output(26, True)
time.sleep(2)
GPIO.output(26, False)
   
GPIO.cleanup()

print('==> Starting PPP interface...')

startPPP = Popen(['sleep 10 && sudo pon huawei'], shell=True, stdin=None, stdout=None, stderr=None, bufsize=-1)

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

print('==> Drive API Login correct, uploading files on boot...')

ProcessData()

print('*** STARTING PIUSB WATCHDOG ***')
handler = ModHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/home/pi/piusb.bin', pyinotify.IN_MODIFY)
notifier.loop()
