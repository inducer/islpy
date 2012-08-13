Obtaining :mod:`islpy`
======================

islpy may be downloaded from the page for `islpy at the Python package index
<http://pypi.python.org/pypi/islpy>`_.

You may also clone its git repository::

    git clone http://git.tiker.net/trees/islpy.git
    git clone git://github.com/inducer/islpy

Wiki, FAQ, Installation Instructions
====================================

A `wiki page <http://wiki.tiker.net/IslPy>`_ is also available, where install
instructions and an FAQ will grow over time.

For a mailing list, please consider using the `isl list
<http://groups.google.com/group/isl-development>`_ until they tell us to get
lost.

Licensing
=========

islpy is licensed to you under the MIT/X Consortium license:

Copyright (c) 2011 Andreas Klöckner and Contributors.

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

.. note::

    The isl itself is licensed under the `Lesser GPL
    <https://secure.wikimedia.org/wikipedia/en/wiki/GNU_Lesser_General_Public_License>`_.
    The license above applies only to the wrapping code.


Relation with isl's C interface
===============================

Nearly all of the bindings to isl are auto-generated, using the following
rules:

* Follow :pep:`8`.
* Expose the underlying object-oriented structure.
* Remove the `isl_` and `ISL_` prefixes from data types, macros and
  function names, replace them with Python namespaces.
* A method `isl_printer_print_set` would thus become
  :meth:`islpy.Printer.print_set`.

See also :ref:`gen-remarks`.

User-visible Changes
====================

Version 2012.1
--------------

.. note::

    This version is currently in development and can be obtained from
    islpy's version control.

Version 2011.3
--------------

* Add :meth:`islpy.Set.project_out_except` and friends.
* Add :meth:`islpy.Set.remove_divs_of_dim_type` and friends.
* :class:`islpy.Dim` was renamed to :class:`islpy.Space` in isl.
* :class:`islpy.Div` was removed and replaced by :class:`islpy.Aff`
  wherever it was used previously.
* :meth:`islpy.BasicSet.as_set`
  and
  :meth:`islpy.BasicMap.as_map`
  were removed.
* :ref:`automatic-casts` were added.
* Support for more Python :class:`set`-like behavior was added. In particular,
  the operators `|`, `&', '-', `<`, `<=`, `>`, `>=`, `==`, `!=` work as expected.
* Support direct construction from string for objects that have a `read_from_str`
  method.
* The constant in a :class:`islpy.Constraint` is now set as the '1'
  key in a coefficient dictionary in
  :meth:`islpy.Constraint.eq_from_names`,
  :meth:`islpy.Constraint.ineq_from_names`, and
  :meth:`islpy.Constraint.set_coefficients_by_name`.

Version 2011.2
--------------

* Switch to copy-by-default semantics.
* A few changes in Python-side functionality.
* Automatic type promotion in 'self' argument.

Version 2011.1
--------------

* Initial release.
