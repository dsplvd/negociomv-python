#!/usr/bin/env python
   
import RPi.GPIO as GPIO
import time
import syslog

syslog.syslog('==> Restarting modem...')
   
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)
   
GPIO.output(26, True)
time.sleep(2)
GPIO.output(26, False)
   
GPIO.cleanup()
