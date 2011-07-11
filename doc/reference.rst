Reference guide
===============

.. module:: islpy
.. moduleauthor:: Andreas Kloeckner <inform@tiker.net>

General Remarks
^^^^^^^^^^^^^^^

.. _auto-invalidation:

Invalidation of Arguments
-------------------------

You may notice that many methods below say '(becomes invalid)'. This has to do
with an idiosyncrasy in isl's interface that was retained at the Python level
for efficiency. Such arguments will be deleted (by isl) upon entry to the
called function. If you would like to retain access to that object, simply
append a `.copy()` to that argument. (Note that you will notice if an object
got deleted for you accidentally, as the next operation on it will simply fail
with an exception.

Symbolic Constants
^^^^^^^^^^^^^^^^^^

.. autoclass:: format
    :members:
    :undoc-members:

.. autoclass:: error
    :members:
    :undoc-members:
    :exclude-members: names, values

.. autoclass:: dim_type
    :members:
    :undoc-members:
    :exclude-members: names, values

.. autoclass:: fold
    :members:
    :undoc-members:
    :exclude-members: names, values


Basic Building Blocks
^^^^^^^^^^^^^^^^^^^^^

Context
-------

.. class:: Context()

Dim
---

.. autoclass:: Dim
    :members:

Local Space
-----------

.. autoclass:: LocalSpace
    :members:

Constraints
-----------

.. autoclass:: Constraint
    :members:

Existentially Quantified Variables
----------------------------------

.. autoclass:: Div
    :members:

Vector
------

.. autoclass:: Vec
    :members:

Matrix
------

.. autoclass:: Mat
    :members:

Sets and Maps
^^^^^^^^^^^^^

Basic Set
---------

.. autoclass:: BasicSet
    :members:

Basic Map
---------

.. autoclass:: BasicMap
    :members:

Set
---

.. autoclass:: Set
    :members:

Map
---

.. autoclass:: Map
    :members:

Union Set
---------

.. autoclass:: UnionSet
    :members:

Union Map
---------

.. autoclass:: UnionMap
    :members:

Geometric Entities
^^^^^^^^^^^^^^^^^^

Point
-----

.. autoclass:: Point
    :members:

Vertex
------

.. autoclass:: Vertex
    :members:

Vertices
--------

.. autoclass:: Vertices
    :members:

Cell
----

.. autoclass:: Cell
    :members:

Quasi Affine Expressions
^^^^^^^^^^^^^^^^^^^^^^^^

Quasi Affine Expression
-----------------------

.. autoclass:: Aff
    :members:

Piecewise Quasi Affine Expression
---------------------------------

.. autoclass:: PwAff
    :members:

Quasipolynomials
^^^^^^^^^^^^^^^^

QPolynomial
-----------

.. autoclass:: QPolynomial
    :members:

PwQPolynomial
-------------

.. autoclass:: PwQPolynomial
    :members:

UnionPwQPolynomial
------------------

.. autoclass:: UnionPwQPolynomial
    :members:

QPolynomialFold
---------------

.. autoclass:: QPolynomialFold
    :members:

PwQPolynomial
-------------

.. autoclass:: PwQPolynomialFold
    :members:

UnionPwQPolynomialFold
----------------------

.. autoclass:: UnionPwQPolynomialFold
    :members:

Scheduling
^^^^^^^^^^

Band
----

.. autoclass:: Band
    :members:

Schedule
--------

.. autoclass:: Schedule
    :members:

Dataflow
^^^^^^^^

Access Info
-----------

.. autoclass:: AccessInfo
    :members:

Flow
----

.. autoclass:: Flow
    :members:

Lists
^^^^^

.. autoclass:: BasicSetList
    :members:

.. autoclass:: SetList
    :members:

.. autoclass:: AffList
    :members:

.. autoclass:: BandList
    :members:

Output
^^^^^^

.. autoclass:: Printer
    :members:

.. vim: sw=4
