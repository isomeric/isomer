Development Standards
=====================


We aim for the following development standards:


Cyclomatic Complexity
---------------------

- Code Complexity shall not exceed ``10``

  See: `Limiting Cyclomatic Complexity <http://en.wikipedia.org/wiki/Cyclomatic_complexity#Limiting_complexity_during_development>`_


Coding Style
------------

.. note:: We do accept "black" formatting.

- Code shall confirm to the `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`_ Style Guide.

- Doc Strings shall confirm to the `PEP257 <http://legacy.python.org/dev/peps/pep-0257/>`_ Convention.

.. note:: Arguments, Keyword Arguments, Return and Exceptions must be
  documented with the appropriate Sphinx `Python Domain <https://www.sphinx-doc.org/en/master/usage/restructuredtext/domains.html#the-python-domain>`_.


Revision History
----------------

- Commits shall be small tangible pieces of work.
  - Each commit must be concise and manageable.
  - Large changes are to be done over smaller commits.
- There shall be no commit squashing.
- Rebase your changes as often as you can.


Unit Tests
----------

- Every new feature and bug fix must be accompanied with a unit test.
  (*The only exception to this are minor trivial changes*).
