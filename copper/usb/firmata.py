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

"""USB driver for a Firmata-based device."""
import abc
import os
import select
import threading
from copper.delegate import AnalogInputDelegate
from copper.delegate import GpioDelegate
from copper.delegate import I2cDelegate
import pyfirmata
import queue
import usbinfo

I2C_WRITE = 0x00
I2C_READ = 0x08
I2C_END_TX_MASK = 0x40


class FirmataException(Exception):
  """An exception happened in the Firmata API."""


class _ArduinoABC(object):
  """Abstract base class for an Arduino running StandardFirmata.

  Args:
    serial_number: String of the USB iSerialNumber associated with the device.
  """
  __metaclass__ = abc.ABCMeta

  def __init__(self, serial_number):
    if not isinstance(serial_number, str):
      raise FirmataException('Serial number must be a string.')
    self._serial_number = serial_number

    # Find associated character device
    endpoints = [ep for ep in usbinfo.endpoints(serial_number=serial_number)
                 if (ep.id_vendor, ep.id_product) in self.IDS
                 and ep.devname.startswith('/dev/tty')]
    if len(endpoints) != 1:
      raise FirmataException(
          'Exactly one character file expected for Firmata device.')

    self._client = self.CLASS(endpoints[0].devname)

    # Launch packet handler thread
    self._terminate_pipe = os.pipe()
    self._packet_handler_thread = threading.Thread(
        target=self._packet_handler_task)
    self._packet_handler_thread.daemon = True
    self._packet_handler_thread.start()

    # Setup handlers for incoming messages.
    self._client.add_cmd_handler(pyfirmata.DIGITAL_MESSAGE,
                                 self._handle_digital_message)
    self._client.add_cmd_handler(pyfirmata.I2C_REPLY,
                                 self._handle_sysex_i2c_reply)

    # Create a blank dictionary mapping each GPIO to a callback function
    self._gpio_callbacks = dict()

    # Configure I2C
    self._i2c_enabled = False
    self._i2c_reply = queue.Queue(1)
    self._i2c_read_lock = threading.Lock()

    # Setup I/O delegates
    self.gpio = [_ArduinoGpio(self, port_id=idx)
                 for idx in range(len(self._client.digital))]
    self.analog_in = [_ArduinoAnalogInput(self, port_id=idx)
                      for idx in range(len(self._client.analog))]
    self.i2c = _ArduinoI2c(self)

  def close(self):
    """Close all connections."""
    os.write(self._terminate_pipe[1], chr(0))
    self._client.exit()

  def _packet_handler_task(self):
    """Packet handler task."""
    terminate_read_pipe = self._terminate_pipe[0]
    serial_port = self._client.sp
    rlist = [terminate_read_pipe, serial_port]
    while True:
      rsel, _, _ = select.select(rlist, [], [])
      if terminate_read_pipe in rsel:
        break
      if serial_port in rsel:
        while self._client.bytes_available():
          self._client.iterate()

  def _handle_digital_message(self, port_nr, lsb, msb):
    """Override for the pyfirmata DIGITAL_MESSAGE handler.

    The digital message handler handles changes to the input values on a
    port. This handler updates the locally cached value and invokes any
    callbacks associated with that GPIO.

    Args:
      port_nr: Port number to update.
      lsb: Least significant bit
      msb: 7 most significant bits
    """
    mask = (msb << 7) + lsb
    port = self._client.digital_ports[port_nr]
    old_values = [pin.value for pin in port.pins]
    port.update(mask)
    new_values = [pin.value for pin in port.pins]
    for idx, old_pin_value in enumerate(old_values):
      if old_pin_value != new_values[idx]:
        callback = self._gpio_callbacks.get(idx + port_nr * 8, None)
        if callback:
          callback()

  def _handle_sysex_i2c_reply(self, num_bytes, *rx_data):  # pylint: disable=unused-argument
    """Handler for SYSEX_I2C_REPLY.

    Args:
      num_bytes: Number of bytes in the reply data.
      *rx_data: List of bytes in the reply data.
    """
    i2c_reply = list()
    data = rx_data[3:]
    for lsb, msb in zip(data[0::2], data[1::2]):
      i2c_reply.append(lsb | (msb << 7))
    self._i2c_reply.put(i2c_reply)

  def gpio_write(self, index, write_value):
    """Write a digital value to a GPIO.

    Args:
      index: Index of the GPIO to write.
      write_value: None or one of 0 or 1. If None is given then GPIO will
        enter a hi-Z mode assumming GPIO is capable of tri-state behavior.
    """
    if write_value is None:
      self._client.digital[index].mode = pyfirmata.INPUT
    else:
      self._client.digital[index].write(int(write_value))
      self._client.digital[index].mode = pyfirmata.OUTPUT

  def gpio_read(self, index):
    """Read a digital value from a GPIO.

    Args:
      index: Index of the GPIO to read from.
    Returns:
      Value of GPIO (either 0 or 1).
    """
    # Prior to first write, read values will return None
    read_value = self._client.digital[index].read()
    return 0 if read_value is None else int(read_value)

  def gpio_callback(self, index, func):
    """Sets the callback function for changes to the specified GPIO.

    Args:
      index: Index of GPIO to trigger from.
      func: Function to register when GPIO toggles. If None is supplied then
        no action will be taken when the GPIO toggles. Registering a callback
        should result in that GPIO transitioning to input mode.
    Raises:
      FirmataException: When callback function isn't callable.
    """
    if not callable(func):
      raise FirmataException('Callback function must be callable.')
    if func:
      self.gpio_write(index, None)
      self._gpio_callbacks[index] = func
      self._client.digital[index].enable_reporting()
    else:
      del self._gpio_callbacks[index]
      self._client.digital[index].disable_reporting()

  def i2c_enable(self):
    """Enable primary I2C bus."""
    self._client.send_sysex(pyfirmata.I2C_CONFIG, bytearray([0, 0]))

  def i2c_write(self, address, register, write_data):
    """Write data to a register on an I2C slave.

    Args:
      address: Address of I2C slave to write to.
      register: 8-bit value indicating the slave register to write to.
      write_data: bytearray of data to write.
    """
    payload = bytearray([address, I2C_WRITE])
    data = chr(register) + write_data
    for item in data:
      lsb = item & 0x7f
      payload.append(lsb)
      msb = (item >> 7) & 0x7f
      payload.append(msb)
    self._client.send_sysex(pyfirmata.I2C_REQUEST, payload)

  def adc_enable(self, index):
    """Enable a specified ADC.

    Args:
      index: ADC index to enable.
    """
    self._client.analog[index].enable_reporting()

  def adc_disable(self, index):
    """Disable a specified ADC.

    Args:
      index: ADC index to disable.
    """
    self._client.analog[index].disable_reporting()

  def adc_read(self, index):
    """Read voltage value from a specified ADC.

    Args:
      index: ADC index to read from.
    Returns:
      Voltage value at ADC pin.
    Raises:
      FirmataException: If ADC is not enabled first.
    """
    pin = self._client.analog[index]
    if not pin.reporting:
      raise FirmataException('ADC must first be enabled before reading.')
    return pin.value

  def i2c_read(self, address, register, num_bytes, repeated_start=False):
    """Read data from an I2C slave.

    Args:
      address: Address of I2C slave to read from.
      register: 8-bit value indicating the slave register to write to.
      num_bytes: Number of bytes to read from.
      repeated_start: Use a repeated START.
    Returns:
      bytearray of returned data.
    Raises:
      FirmataException: If a register is not specified.
    """
    if register is None:
      raise FirmataException('Bare I2C reads not allowed on Firmata.')
    mode = I2C_READ | (I2C_END_TX_MASK if repeated_start else 0x0)
    with self._i2c_read_lock:
      payload = bytearray([address, mode,
                           register & 0x7f, (register >> 7) & 0x7f,
                           num_bytes & 0x7f, (num_bytes >> 7) & 0x7f])
      self._client.send_sysex(pyfirmata.I2C_REQUEST, payload)
      i2c_reply = self._i2c_reply.get()
      return bytearray(i2c_reply[:num_bytes])


