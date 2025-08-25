islpy: Polyhedral Analysis from Python
======================================

.. image:: https://gitlab.tiker.net/inducer/islpy/badges/main/pipeline.svg
    :alt: Gitlab Build Status
    :target: https://gitlab.tiker.net/inducer/islpy/commits/main
.. image:: https://github.com/inducer/islpy/actions/workflows/ci.yml/badge.svg
    :alt: Github Build Status
    :target: https://github.com/inducer/islpy/actions/workflows/ci.yml
.. image:: https://badge.fury.io/py/islpy.svg
    :alt: Python Package Index Release Page
    :target: https://pypi.org/project/islpy/
.. image:: https://zenodo.org/badge/2021524.svg
    :alt: Zenodo DOI for latest release
    :target: https://zenodo.org/badge/latestdoi/2021524

islpy is a Python wrapper around Sven Verdoolaege's `isl
<https://libisl.sourceforge.io/>`__, a library for manipulating sets and
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

Islpy comes with comprehensive `documentation <http://documen.tician.de/islpy>`__.

*Requirements:* islpy needs a C++ compiler to build. It can optionally make use
of GMP for support of large integers.

One important thing to know about islpy is that it exposes every function in isl
that is visible in the headers, not just what isl's authors consider its
documented, public API (marked by ``__isl_export``). These (technically)
undocumented functions are marked in the islpy documentation. Many of them are useful
and essential for certain operations, but isl's API stability guarantees do not
apply to them. Use them at your own risk.

Islpy can optionally be built with support for `barvinok <https://repo.or.cz/barvinok.git>`__,
a library for counting the number of integer points in parametric and non-parametric
polytopes. Notably, unlike isl, barvinok is GPL-licensed, so doing so changes
islpy's effective license as well. In addition to islpy's `regular PyPI source
and binary wheel downloads <https://pypi.org/project/islpy/>`__, `Cambridge Yang
<https://github.com/thisiscam>`__ has made available a `package with wheels that
include Barvinok <https://pypi.org/project/islpy-barvinok/>`__.

