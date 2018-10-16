# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Drivers for FTDI devices."""

import threading
from copper.delegate import GpioDelegate
import pylibftdi
import usbinfo


class FtdiException(Exception):
  """An exception happened in the FTDI API."""


class Ftdi(object):
  """Class for interacting with FTDI using libftdi.
  """
  ID_VENDOR = 0x0403

  def __init__(self, serial_number):
    self.serial_number = serial_number

    # Number of buses corresponds to number of interface endpoints
    num_buses = len([ep for ep in usbinfo.endpoints(id_vendor=self.ID_VENDOR)
                     if ep.serial_number == serial_number
                     and ep.interface is not None])
    if num_buses == 0:
      raise FtdiException('No FTDI device with serial number {}.'.format(
          serial_number))

    # FTDI data buses are named DBUS on single bus devices or ADBUS, BDBUS,
    # CDBUS, etc. on multi-bus devices.
    if num_buses == 1:
      dbuses = ['dbus']
    else:
      dbuses = ['{}dbus'.format(chr(ord('a') + i)) for i in range(num_buses)]
    self._dbuses = dbuses
    self._dbus_map = dict(zip(dbuses, range(num_buses)))

    # Lazy create bit-bang device objects for each bus.
    self._bb_devices = [None] * num_buses

    # Create locks to protect concurrent read-modify-writes of bus ports.
    self._bus_rmw_lock = [threading.Lock()] * num_buses

    # Create delegate objects for each GPIO grouped by buses
    for bus_name, bus in self._dbus_map.items():
      delegates = [_FtdiGpio(self, bus, pin) for pin in range(8)]
      self.__setattr__(bus_name, delegates)

  def set_bitbang_mode(self, bus, output_enable=0xFF):
    """Sets a specified bus to bit-bang mode.

    This operation should only be performed once per bus as a bus is typically
    hardwired to either serial or bit-bang circuitry.

    Args:
      bus: ID of the bus to index. This can either be a cardinal bus index
        or a name like 'ADBUS'.
      output_enable: 8-bit value representing the output_enable of the bus
        port with the LSB corresponding to bit 0 and the MSB corresponding
        to bit 7 of the bus. A high value signifies an enabled output.
    Raises:
      ValueError: When output_enable value is out of range.
      FtdiException: When deivce is already in bit-bang mode.
    """
    if output_enable not in range(256):
      raise ValueError('Illegal output_enable value: {}'.format(output_enable))
    bus = self._get_bus_index(bus)
    if self._bb_devices[bus]:
      raise FtdiException('Bus {} already set to bit-bang mode.'.format(bus))
    self._bb_devices[bus] = pylibftdi.BitBangDevice(
        self.serial_number, interface_select=bus)

  def get_comm_port(self, bus):
    """Get the communications port of a given bus.

    Args:
      bus: ID of the bus to index. This can either be a cardinal bus index
        or a name like 'ADBUS'.
    Returns:
      Communications port of the given bus.
    """
    bus = self._get_bus_index(bus)
    endpoints = [ep for ep in usbinfo.usbinfo()
                 if int(ep['idVendor'], 16) == self.ID_VENDOR
                 and ep.get('iSerialNumber') == self.serial_number
                 and ep.get('bInterfaceNumber', '').isdigit()
                 and ep.get('devname', '').startswith('/dev/tty')]
    for ep in endpoints:
      if int(ep['bInterfaceNumber'], 16) == bus:
        return ep['devname']

  def gpio_write(self, bus, index, write_data):
    """Write a digital value to a GPIO.

    Args:
      bus: ID of the bus to write to. This can either be a cardinal bus index
        or a name like 'ADBUS'.
      index: Index of the GPIO in bus to write.
      write_data: None or one of 0 or 1. If None is given then GPIO will
        enter a hi-Z mode assumming GPIO is capable of tri-state behavior.
    """
    bb = self._get_bit_bang_device(bus)
    mask = 1 << index
    imask = 0xFF ^ mask
    with self._bus_rmw_lock[bb.interface_select]:
      if write_data is None:
        bb.direction &= imask
      else:
        wmask = mask if write_data else 0
        bb.port = bb.port & imask | wmask
        bb.direction |= mask

  def gpio_read(self, bus, index):
    """Read a digital value from a GPIO.

    Args:
      bus: ID of the bus to read from. This can either be a cardinal bus index
        or a name like 'ADBUS'.
      index: Index of the GPIO to read from.
    Returns:
      Value of GPIO (either 0 or 1).
    """
    bb = self._get_bit_bang_device(bus)
    return (bb.port >> index) & 0x1

  def _get_bus_index(self, bus):
    """Returns the cardinal bus index for the specified bus.

    Args:
      bus: ID of the bus to index. This can either be a cardinal bus index
        or a name like 'ADBUS'.
    Returns:
      A cardinal bus index.
    Raises:
      ValueError: When an illegal bus value is given.
    """
    if isinstance(bus, str):
      try:
        return self._dbus_map[bus.lower()]
      except KeyError:
        raise ValueError('Illegal bus ID: {}'.format(bus))
    elif isinstance(bus, int):
      return bus
    else:
      raise ValueError('Illegal bus ID: {}'.format(bus))

  def _get_bit_bang_device(self, bus):
    """Returns the bit-bang device.

    Args:
      bus: ID of the bus to index. This can either be a cardinal bus index
        or a name like 'ADBUS'.
    Returns:
      A BitBangDevice object.
    Raises:
      FtdiException: When bus is not set to bit-bang mode.
    """
    bus = self._get_bus_index(bus)
    bit_bang_device = self._bb_devices[bus]
    if bit_bang_device is None:
      raise FtdiException('Bus {} is not set to bit-bang mode.'.format(bus))
    return bit_bang_device


class _FtdiGpio(GpioDelegate):
  """Implementation of GPIO delegate for an FTDI GPIO pin.

  Args:
    index: Index of the GPIO.
  """

  def __init__(self, ftdi, bus, index):
    self._ftdi = ftdi
    self._bus = bus
    self._index = index

  def write(self, write_data):
    self._ftdi.gpio_write(self._bus, self._index, write_data)

  def read(self):
    return self._ftdi.gpio_read(self._bus, self._index)
