import pyinotify
import sys
import time
import threading
import syslog
from datetime import datetime

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

def file_get_contents(filename):
  if os.path.exists(filename):
    fp = open(filename, "r")
    content = fp.read()
    fp.close()
    return content

def ProcessData():
    syslog.syslog("==> Waiting for files...")
    time.sleep(15)

    if not os.path.isfile('/home/pi/piusb.bin'):
      syslog.syslog("==> Bin file not found, creating bin file and mounting...")
      createBinFile = Popen(['sudo dd bs=1M if=/dev/zero of=/home/pi/piusb.bin count=64 && sudo mkdosfs /home/pi/piusb.bin -F 32 -I'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
      time.sleep(7)
    else:
      syslog.syslog("==> Bin file found, mounting...")

    mountFilesystem = Popen(['mkdir -p /mnt/usbfat32 && sudo mount -o ro /home/pi/piusb.bin /mnt/usbfat32'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
    output, error = mountFilesystem.communicate()

    if mountFilesystem.returncode == 0:
      syslog.syslog("==> Filesystem mounted, syncing files...")
      syncFiles = Popen(['rm -rf /home/pi/temp_files && mkdir /home/pi/temp_files && rsync -Irc --exclude ".*" /mnt/usbfat32/ /home/pi/temp_files/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
      output, error = syncFiles.communicate()

      if syncFiles.returncode == 0:

        syslog.syslog("==> Files synced, unmounting and processing...")
        unmountFilesystem = Popen(['sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
        output, error = unmountFilesystem.communicate()

        if unmountFilesystem.returncode == 0:

          syslog.syslog("==> Unmount successful, uploading...")

          # *** COMPLETED ***
          list_completed = glob.glob('/home/pi/temp_files/COMPLETED/*.CSV')

          if len(list_completed) != 0:

            completed_latest = '/home/pi/temp_files/COMPLETED/'+str(datetime.now().year)+'MO'+str('%02d' % datetime.now().month)+'.CSV'
            completed_latest_filename = str(datetime.now().year)+'MO'+str('%02d' % datetime.now().month)+'.CSV'

            if os.path.isfile(completed_latest):

              # completed_file = {'name': completed_latest_filename, 'parents': ['1iuLUfvco6cMEo5CmwHj3X-jFis27CgZE']}
              completed_file = {'name': completed_latest_filename, 'parents': [completedFolder]}
              completed_media = MediaFileUpload(completed_latest, mimetype='text/csv')
              completed_upload = service.files().create(body=completed_file, media_body=completed_media, fields='id').execute()

              syslog.syslog ('==> COMPLETED File ID: %s' % (completed_upload.get('id')))

              syslog.syslog("==> COMPLETED processed, DELETING BIN FILES FOR GOOD MEASURE")
              deleteBinFiles = Popen(['mkdir -p /mnt/usbfat32 && sudo mount -o rw /home/pi/piusb.bin /mnt/usbfat32 && sudo rm -rf /mnt/usbfat32/COMPLETED/*.* && sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

            else:
              syslog.syslog("==> " + completed_latest + " FILE NOT FOUND, DELETING BIN FILES")
              deleteBinFiles = Popen(['mkdir -p /mnt/usbfat32 && sudo mount -o rw /home/pi/piusb.bin /mnt/usbfat32 && sudo rm -rf /mnt/usbfat32/COMPLETED/*.* && sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

          else:
            syslog.syslog("==> No COMPLETED to upload, done")

          # *** TICKET ***
          list_ticket = glob.glob('/home/pi/temp_files/TICKET#/*.CSV')
          if len(list_ticket) != 0:

            createBigCsv = Popen(['sed \'\' /home/pi/temp_files/TICKET#/*.CSV > /home/pi/temp_files/TICKET#/bigfile.csv && lzma -c --stdout /home/pi/temp_files/TICKET#/bigfile.csv>/home/pi/temp_files/TICKET#/bigfile.lzma'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
            time.sleep(7);
            # ticket_file = {'name': 'bigfile.lzma', 'parents': ['1KChS1VhzSPdffXQ2u3D4YVt9Bw8mUInl']}
            ticket_file = {'name': 'bigfile.lzma', 'parents': [ticketFolder]}
            ticket_media = MediaFileUpload('/home/pi/temp_files/TICKET#/bigfile.lzma', mimetype='text/csv')
            ticket_upload = service.files().create(body=ticket_file, media_body=ticket_media, fields='id').execute()

            syslog.syslog ('==> TICKET File ID: %s' % (ticket_upload.get('id')))

            syslog.syslog("==> TICKET processed, done")

            deleteTicketFiles = Popen(['mkdir -p /mnt/usbfat32 && sudo mount -o rw /home/pi/piusb.bin /mnt/usbfat32 && sudo rm -rf /mnt/usbfat32/TICKET#/*.* && sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)


          else:
            syslog.syslog("==> No TICKET# to upload, done")

        elif syncFiles.returncode == 1:
           syslog.syslog('==> Cant find %s' % (error))
        else:
           assert syncFiles.returncode > 1
           syslog.syslog('==> Error occurred: %s' % (error))

      elif syncFiles.returncode == 1:
         syslog.syslog('==> Cant find %s' % (error))
      else:
         assert syncFiles.returncode > 1
         syslog.syslog('==> Error occurred: %s' % (error))


    elif mountFilesystem.returncode == 1:
      syslog.syslog('==> Cant find %s, unmounting...' % (error))
      Popen(['sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)
    else:
      assert mountFilesystem.returncode > 1
      syslog.syslog('Error occurred: %s, unmounting...' % (error))
      Popen(['sudo umount /mnt/usbfat32/'], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=-1)

class ModHandler(pyinotify.ProcessEvent):
    count = 0

    def _enable_watchdog(self):
        syslog.syslog('==> Watchdog enabled')
        self.count = 0

    def _upload_files(self):
        syslog.syslog('==> Processing USB Storage, ignoring further modifications...')
        ProcessData()

    def _run_cmd(self):
        syslog.syslog('==> Uploading files..., Watchdog disabled')
        uploadFiles = threading.Thread(target=self._upload_files)
        uploadFiles.start()
        enableWatchdog = threading.Timer(180, self._enable_watchdog)
        enableWatchdog.start()

    # evt has useful properties, including pathname
    def process_IN_MODIFY(self, evt):
        if self.count < 1:
            syslog.syslog('==> Filesystem modified')
            self._run_cmd()
        else:
            syslog.syslog('==> Filesystem modified but ignored')
        self.count +=1

syslog.syslog('*** NEGOCIOMV STARTED ***')

syslog.syslog('==> Checking for code changes...')

gitPull = Popen(['cd /home/pi/negociomv-python/ && git stash && git pull'], shell=True, stdin=None, stdout=None, stderr=None, bufsize=-1)

syslog.syslog('==> Retrieving folder names...')

homePath = os.path.expanduser("~")

if os.path.isfile(homePath + '/completed-folder'):
    completedFolder = file_get_contents(homePath + '/completed-folder').rstrip()
else: 
    syslog.syslog('==> Complete folder not set')
  
if os.path.isfile(homePath + '/ticket-folder'):
    ticketFolder = file_get_contents(homePath + '/ticket-folder').rstrip()
else:
    syslog.syslog('==> Ticket folder not set')

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

syslog.syslog('==> Drive API Login correct, uploading files on boot...')

ProcessData()

syslog.syslog('*** STARTING PIUSB WATCHDOG ***')
handler = ModHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/home/pi/piusb.bin', pyinotify.IN_MODIFY)
notifier.loop()
