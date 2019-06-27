#/bin/bash

FILE=/data/piusb.bin
if test -f "$FILE"; then
    echo "$FILE exist"
else
  echo "$FILE doesn't exist, creating filesystem..."
  dd if=/dev/zero of=/data/piusb.bin bs=1M count=128
  mkdosfs /data/piusb.bin
  mkdir /data/temp_files/
fi

echo "Loading modules..."

modprobe dwc2 && modprobe g_mass_storage file=/data/piusb.bin removable=1 ro=0 stall=0 &

#python gpio.py

#echo "Starting PPP interface..."

#pon huawei

#echo "Runing python scripts..."

python solid-balena.py