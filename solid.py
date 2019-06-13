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

class ModHandler(pyinotify.ProcessEvent):
    count = 0

    def _restart_timer(self):
        syslog.syslog('==> Timer restarted')
        self.count = 0

    def _upload_files(self):
        syslog.syslog('==> Processing USB Storage...')
        runCompleteFlow = Popen(['python /home/pi/negociomv-python/complete.py'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
        output, error = runCompleteFlow.communicate()
        if runCompleteFlow.returncode == 0:
            syslog.syslog('==> Files uploaded successfully')
            self.count = 0
        elif runCompleteFlow.returncode == 1:
            syslog.syslog('==> Upload failed: %s ***' % (error))
            self.count = 0

    def _run_cmd(self):
        syslog.syslog('==> Uploading files...')
        uploadFiles = threading.Thread(target=self._upload_files)
        uploadFiles.start()

    # evt has useful properties, including pathname
    def process_IN_MODIFY(self, evt):
        syslog.syslog('*** PISUSB MODIFIED ***')
        if self.count < 1:
            self._run_cmd()
  self.count +=1


syslog.syslog('*** STARTING PIUSB WATCHDOG ***')
handler = ModHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/home/pi/piusb.bin', pyinotify.IN_MODIFY)
notifier.loop()

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

syslog.syslog('==> DRIVE API LOGIN CORRECT')
