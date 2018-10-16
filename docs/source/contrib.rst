.. _contributing:

Contributor Guide
=================

This part of the documentation focuses on allowing users to contribute new
modules to the Copper library. Copper is designed as a living and growing
library of hardware abstractions built from community contributions.

.. _philosophy:

Development Philosophy
----------------------

Copper was designed around the :pep:`20` philosphy.

#. Beautiful is better than ugly.
#. Explicit is better than implicit.
#. Simple is better than complex.
#. Complex is better than complicated.
#. Readability counts.
#. If the implementation is hard to explain, it's a bad idea. If the
   implementation is easy to explain, it may be a good idea.

In addition, we believe in many design values espoused by Don Norman. A
software API is much like a user interface for developers so we think that
many of the same principles apply. A good API should be stylistically
consistent. It should be obvious what each part of an API affords without
the need to consult documentation or requiring the user to understand the
implementation of that API. Moreover, a good API should not carry unnecessary
functionality or have any hidden side effects.

All contributions to Copper should keep these in mind.

.. _coding_standards:

Coding Standards
----------------

Copper generally follows :pep:`8` with a few additions and exceptions:

* Each indentation level is 2 spaces to help avoid exceeding the 79 character
  limit. This will require a change to your editor settings if your editor
  automatically indents Python.
* Use parentheses instead of a continuation ``\`` when exceeding the line
  limit.
* Avoid using ``logging`` unless it is suppressed by default. Logging within
  low-level code has the potential to inundate the console with excessive
  information that many users may not want.
* Always use single-quoted strings unless you absolutely need to.
* Never directly reference any file path or designator that only exists in
  your personal setup. For example, references to character device files like
  ``/dev/ttyACM0`` may refer to something different on someone else's setup
  than it does on yours.

.. _github:

Code Contributions
------------------

When contributing to Copper, you will want to follow these steps:

#. Add a new issue on GitHub.
#. Fork the repository on GitHub.
#. Write tests that validate your changes.
#. Make your change.
#. Run all tests and confirm that they pass.
#. Send a GitHub Pull Request to Copper's ``master`` branch.
