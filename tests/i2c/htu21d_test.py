# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from copper import delegate
from copper.i2c import htu21d


class Htu21dTest(unittest.TestCase):

  def setUp(self):
    self.mock_i2c = MockI2cDelegate()
    self.dut = htu21d.Htu21d(i2c=self.mock_i2c)

  def test_temperature_normal(self):
    read_queue = self.mock_i2c.read_queue[htu21d.TRIGGER_TEMP_HOLD]
    read_queue.append(bytearray(b'\00\00\00'))
    expected_temperature = -46.85
    try:
      actual_temperature = self.dut.temperature
    except htu21d.Htu21dException:
      actual_temperature = None
    self.assertIsNotNone(actual_temperature, 'Unexpected CRC error.')
    self.assertLess(abs(expected_temperature - actual_temperature), 0.01,
                    'Expected temperature {} but got {}.'.format(
                        expected_temperature, actual_temperature))

  def test_temperature_crc_error(self):
    read_queue = self.mock_i2c.read_queue[htu21d.TRIGGER_TEMP_HOLD]
    for crc in range(1, 256):
      ba = bytearray(3)
      ba[2] = crc
      read_queue.append(ba)
      try:
        temperature = self.dut.temperature
      except htu21d.Htu21dException:
        temperature = None
      self.assertIsNone(temperature, 'Expected CRC error.')

  def test_humidity_normal(self):
    read_queue = self.mock_i2c.read_queue[htu21d.TRIGGER_HUM_HOLD]
    read_queue.append(bytearray(b'\00\00\00'))
    expected_humidity = 0.0
    try:
      actual_humidity = self.dut.humidity
    except htu21d.Htu21dException:
      actual_humidity = None
    self.assertIsNotNone(actual_humidity, 'Unexpected CRC error.')
    self.assertLess(abs(expected_humidity - actual_humidity), 0.01,
                    'Expected humidity {} but got {}.'.format(
                        expected_humidity, actual_humidity))

  def test_humidity_crc_error(self):
    read_queue = self.mock_i2c.read_queue[htu21d.TRIGGER_HUM_HOLD]
    for crc in range(1, 256):
      ba = bytearray(3)
      ba[2] = crc
      read_queue.append(ba)
      try:
        humidity = self.dut.humidity
      except htu21d.Htu21dException:
        humidity = None
      self.assertIsNone(humidity, 'Expected CRC error.')

  def test_reset(self):
    self.dut.reset()
    last_write = self.mock_i2c.write_history.pop(0)
    self.assertEqual(last_write, bytearray(b'\xfe'),
                     'Last write {} differs from "\xfe".'.format(last_write))


class MockI2cDelegate(delegate.I2cDelegate):

  def __init__(self):
    self.write_history = []
    self.read_queue = {
        htu21d.TRIGGER_TEMP_HOLD: list(),
        htu21d.TRIGGER_HUM_HOLD: list(),
        htu21d.TRIGGER_TEMP_NOHOLD: list(),
        htu21d.TRIGGER_HUM_NOHOLD: list(),
        htu21d.WRITE_USER: list(),
        htu21d.READ_USER: list(),
        htu21d.SOFT_RESET: list(),
    }
    self.registers = self.read_queue.keys()

  def write(self, address, register, write_data):
    if address == htu21d.I2C_ADDR:
      if register not in self.registers:
        raise ValueError('Illegal register.')
      self.write_history.append(bytearray([register]) + write_data)

  def read(self, address, register, num_bytes, repeated_start=False):
    if address == htu21d.I2C_ADDR:
      if register not in self.registers:
        raise ValueError('Illegal register.')
      return self.read_queue[register].pop(0)


if __name__ == '__main__':
  unittest.main()
