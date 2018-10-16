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

"""HTD21D module driver."""

import math
from copper import delegate


I2C_ADDR = 0x40

TRIGGER_TEMP_HOLD = 0xE3
TRIGGER_HUM_HOLD = 0xE5
TRIGGER_TEMP_NOHOLD = 0xF3
TRIGGER_HUM_NOHOLD = 0xF5
WRITE_USER = 0xE6
READ_USER = 0xE7
SOFT_RESET = 0xFE

# Partial pressure constants for dew point calculation
K_PP = dict(A=8.1332, B=1762.39, C=235.66)


class Htu21dException(Exception):
  """An exception type for HTU21D errorss."""


class Htu21d(object):
  """Interface to a HTD21D temperature and humidity sensor.

  Args:
    i2c: I/O delegate to proxy I2C commands through.
  """

  def __init__(self, i2c):
    super(Htu21d, self).__init__()

    if not isinstance(i2c, delegate.I2cDelegate):
      raise TypeError('I/O delegate does not implement I2C protocol.')

    self.i2c = i2c

  def validate_crc(self, msb, lsb, crc):
    """Validate the CRC for the incoming message.

    Args:
      msb: Most significant byte.
      lsb: Least significant byte.
      crc: Computed CRC-8 value.
    Raises:
      Htu21dException: When CRC check fails.
    """
    remainder = (((msb << 8) | lsb) << 8) | crc
    divsor = 0x988000

    for i in range(0, 16):
      if remainder & 1 << (23 - i):
        remainder ^= divsor
      divsor >>= 1

    if remainder != 0:
      raise Htu21dException('CRC Exception')

  def reset(self):
    """Issue a reset to the sensor."""
    self.i2c.write(I2C_ADDR, SOFT_RESET, bytearray([]))

  def read_temperature_register(self):
    """Reads the raw temperature from the sensor.

    Returns:
      The raw register value after triggering a temperature measurement.
    """
    msb, lsb, crc = self.i2c.read(I2C_ADDR, TRIGGER_TEMP_HOLD, 3)
    self.validate_crc(msb, lsb, crc)
    return ((msb << 8) + lsb) & 0xfffc

  def read_humidity_register(self):
    """Reads the raw relative humidity from the sensor.

    Returns:
      The raw register value after triggering a humidity measurement.
    """
    msb, lsb, crc = self.i2c.read(I2C_ADDR, TRIGGER_HUM_HOLD, 3)
    self.validate_crc(msb, lsb, crc)
    return ((msb << 8) + lsb) & 0xfffc

  @property
  def temperature(self):
    """Gets the temperature in degrees celsius."""
    return float(self.read_temperature_register()) / 65536 * 175.72 - 46.85

  @property
  def humidity(self):
    """Gets the relative humidity."""
    return max(0, float(self.read_humidity_register()) / 65536 * 125 - 6)

  @property
  def partial_pressure(self):
    """The current partial."""
    exponent = K_PP['A'] - K_PP['B'] / (self.temperature + K_PP['C'])
    return math.pow(10, exponent)

  @property
  def dewpoint(self):
    """The dew point temperature (in Celsius)."""
    ppressure = self.partial_pressure
    denominator = math.log10(self.humidity * ppressure / 100) - K_PP['A']
    return - (K_PP['B'] / denominator + K_PP['C'])

