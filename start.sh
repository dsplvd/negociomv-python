#/bin/bash

FILE=/data/piusb.bin
if test -f "$FILE"; then
    echo "$FILE exist"
else
  dd if=/dev/zero of=/data/piusb.bin bs=1M count=128
  mkdosfs /data/piusb.bin
  mkdir /data/temp_files/
fi

modprobe g_mass_storage file=/data/piusb.bin removable=1 ro=0 stall=0

python gpio.py && pon huawei && python solid-balena.py
