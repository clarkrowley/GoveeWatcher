#!/usr/bin/env python3

from time import sleep
import os
import sys
import struct
from datetime import datetime

from bleson import get_provider, Observer #, UUID16
from bleson.logger import log, set_level, ERROR, DEBUG

class GoveeWatcher:

  def __init__(self):
    self.govee_devices = {}
    self.start()

    # Disable warnings
    set_level(ERROR)
    # # Uncomment for debug log level
    # set_level(DEBUG)

  def print_values(self,mac):
    govee_device = self.govee_devices[mac]
    fmt='%4s %6s - T: %4.1f C / %5.1f F - RH: %5.1f %% - Bat: %3.0f %%'
    print( fmt % (
       govee_device['name'],
       govee_device['now'],
       govee_device['tempInC'],
       govee_device['tempInF'],
       govee_device['humidity'],
       govee_device['battery'] )
    )

  def print_rssi(self,mac):
    govee_device = govee_devices[mac]
    print(
        f"{govee_device['name']} - RSSI: {govee_device['rssi']}"
    )

  def decode_temp_humid_bat(self,advertisement) -> tuple[float, float, float]:
    temp, hum, bat = struct.unpack_from("<HHB", advertisement.mfg_data[-5:])
    if temp & (1 << 15):
      temp = temp - (1 << 16)
    if hum & (1 << 15):
      hum = hum - (1 << 16)
    temp /= 100
    hum /= 100
    return temp, hum, bat

  # On BLE advertisement callback
  def on_advertisement(self,advertisement):

    if advertisement.name is not None:
      if advertisement.name.startswith('Govee_H5179'):
        now = datetime.now().strftime("%H:%M:%S")
        self.mac = advertisement.name.split("_")[2]
        if self.mac not in self.govee_devices:
          self.govee_devices[self.mac] = {}
        self.govee_devices[self.mac]["name"] = self.mac
        self.govee_devices[self.mac]["now"] = now

    if advertisement.mfg_data is not None:
      encoded_data = int(advertisement.mfg_data.hex()[0:5], 16)
      if encoded_data == 6286:
        tempC,rh,bat = self.decode_temp_humid_bat(advertisement)
        tempF = tempC * 1.8 + 32
        self.govee_devices[self.mac]["tempInC"] = tempC
        self.govee_devices[self.mac]["tempInF"] = tempF
        self.govee_devices[self.mac]["humidity"] = rh
        self.govee_devices[self.mac]["battery"] = bat
        self.print_values(self.mac)

  def start(self):
    self.adapter = get_provider().get_adapter()
    print(self.adapter)

    self.observer = Observer(self.adapter)
    print(self.observer)
    self.observer.on_advertising_data = self.on_advertisement

try:
  watcher = GoveeWatcher()
  while True:
    watcher.observer.start()
    sleep(2)
    watcher.observer.stop()

except KeyboardInterrupt:
  try:
    watcher.observer.stop()
    sys.exit(0)
  except SystemExit:
    watcher.observer.stop()
    os._exit(0)

