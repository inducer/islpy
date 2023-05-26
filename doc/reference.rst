Reference guide: Overview
=========================

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
integers and Python :class:`long` integers. It will return Python long integers.

.. _automatic-casts:

Automatic Casts
---------------

:mod:`islpy` will automatically perform the following upward casts in argument
lists:

==================== ==========================
Called with          Argument Type
==================== ==========================
:class:`BasicSet`    :class:`Set`
:class:`Set`         :class:`UnionSet`
:class:`BasicMap`    :class:`Map`
:class:`Map`         :class:`UnionMap`
:class:`Aff`         :class:`PwAff`
:class:`PwAff`       :class:`UnionPwAff`
:class:`MultiAff`    :class:`PwMultiAff`
:class:`PwMultiAff`  :class:`UnionPwMultiAff`
:class:`Space`       :class:`LocalSpace`
==================== ==========================

as well as casts contained in the transitive closure of this 'casting graph'.

Error Reporting
---------------

.. exception:: Error

Convenience
^^^^^^^^^^^

.. autofunction:: make_zero_and_vars

.. autofunction:: affs_from_space


Lifetime Helpers
^^^^^^^^^^^^^^^^

.. class:: ffi_callback_handle

    Some callbacks, notably those in :class:`AstBuild`, need to outlive the
    function call to which they're passed. These callback return a callback
    handle that must be kept alive until the callback is no longer needed.

Global Data
^^^^^^^^^^^

.. data:: DEFAULT_CONTEXT

    ISL objects being unpickled or initialized from strings will be instantiated
    within this :class:`Context`.

    .. versionadded:: 2015.2

Symbolic Constants
^^^^^^^^^^^^^^^^^^

.. autoclass:: error
    :members:
    :undoc-members:
    :exclude-members: names, values, @entries

.. autoclass:: dim_type
    :members:
    :undoc-members:
    :exclude-members: names, values, @entries

.. autoclass:: fold
    :members:
    :undoc-members:
    :exclude-members: names, values, @entries

.. autoclass:: format
    :members:
    :undoc-members: @entries

.. autoclass:: yaml_style
    :members:
    :undoc-members: @entries

Output
^^^^^^

.. autoclass:: Printer
    :members:

Helper functions
^^^^^^^^^^^^^^^^

.. autofunction:: align_spaces
.. autofunction:: align_two

Canonical Names for Internal Module
-----------------------------------

.. ::

   This should switch to using ``:canonical:`` once Sphinx 4.0 is released.

.. currentmodule:: islpy._isl

.. class:: stat

    A status result.

.. class:: error

    See :class:`islpy.error`.

.. class:: dim_type

    See :class:`islpy.dim_type`.

.. class:: fold

    See :class:`islpy.fold`.

.. class:: format

    See :class:`islpy.format`.

.. class:: yaml_style

    See :class:`islpy.yaml_style`.

.. class:: Printer

    See :class:`islpy.Printer`.

.. vim: sw=4
