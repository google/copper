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

"""USB driver for Google Tigertail."""
import usb


class TigertailError(Exception):
  """Error when parsing device configuration."""


class Tigertail(object):
  """Class representing a Google Tigertail device.

  Args:
    serial: A string that's the serial number of the Tigertail device.
  """
  USB_VID = 0x18d1
  USB_PID = 0x5027
  READ_EP_OFFSET = 0x81
  WRITE_EP_OFFSET = 0x1

  def __init__(self, serial):
    devices = usb.core.find(idVendor=self.USB_VID, idProduct=self.USB_PID,
                            find_all=True)

    if not devices:
      raise TigertailError('Unable to find Tigertail.')

    if serial:
      for device in devices:
        if usb.util.get_string(device, device.iSerialNumber) == str(serial):
          self._device = device
          break
      else:
        raise TigertailError(
            'Unable to find Tigertail with serial number {}.'.format(serial))
    else:
      self._device = devices.next()

    # Attempt to set configuration
    try:
      self._device.set_configuration()
    except usb.core.USBError:
      pass

    # Get an endpoint instance
    config = self._device.get_active_configuration()
    interface = usb.util.find_descriptor(config, bInterfaceNumber=0)
    if not interface:
      raise TigertailError('Tigertail interface not found.')

    if self._device.is_kernel_driver_active(interface.bInterfaceNumber):
      self._device.detach_kernel_driver(interface.bInterfaceNumber)

    read_endpoint_number = interface.bInterfaceNumber + self.READ_EP_OFFSET
    self._read_endpoint = usb.util.find_descriptor(
        interface, bEndpointAddress=read_endpoint_number)

    write_endpoint_number = interface.bInterfaceNumber + self.WRITE_EP_OFFSET
    self._write_endpoint = usb.util.find_descriptor(
        interface, bEndpointAddress=write_endpoint_number)

  def off(self):
    """Do not allow any pass-thru to DUT USB-C port."""
    self._mux('off')

  def sel_a(self):
    """Pass-thru port A to DUT USB-C port."""
    self._mux('A')

  def sel_b(self):
    """Pass-thru port B to DUT USB-C port."""
    self._mux('B')

  def _mux(self, option):
    """Set mux select option.

    Args:
      option: multiplexor option
    """
    self._write_endpoint.write('mux {}\r\n'.format(option))