class _ArduinoGpio(GpioDelegate):
  """Delegate implentation for Arduino GPIO.

  Args:
    arduino: Parent Arduino object.
    port_id: Port ID of GPIO.
  """

  def __init__(self, arduino, port_id):
    self._arduino = arduino
    self._port_id = port_id

  def write(self, write_value):
    """Write a digital value to the GPIO.

    Args:
      write_value: None or one of 0 or 1. If None is given then GPIO will
        enter a hi-Z mode assumming GPIO is capable of tri-state behavior.
    """
    self._arduino.gpio_write(self._port_id, write_value)

  def read(self):
    """Read a digital value from the GPIO.

    Returns:
      Value of GPIO (either 0 or 1).
    """
    return self._arduino.gpio_read(self._port_id)

  def callback(self, func):
    """Sets the callback function for changes to the specified GPIO.

    Args:
      func: Function to register when GPIO toggles. If None is supplied then
        no action will be taken when the GPIO toggles. Registering a callback
        should result in that GPIO transitioning to input mode.
    """
    self._arduino.gpio_callback(self._port_id, func)


class _ArduinoAnalogInput(AnalogInputDelegate):
  """Delegate implentation for Arduino ADC.

  Args:
    arduino: Parent Arduino object.
    port_id: Port ID of ADC pin.
  """
  ADC_VOLTAGE_MIN = 0.0
  ADC_VOLTAGE_MAX = 5.0

  def __init__(self, arduino, port_id):
    self._arduino = arduino
    self._port_id = port_id

  def read(self):
    """Read an analog value from the ADC pin.

    Returns:
      Voltage value at ADC pin.
    """
    return self.ADC_VOLTAGE_MAX * self._arduino.adc_read(self._port_id)

  @property
  @abc.abstractmethod
  def min(self):
    """Minimum sensed voltage on this ADC input."""
    return self.ADC_VOLTAGE_MIN

  @property
  @abc.abstractmethod
  def max(self):
    """Maximum sensed voltage on this ADC input."""
    return self.ADC_VOLTAGE_MAX


