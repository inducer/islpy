Welcome to islpy's documentation!
=================================

islpy is a Python wrapper around Sven Verdoolaege's `isl
<https://libisl.sourceforge.io/>`_, a library for manipulating sets and
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

Now you obviously want to watch the library do something (at least mildly)
cool? Well, sit back and watch:

.. literalinclude:: ../examples/demo.py
   :end-before: ENDEXAMPLE

This prints the following::

    set 1: { [x, y] : x >= 1 and x <= 5 and y >= 1 and y <= 5 }
    set 2: { [x, y] : x >= 0 and x <= 4 and y >= 0 and y <= 3 + x }
    union: { [x, y] : x >= 0 and y >= 0 and x <= 5 and y <= 3 + 2x and y >= -4 + x and y <= 15 - 2x and 3y <= 13 + 2x }

With some hacky plotting code (not shown), you can actually see what this
example just did. We gave it the two polyhedra on the left, asked it to compute
the union, and computed the convex hull:

+-------------------------------------+-------------------------------------+
| .. image:: images/before-union.png  | .. image:: images/after-union.png   |
+-------------------------------------+-------------------------------------+

See :download:`example/demo.py <../examples/demo.py>` to see the full example,
including the less-than-perfect plotting code. :)

Note that far better plotting of isl(py) sets is available by installing Tobias
Grosser's `islplot package <https://github.com/tobig/islplot>`_.

Overview
--------

This manual will not try to teach you much about the isl itself, it simply
lists, in a reference fashion, all the entrypoints available in :mod:`islpy`.
To get information on how to use the isl, see the real `isl manual
<https://libisl.sourceforge.io/manual.pdf>`_. The `manual
<http://barvinok.gforge.inria.fr/barvinok.pdf>`_ for the `barvinok
package <http://barvinok.gforge.inria.fr/>`_ is also quite helpful to get
an idea.

.. toctree::
    :maxdepth: 2

    misc
    reference
    ref_fundamental
    ref_expr
    ref_set
    ref_geo
    ref_ast
    ref_flow
    ref_schedule
    ref_containers
    🚀 Github <https://github.com/inducer/islpy>
    💾 Download Releases <https://pypi.python.org/pypi/islpy>

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

