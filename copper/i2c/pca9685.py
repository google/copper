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

"""PCA9685 module driver."""
import math
import time
from copper import delegate


MODE1 = 0x00
MODE2 = 0x01
SUBADR1 = 0x02
SUBADR2 = 0x03
SUBADR3 = 0x04
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

MODE1_RESTART = 0x80
MODE1_SLEEP = 0x10
MODE1_ALLCALL = 0x01
MODE2_INVRT = 0x10
MODE2_OUTDRV = 0x04


class Pca9685(object):
  """Interface to a PCA9685 PWM controller.

  Args:
    i2c: I/O delegate to proxy I2C commands through.
    address: Lower 6-bits slave address based on pin straps A5 to A0.
  """

  def __init__(self, i2c, address):
    super(Pca9685, self).__init__()

    if not isinstance(i2c, delegate.I2cDelegate):
      raise TypeError('I/O delegate does not implement I2C protocol.')

    self._i2c = i2c
    self._address = (address & 0x3f) + 0x40

    self._i2c.write8(self._address, MODE2, MODE2_OUTDRV)
    self._i2c.write8(self._address, MODE1, MODE1_ALLCALL)
    time.sleep(0.005)
    mode1 = self._i2c.read8(self._address, MODE1)
    mode1 &= ~MODE1_SLEEP
    self._i2c.write8(self._address, MODE1, mode1)

  def set_pwm_freq(self, freq_hz):
    """Sets the PWM frequency to the provided value in hertz.

    Args:
      freq_hz: PWM frequency in Hz
    """
    prescaleval = (25000000. / 4096.) / float(freq_hz) - 1.0
    prescale = int(math.floor(prescaleval + 0.5))
    oldmode = self._i2c.read8(self._address, MODE1)
    newmode = (oldmode & 0x7F) | 0x10
    self._i2c.write8(self._address, MODE1, newmode)
    self._i2c.write8(self._address, PRESCALE, prescale)
    self._i2c.write8(self._address, MODE1, oldmode)
    time.sleep(0.005)
    self._i2c.write8(self._address, MODE1, oldmode | 0x80)

  def set_pwm(self, channel, on, off):
    """Sets the ON and OFF transition times (out of 4095) for the PWM channel.

    Args:
      channel: Channel to set
      on: On transition time
      off: Off transition time
    Raises:
      ValueError: When arguments are out of range.
    """
    if channel < 0 or channel > 15:
      raise ValueError('PCA9685 channel should be between 0 and 15.')
    if on < 0 or on > 4095:
      raise ValueError('PCA9685 on time should be between 0 and 4095.')
    if off < 0 or off > 4095:
      raise ValueError('PCA9685 on time should be between 0 and 4095.')
    self._i2c.write8(self._address, LED0_ON_L + 4 * channel, on & 0xFF)
    self._i2c.write8(self._address, LED0_ON_H + 4 * channel, on >> 8)
    self._i2c.write8(self._address, LED0_OFF_L + 4 * channel, off & 0xFF)
    self._i2c.write8(self._address, LED0_OFF_H + 4 * channel, off >> 8)

  def set_pwm_duty(self, channel, duty):
    """Sets the duty cycle of a particular channel as fraction.

    Sets the PWM on and off cycles by fixing the on time to 0 and the off
    time that results in the duty fractional amount.

    Args:
      channel: Channel to set.
      duty: Duty fraction of PWM.
    """
    self.set_pwm(channel, 0, int(duty * 4095))
