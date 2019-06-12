import pyinotify
import subprocess
import sys
import time
import threading

class ModHandler(pyinotify.ProcessEvent):
    count = 0

    def _restart_timer(self):
        print('==> RUN ENDED')
	self.count = 0

    def _run_cmd(self):
        print('==> RUNNING')
	#print('==> RUN ENDED')
        timer = threading.Timer(30, self._restart_timer)
        timer.start()
        #subprocess.call(self.cmd.split(' '), cwd=self.cwd)

    # evt has useful properties, including pathname
    def process_IN_MODIFY(self, evt):
        print('Data changed')
        if self.count < 1:
            self._run_cmd()
	self.count +=1

handler = ModHandler()
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/home/pi/piusb.bin', pyinotify.IN_MODIFY)
notifier.loop()
