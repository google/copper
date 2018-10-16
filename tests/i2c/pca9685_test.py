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
from copper.i2c import pca9685

PCA9685_REGS = (
    'MODE1', 'MODE2', 'SUBADR1', 'SUBADR2', 'SUBADR3', 'PRESCALE',
    'LED0_ON_L', 'LED0_ON_H', 'LED0_OFF_L', 'LED0_OFF_H', 'ALL_LED_ON_L',
    'ALL_LED_ON_H', 'ALL_LED_OFF_L', 'ALL_LED_OFF_H')


class Pca9685Test(unittest.TestCase):

  def setUp(self):
    address = 0x48
    self.mock_i2c = MockI2cDelegate(address=address)
    self.dut = pca9685.Pca9685(i2c=self.mock_i2c, address=address)

  def test_init(self):
    self.assertEqual(self.mock_i2c.csr[pca9685.MODE1], 0x1,
                     'Expected MODE1 value of 0x1.')
    self.assertEqual(self.mock_i2c.csr[pca9685.MODE2], 0x4,
                     'Expected MODE2 value of 0x4.')

  def test_set_freq(self):
    self.dut.set_pwm_freq(60)
    self.assertEqual(self.mock_i2c.csr[pca9685.MODE1], 0x81,
                     'Expected MODE1 value of 0x81.')
    self.assertEqual(self.mock_i2c.csr[pca9685.PRESCALE], 0x65,
                     'Expected PRESCALE value of 0x65.')

  def test_set_pwm(self):
    for ch in range(16):
      on = ch + 250
      off = ch + 255
      self.dut.set_pwm(ch, on, off)
      reg = pca9685.LED0_ON_L + ch * 4
      on_lsb = self.mock_i2c.csr[reg]
      on_msb = self.mock_i2c.csr[reg + 1]
      off_lsb = self.mock_i2c.csr[reg + 2]
      off_msb = self.mock_i2c.csr[reg + 3]
      mock_on = (on_msb << 8) + on_lsb
      mock_off = (off_msb << 8) + off_lsb
      self.assertEqual(on, mock_on, 'Expected on time mismtach.')
      self.assertEqual(off, mock_off, 'Expected off time mismtach.')


class MockI2cDelegate(delegate.I2cDelegate):

  def __init__(self, address):
    self.address = address
    self.csr = dict(
        zip([getattr(pca9685, reg) for reg in PCA9685_REGS],
            [0] * len(PCA9685_REGS)))
    for idx in range(0x0A, 0x46):
      self.csr[idx] = 0

  def write(self, address, register, write_data):
    if address == self.address:
      if register not in self.csr:
        raise ValueError('Illegal register.')
      for idx, byte in enumerate(write_data):
        self.csr[register + idx] = byte

  def read(self, address, register, num_bytes, repeated_start=False):
    if address == self.address:
      if register not in self.csr:
        raise ValueError('Illegal register.')
      return bytearray([self.csr[register + idx] for idx in range(num_bytes)])


if __name__ == '__main__':
  unittest.main()
