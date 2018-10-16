.. _intro:

Introduction
============

Copper was borne out of the desire to develop complex hardware systems using
using common off-the-shelf components while using Python as the language to
drive complex business logic. Such a system is common in hardware test
automation, autonomous vehicles, manufacturing stations, and other robotic
applications.

At the time of its inception, many solutions exist for individual components
but none share a common API theme with each other. The Copper effort attempts
to bring all of these under one effort with a single consistent API style
with interfaces for protocol delegation.

The focus of Copper is good API by design. An API should be simple and
consistent. Their affordances should be obvious--a class named ``Htu21d``,
for example, should have methods for interacting with a HTU21D temperature
and humidity sensor and nothing else. There should be simple and obvious
methods and properties such as ``temperature`` and ``humidity`` for this
particular example.
