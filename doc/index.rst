Welcome to islpy's documentation!
=================================

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

Now you obviously want to watch the library do something (at least mildly)
cool? Well, sit back and watch::

    import islpy as isl

    ctx = isl.Context()
    space = isl.Space.create_from_names(ctx, set=["x", "y"])

    bset = (isl.BasicSet.universe(space)
            .add_constraint(isl.Constraint.ineq_from_names(space, {1: -1, "x":1}))
            .add_constraint(isl.Constraint.ineq_from_names(space, {1: 5, "x":-1}))
            .add_constraint(isl.Constraint.ineq_from_names(space, {1: -1, "y": 1}))
            .add_constraint(isl.Constraint.ineq_from_names(space, {1: 5, "y": -1})))
    print "set 1:", bset

    bset2 = isl.BasicSet("{[x, y] : x >= 0 and x < 5 and y >= 0 and y < x+4 }")
    print "set 2:", bset2

    bsets_in_union = []
    bset.union(bset2).coalesce().foreach_basic_set(bsets_in_union.append)
    union, = bsets_in_union
    print "union:", union

This prints the following::

    set 1: { [x, y] : x >= 1 and x <= 5 and y >= 1 and y <= 5 }
    set 2: { [x, y] : x >= 0 and x <= 4 and y >= 0 and y <= 3 + x }
    union: { [x, y] : x >= 0 and y >= 0 and x <= 5 and y <= 3 + 2x and y >= -4 + x and y <= 15 - 2x and 3y <= 13 + 2x }

With some hacky plotting code (not shown), you can actually see what this
example just did. We gave it the two polyhedra on the left, asked it to compute
the union, and furthermore to try and coalesce this union back into a basic
polyhedron:

+-------------------------------------+-------------------------------------+
| .. image:: images/before-union.png  | .. image:: images/after-union.png   |
+-------------------------------------+-------------------------------------+

You can convince yourself by looking at the grid intersections that indeed no
integer points were added to the polyhedron during this process.  (A "basic
polyhedron", really an :class:`islpy.BasicSet`, is expressible through a
conjunction of constraints.)

See :file:`example/demo.py` to see the full example, including the less-than-perfect
plotting code. :)

Overview
--------

This manual will not try to teach you much about the isl itself, it simply
lists, in a reference fashion, all the entrypoints available in :mod:`islpy`.
To get information on how to use the isl, see the real `isl manual
<http://www.kotnet.org/~skimo/isl/manual.pdf>`_. The `manual
<http://www.kotnet.org/~skimo/barvinok/barvinok.pdf>`_ for the `barvinok
package <http://www.kotnet.org/~skimo/barvinok/>`_ is also quite helpful to get
an idea.

.. toctree::
    :maxdepth: 3

    misc
    reference

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

