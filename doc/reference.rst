Reference guide
===============

.. module:: islpy
.. moduleauthor:: Andreas Kloeckner <inform@tiker.net>

.. _gen-remarks:

General Remarks
^^^^^^^^^^^^^^^

Creation via Static Methods
---------------------------

To map more directly to the isl's C interface, object creation in :mod:`islpy`
is done through static methods instead of through constructors. These are
marked '(static)' in each class's overview section.

Documented vs. Non-documented Functionality
-------------------------------------------

Since :mod:`islpy` is automatically generated from the isl C headers, some of
the functionality it exposes might be undocumented. Undocumented functionality
might change or vanish without notice. 'Documented' functionality is defined as
whatever is mentioned in the `isl manual
<http://www.kotnet.org/~skimo/isl/user.html>`_. :mod:`islpy` will let you call
undocumented functions, but you are doing so at your own risk.

.. _auto-invalidation:

Invalidation of Arguments
-------------------------

You may notice that a few methods below say '(becomes invalid)'. This has to do
with an idiosyncrasy in isl's interface that was retained at the Python level
for efficiency. Such arguments will be deleted (by isl) upon entry to the
called function. If you would like to retain access to that object, simply
append a `.copy()` to that argument. (Note that you will notice if an object
got deleted for you accidentally, as the next operation on it will simply fail
with an exception.)

Integers
--------

Whenever an integer argument is required, :mod:`islpy` supports regular Python
integers, Python long integers, and :mod:`gmpy` integers. It will return
:mod:`gmpy` integers.

.. _automatic-casts:

Automatic Casts
---------------

:mod:`islpy` will automatically perform the following upward casts in argument
lists:

==================== ==========================
Called with          Argument Type
==================== ==========================
:class:`BasicSet`    :class:`Set`
:class:`BasicMap`    :class:`Map`
:class:`Set`         :class:`UnionSet`
:class:`Map`         :class:`UnionMap`
:class:`Space`       :class:`LocalSpace`
:class:`Aff`         :class:`PwAff`
==================== ==========================

as well as casts contained in the transitive closure of this 'casting graph'.

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

.. autoclass:: constants
    :members:
    :undoc-members:

Basic Building Blocks
^^^^^^^^^^^^^^^^^^^^^

Context
-------

.. class:: Context()

Space
-----

(formerly called :class:`Dim`. A compatibility alias is in place.)

.. autoclass:: Space
    :members:

Local Space
-----------

.. autoclass:: LocalSpace
    :members:

Constraints
-----------

.. autoclass:: Constraint
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

Quasi-Affine Expressions
^^^^^^^^^^^^^^^^^^^^^^^^

Quasi-Affine Expression
-----------------------

.. autoclass:: Aff
    :members:

Piecewise Quasi-Affine Expression
---------------------------------

.. autoclass:: PwAff
    :members:

Multiply Affine Expressions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Multiply Affine Expression
--------------------------

.. autoclass:: MultiAff
    :members:

Piecewise Multiply Affine Expression
------------------------------------

.. autoclass:: PwMultiAff
    :members:

Union of Piecewise Multiply Affine Expression
---------------------------------------------

.. autoclass:: UnionPwMultiAff
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

Restriction
-----------

.. autoclass:: Restriction
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

Helper functions
^^^^^^^^^^^^^^^^

.. autofunction:: align_spaces
.. autofunction:: align_two

.. vim: sw=4
