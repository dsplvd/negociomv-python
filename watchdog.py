import pyinotify
import subprocess
import sys
import time
import threading
import syslog

class ModHandler(pyinotify.ProcessEvent):
    count = 0

    def _restart_timer(self):
        syslog.syslog('==> Timer restarted')
        self.count = 0

    def _upload_files(self):
        syslog.syslog('*** UPLOADING COMPLETED FILES & TICKETS ***')
        runCompleteFlow = subprocess.Popen(['python /home/pi/negociomv-python/complete.py'], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
        output, error = runCompleteFlow.communicate()
        if runCompleteFlow.returncode == 0:
            syslog.syslog('*** Files uploaded successfully ***')
        elif runCompleteFlow.returncode == 1:
            syslog.syslog('*** Upload failed: %s ***' % (error))
        self.count = 0

    def _run_cmd(self):
        syslog.syslog('==> Restarting timer...')
        uploadFiles = threading.Thread(self._restart_timer, args=())
        timer.start()

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
