#!/usr/bin/env python

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
"""Python setup file for copper module."""


from setuptools import setup

PKG_NAME = 'copper'
PKG_VERSION_MAJOR = 0
PKG_VERSION_MINOR = 9
PKG_VERSION_MICRO = 0
PKG_VERSION = '{major}.{minor}.{micro}'.format(
    major=PKG_VERSION_MAJOR,
    minor=PKG_VERSION_MINOR,
    micro=PKG_VERSION_MICRO)
PKG_DESC = 'Module for interacting with electromechanical systems.'

PKG_LONG_DESC = """
{pkg} is a Python module that provides low-level APIs for creating large
complex mechatronic systems. Devices may include electromechanical robotic
actuators, sensors, switches, or anything used in physical automation.
""".format(pkg=PKG_NAME)


def main():
  setup_data = dict(
      name=PKG_NAME,
      version=PKG_VERSION,
      packages=[PKG_NAME],
      description=PKG_DESC,
      long_description=PKG_LONG_DESC,
      license='Apache 2 license',
      platforms=['Linux', 'Darwin'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: Robot Framework :: Library',
          'Intended Audience :: Developers',
          'Intended Audience :: Manufacturing',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Telecommunications Industry',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Software Development',
          'Topic :: Software Development :: Embedded Systems',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Testing',
          'Topic :: System :: Hardware :: Hardware Drivers',
      ],
      install_requires=[
          'pyfirmata',
          'pylibftdi',
          'pyusb',
          'usbinfo>=1.1'
      ],
  )

  setup(**setup_data)


if __name__ == '__main__':
  main()
