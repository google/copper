Python Copper
=============

**Copper** is a module aimed at providing low-level hardware abstraction
layers (HAL) as Python modules. Copper aims to create a simple and well
designed API that will allow engineers with a diversity of skill sets and
skill levels to develop complex eletromechanical systems from common
off-the-shelf components.

-------------------

**Be lazy like a fox: control hardware with readable code.**

.. code-block:: python

    >>> from copper.usb import firmata
    >>> from copper.i2c import pca9685
    >>> uno = firmata.ArduinoUno('95530343434351A002E0')
    >>> uno.i2c_enable()
    >>> servo = pca9685.Pca9685(i2c=uno.i2c, address=0x40)
    >>> servo.set_pwm_duty(channel=0, duty=0.8)

.. toctree::
   :maxdepth: 2

   intro
   user
   contrib

History
-------

Version 0.9
```````````

* Initial version.
* Support for USB devices:

  * Arduino Uno, Mega, and Due running StandardFirmata.
  * FTDI serial devices (not using D2XX or MPSSE).
  * ChromiumOS Tigertail USB-C multiplexor.

* Support for I²C components:

  * PCA9685 PWM controller.
  * HTU21D temperature and humidity sensor.

License
-------

Copyright 2018 Google Inc. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
