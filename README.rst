islpy is a Python wrapper around Sven Verdoolaege's `isl
<http://www.kotnet.org/~skimo/isl/>`_, a library for manipulating sets and
relations of integer points bounded by linear constraints.

Supported operations on sets include

* intersection, union, set difference,
* emptiness check,
* convex hull,
* (integer) affine hull,
* integer projection,
* computing the lexicographic minimum using parametric integer programming,
* coalescing, and
* parametric vertex enumeration.

It also includes an ILP solver based on generalized basis reduction, transitive
closures on maps (which may encode infinite graphs), dependence analysis and
bounds on piecewise step-polynomials.

Islpy comes with comprehensive `documentation <http://documen.tician.de/islpy>`_.

*Requirements:* Only the `GNU Multiprecision Library <http://gmplib.org/>`_
and its Python wrapper `gmpy <https://code.google.com/p/gmpy/>`_ (Version 1.x)
are required. A version of isl is shipped with islpy, but optionally
a system-wide one may also be used.

