islpy: Polyhedral Analysis from Python
======================================

.. image:: https://gitlab.tiker.net/inducer/islpy/badges/main/pipeline.svg
    :alt: Gitlab Build Status
    :target: https://gitlab.tiker.net/inducer/islpy/commits/main
.. image:: https://github.com/inducer/islpy/workflows/CI/badge.svg?branch=main&event=push
    :alt: Github Build Status
    :target: https://github.com/inducer/islpy/actions?query=branch%3Amain+workflow%3ACI+event%3Apush
.. image:: https://badge.fury.io/py/islpy.png
    :alt: Python Package Index Release Page
    :target: https://pypi.org/project/islpy/

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

*Requirements:* islpy needs a C++ compiler to build. GMP, which used to be
a dependency, is no longer required.