class _ArduinoI2c(I2cDelegate):
  """Delegate implentation for Arduino GPIO.

  Args:
    arduino: Parent Arduino object.
  """

  def __init__(self, arduino):
    self._arduino = arduino

  def write(self, address, register, write_data):
    """Write data to a register on an I2C slave.

    Args:
      address: Address of I2C slave to write to.
      register: 8-bit value indicating the slave register to write to.
      write_data: bytearray of data to write.
    """
    self._arduino.i2c_write(address, register, write_data)

  def read(self, address, register, num_bytes, repeated_start=False):
    """Read data from an I2C slave.

    Args:
      address: Address of I2C slave to read from.
      register: 8-bit value indicating the slave register to write to.
      num_bytes: Number of bytes to read from.
      repeated_start: Use a repeated START.
    Returns:
      bytearray of returned data.
    """
    return self._arduino.i2c_read(address, register, num_bytes, repeated_start)


class ArduinoUno(_ArduinoABC):
  """Object wrapper for an Arduino Uno running StandardFirmata.

  Args:
    serial_number: String of the USB iSerialNumber associated with the device.
  """
  CLASS = pyfirmata.Arduino
  IDS = [(0x2341, 0x0043), (0x2341, 0x0001), (0x2A03, 0x0043), (0x2341, 0x0243)]

  def __init__(self, serial_number):
    _ArduinoABC.__init__(self, serial_number)


class ArduinoMega(_ArduinoABC):
  """Object wrapper for an Arduino Mega running StandardFirmata.

  Args:
    serial_number: String of the USB iSerialNumber associated with the device.
  """
  CLASS = pyfirmata.ArduinoMega
  IDS = [(0x2341, 0x0010), (0x2341, 0x0042), (0x2A03, 0x0010),
         (0x2A03, 0x0042), (0x2341, 0x0210), (0x2341, 0x0242)]

  def __init__(self, serial_number):
    _ArduinoABC.__init__(self, serial_number)


class ArduinoDue(_ArduinoABC):
  """Object wrapper for an Arduino Due running StandardFirmata.

  Args:
    serial_number: String of the USB iSerialNumber associated with the device.
  """
  CLASS = pyfirmata.ArduinoDue
  IDS = [(0x2341, 0x003d), (0x2341, 0x003e)]

  def __init__(self, serial_number):
    _ArduinoABC.__init__(self, serial_number)
