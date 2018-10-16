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

"""Delegate classes."""
import abc


class GpioDelegate(object):
  """Abstract base class for digitial GPIO delegate class."""
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def write(self, value):
    """Write a digital value to a GPIO.

    Args:
      value: One of 0 or 1
    """

  @abc.abstractmethod
  def read(self):
    """Read a digital value from a GPIO.

    Returns:
      Value of GPIO (either 0 or 1).
    """

  def callback(self, func):
    """Sets the callback function for changes to the specified GPIO.

    Args:
      func: Function to register when GPIO toggles. If None is supplied then
        no action will be taken when the GPIO toggles.
    """
    raise NotImplementedError('This delegate does not support callbacks.')


class AnalogInputDelegate(object):
  """Abstract base class for analog input delegate class."""
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def read(self):
    """Read an analog value for an ADC.

    Returns:
      Voltage read at ADC input.
    """

  @property
  @abc.abstractmethod
  def min(self):
    """Minimum sensed voltage on this ADC input."""

  @property
  @abc.abstractmethod
  def max(self):
    """Maximum sensed voltage on this ADC input."""


class AnalogOutputDelegate(object):
  """Abstract base class for analog output delegate class."""
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def write(self, voltage):
    """Write an analog value to a DAC.

    Args:
      voltage: Voltage to drive a DAC output.
    """

  @property
  @abc.abstractmethod
  def min(self):
    """Minimum voltage that can be driven on this DAC output."""

  @property
  @abc.abstractmethod
  def max(self):
    """Maximum voltage that can be driven on this DAC output."""


class I2cDelegate(object):
  """Abstract base class for I2C master delegate class."""
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def write(self, address, register, data):
    """Write data to a register on an I2C slave.

    Args:
      address: Index of the GPIO to write
      register: 8-bit value indicating the slave register to write to
      data: bytearray of data to write
    """
    raise NotImplementedError('I2C write not implemented')

  @abc.abstractmethod
  def read(self, address, register, num_bytes, repeated_start=False):
    """Read data from an I2C slave.

    Args:
      address: Index of the GPIO to write
      register: 8-bit value indicating the slave register to write to
      num_bytes: Number of bytes to read from
      repeated_start: Use a repeated START.
    Return:
      bytearray of returned data
    """

  def write8(self, address, register, data):
    """Write a single byte to an I2C slave.

    Arguments:
      address: I2C slave address to target.
      register: Register to write to.
      data: Data to write to slave.
    """
    self.write(address, register, bytearray([data]))

  def read8(self, address, register, repeated_start=False):
    """Read a single byte from an I2C slave.

    Arguments:
      address: I2C slave address to target.
      register: I2C register to read.
      repeated_start: Use a repeated START.
    Return:
      Returned byte data.
    """
    return self.read(address, register, 1, repeated_start)[0]


class SpiDelegate(object):
  """Abstract base class for SPI master delegate class."""
  __metaclass__ = abc.ABCMeta

  @property
  @abc.abstractmethod
  def cpol(self):
    """Value of CPOL for this SPI bus."""

  @property
  @abc.abstractmethod
  def cpha(self):
    """Value of CPHA for this SPI bus."""

  @abc.abstractmethod
  def transfer(self, bus, write_data, num_bits=None):
    """Initiate a full duplex data transfer to an SPI slave.

    Note:
      This method will not initiate assertion of the SPI chip select line.
      It is up to the caller to perform the appropriate assertion and
      deassertion of that line.
    Args:
      bus: Index of bus for devices with multiple SPI buses.
      write_data: bytearray of data to write.
      num_bits: Number of bits to transfer. If None is specified then the
        number of bits is automatically calculated as the write_data
        length multiplied by 8.
    Returns:
      bytearray of returned data
    """

