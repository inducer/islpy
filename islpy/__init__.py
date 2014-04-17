from __future__ import division


from islpy._isl import *  # noqa
from islpy.version import *  # noqa


_CHECK_DIM_TYPES = [
        dim_type.in_, dim_type.param, dim_type.set]

ALL_CLASSES = tuple(getattr(_isl, cls) for cls in dir(_isl) if cls[0].isupper())
EXPR_CLASSES = tuple(cls for cls in ALL_CLASSES
        if "Aff" in cls.__name__ or "Polynomial" in cls.__name__)

_DEFAULT_CONTEXT = Context()


def _add_functionality():
    import islpy._isl as _isl  # noqa

    # {{{ generic initialization, pickling

    def obj_new_from_string(cls, s, context=None):
        """Construct a new object from :class:`str` s.

        :arg context: a :class:`islpy.Context` to use. If not supplied, use a
            global default context.
        """

        if context is None:
            context = _DEFAULT_CONTEXT

        result = cls.read_from_str(context, s)
        result._made_from_string = True
        return result

    def obj_bogus_init(self, s, context=None):
        assert self._made_from_string
        del self._made_from_string

    def generic_getinitargs(self):
        prn = Printer.to_str(self.get_ctx())
        getattr(prn, "print_"+self._base_name)(self)
        return (prn.get_str(),)

    for cls in ALL_CLASSES:
        if hasattr(cls, "read_from_str"):
            cls.__new__ = staticmethod(obj_new_from_string)
            cls.__init__ = obj_bogus_init
            cls.__getinitargs__ = generic_getinitargs

    # }}}

    # {{{ printing

    def generic_str(self):
        prn = Printer.to_str(self.get_ctx())
        getattr(prn, "print_"+self._base_name)(self)
        return prn.get_str()

    def generic_repr(self):
        prn = Printer.to_str(self.get_ctx())
        getattr(prn, "print_"+self._base_name)(self)
        return "%s(\"%s\")" % (
                type(self).__name__, prn.get_str())

    for cls in ALL_CLASSES:
        if hasattr(cls, "_base_name") and hasattr(Printer, "print_"+cls._base_name):
            cls.__str__ = generic_str
            cls.__repr__ = generic_repr

    # }}}

    # {{{ rich comparisons

    def obj_eq(self, other):
        return self.is_equal(other)

    def obj_ne(self, other):
        return not self.is_equal(other)

    for cls in ALL_CLASSES:
        if hasattr(cls, "is_equal"):
            cls.__eq__ = obj_eq
            cls.__ne__ = obj_ne

    def obj_lt(self, other):
        return self.is_strict_subset(other)

    def obj_le(self, other):
        return self.is_subset(other)

    def obj_gt(self, other):
        return other.is_strict_subset(self)

    def obj_ge(self, other):
        return other.is_subset(self)

    for cls in [BasicSet, BasicMap, Set, Map]:
        cls.__lt__ = obj_lt
        cls.__le__ = obj_le
        cls.__gt__ = obj_gt
        cls.__ge__ = obj_ge

    # }}}

    # {{{ Python set-like behavior

    def obj_or(self, other):
        try:
            return self.union(other)
        except TypeError:
            return NotImplemented

    def obj_and(self, other):
        try:
            return self.intersect(other)
        except TypeError:
            return NotImplemented

    def obj_sub(self, other):
        try:
            return self.subtract(other)
        except TypeError:
            return NotImplemented

    for cls in [BasicSet, BasicMap, Set, Map]:
        cls.__or__ = obj_or
        cls.__ror__ = obj_or
        cls.__and__ = obj_and
        cls.__rand__ = obj_and
        cls.__sub__ = obj_sub

    #}}}

    # {{{ Space

    def space_get_id_dict(self, dimtype=None):
        """Return a dictionary mapping variable :class:`Id` instances to tuples
        of (:class:`dim_type`, index).

        :param dimtype: None to get all variables, otherwise
            one of :class:`dim_type`.
        """
        result = {}

        def set_dim_id(name, tp, idx):
            if name in result:
                raise RuntimeError("non-unique var id '%s' encountered" % name)
            result[name] = tp, idx

        if dimtype is None:
            types = _CHECK_DIM_TYPES
        else:
            types = [dimtype]

        for tp in types:
            for i in range(self.dim(tp)):
                name = self.get_dim_id(tp, i)
                if name is not None:
                    set_dim_id(name, tp, i)

        return result

    def space_get_var_dict(self, dimtype=None):
        """Return a dictionary mapping variable names to tuples of
        (:class:`dim_type`, index).

        :param dimtype: None to get all variables, otherwise
            one of :class:`dim_type`.
        """
        result = {}

        def set_dim_name(name, tp, idx):
            if name in result:
                raise RuntimeError("non-unique var name '%s' encountered" % name)
            result[name] = tp, idx

        if dimtype is None:
            types = _CHECK_DIM_TYPES
        else:
            types = [dimtype]

        for tp in types:
            for i in range(self.dim(tp)):
                name = self.get_dim_name(tp, i)
                if name is not None:
                    set_dim_name(name, tp, i)

        return result

    def space_create_from_names(ctx, set=None, in_=None, out=None, params=[]):
        """Create a :class:`Space` from lists of variable names.

        :param set_: names of `set`-type variables.
        :param in_: names of `in`-type variables.
        :param out: names of `out`-type variables.
        :param params`: names of parameter-type variables.
        """
        dt = dim_type

        if set is not None:
            if in_ is not None or out is not None:
                raise RuntimeError("must pass only one of set / (in_,out)")

            result = Space.set_alloc(ctx, nparam=len(params),
                    dim=len(set))

            for i, name in enumerate(set):
                result = result.set_dim_name(dt.set, i, name)

        elif in_ is not None and out is not None:
            if set is not None:
                raise RuntimeError("must pass only one of set / (in_,out)")

            result = Space.alloc(ctx, nparam=len(params),
                    n_in=len(in_), n_out=len(out))

            for i, name in enumerate(in_):
                result = result.set_dim_name(dt.in_, i, name)

            for i, name in enumerate(out):
                result = result.set_dim_name(dt.out, i, name)
        else:
            raise RuntimeError("invalid parameter combination")

        for i, name in enumerate(params):
            result = result.set_dim_name(dt.param, i, name)

        return result

    Space.create_from_names = staticmethod(space_create_from_names)
    Space.get_var_dict = space_get_var_dict
    Space.get_id_dict = space_get_id_dict

    # }}}

    # {{{ coefficient wrangling

    def obj_set_coefficients(self, dim_tp, args):
        """
        :param dim_tp: :class:`dim_type`
        :param args: :class:`list` of coefficients, for indices `0..len(args)-1`.

        .. versionchanged:: 2011.3
            New for :class:`Aff`
        """
        for i, coeff in enumerate(args):
            self = self.set_coefficient_val(dim_tp, i, coeff)

        return self

    def obj_set_coefficients_by_name(self, iterable, name_to_dim=None):
        """Set the coefficients and the constant.

        :param iterable: a :class:`dict` or iterable of :class:`tuple`
            instances mapping variable names to their coefficients.
            The constant is set to the value of the key '1'.

        .. versionchanged:: 2011.3
            New for :class:`Aff`
        """
        try:
            iterable = iterable.items()
        except AttributeError:
            pass

        if name_to_dim is None:
            name_to_dim = self.get_space().get_var_dict()

        for name, coeff in iterable:
            if name == 1:
                self = self.set_constant_val(coeff)
            else:
                tp, idx = name_to_dim[name]
                self = self.set_coefficient_val(tp, idx, coeff)

        return self

    def obj_get_coefficients_by_name(self, dimtype=None, dim_to_name=None):
        """Return a dictionary mapping variable names to coefficients.

        :param dimtype: None to get all variables, otherwise
            one of :class:`dim_type`.

        .. versionchanged:: 2011.3
            New for :class:`Aff`
        """
        if dimtype is None:
            types = _CHECK_DIM_TYPES
        else:
            types = [dimtype]

        result = {}
        for tp in types:
            for i in range(self.get_space().dim(tp)):
                coeff = self.get_coefficient(tp, i)
                if coeff:
                    if dim_to_name is None:
                        name = self.get_dim_name(tp, i)
                    else:
                        name = dim_to_name[(tp, i)]

                    result[name] = coeff

        const = self.get_constant()
        if const:
            result[1] = const

        return result

    for coeff_class in [Constraint, Aff]:
        coeff_class.set_coefficients = obj_set_coefficients
        coeff_class.set_coefficients_by_name = obj_set_coefficients_by_name
        coeff_class.get_coefficients_by_name = obj_get_coefficients_by_name

    # }}}

    # {{{ Id

    def id_new(cls, name, user=None, context=None):
        if context is None:
            context = _DEFAULT_CONTEXT

        result = cls.alloc(context, name, user)
        result._made_from_python = True
        return result

    def id_bogus_init(self, name, user=None, context=None):
        assert self._made_from_python
        del self._made_from_python

    Id.__new__ = staticmethod(id_new)
    Id.__init__ = id_bogus_init
    Id.user = property(Id.get_user)
    Id.name = property(Id.get_name)

    # }}}

    # {{{ Constraint

    def eq_from_names(space, coefficients={}):
        """Create a constraint `const + coeff_1*var_1 +... == 0`.

        :param space: :class:`Space`
        :param coefficients: a :class:`dict` or iterable of :class:`tuple`
            instances mapping variable names to their coefficients
            The constant is set to the value of the key '1'.

        .. versionchanged:: 2011.3
            Eliminated the separate *const* parameter.
        """
        c = Constraint.equality_alloc(space)
        return c.set_coefficients_by_name(coefficients)

    def ineq_from_names(space, coefficients={}):
        """Create a constraint `const + coeff_1*var_1 +... >= 0`.

        :param space: :class:`Space`
        :param coefficients: a :class:`dict` or iterable of :class:`tuple`
            instances mapping variable names to their coefficients
            The constant is set to the value of the key '1'.

        .. versionchanged:: 2011.3
            Eliminated the separate *const* parameter.
        """
        c = Constraint.inequality_alloc(space)
        return c.set_coefficients_by_name(coefficients)

    Constraint.eq_from_names = staticmethod(eq_from_names)
    Constraint.ineq_from_names = staticmethod(ineq_from_names)

    # }}}

    def basic_obj_get_constraints(self):
        """Get a list of constraints."""
        result = []
        self.foreach_constraint(result.append)
        return result

    # {{{ BasicSet

    BasicSet.get_constraints = basic_obj_get_constraints

    # }}}

    # {{{ BasicMap

    BasicMap.get_constraints = basic_obj_get_constraints

    # }}}

    # {{{ Set

    def set_get_basic_sets(self):
        """Get the list of :class:`BasicSet` instances in this :class:`Set`."""
        result = []
        self.foreach_basic_set(result.append)
        return result

    Set.get_basic_sets = set_get_basic_sets

    # }}}

    # {{{ Map

    def map_get_basic_maps(self):
        """Get the list of :class:`BasicMap` instances in this :class:`Map`."""
        result = []
        self.foreach_basic_map(result.append)
        return result

    Map.get_basic_maps = map_get_basic_maps

    # }}}

    # {{{ common functionality

    def obj_get_id_dict(self, dimtype=None):
        """Return a dictionary mapping :class:`Id` instances to tuples of
        (:class:`dim_type`, index).

        :param dimtype: None to get all variables, otherwise
            one of :class:`dim_type`.
        """
        return self.get_space().get_id_dict(dimtype)

    def obj_get_var_dict(self, dimtype=None):
        """Return a dictionary mapping variable names to tuples of
        (:class:`dim_type`, index).

        :param dimtype: None to get all variables, otherwise
            one of :class:`dim_type`.
        """
        return self.get_space().get_var_dict(dimtype)

    def obj_get_var_ids(self, dimtype):
        """Return a list of :class:`Id` instances for :class:`dim_type` *dimtype*."""
        return [self.get_dim_name(dimtype, i) for i in xrange(self.dim(dimtype))]

    def obj_get_var_names(self, dimtype):
        """Return a list of dim names (in order) for :class:`dim_type` *dimtype*."""
        return [self.get_dim_name(dimtype, i) for i in xrange(self.dim(dimtype))]

    for cls in ALL_CLASSES:
        if hasattr(cls, "get_space") and cls is not Space:
            cls.get_id_dict = obj_get_id_dict
            cls.get_var_dict = obj_get_var_dict
            cls.get_var_ids = obj_get_var_ids
            cls.get_var_names = obj_get_var_names
            cls.space = property(cls.get_space)

    # }}}

    # {{{ PwAff

    def pwaff_get_pieces(self):
        """
        :return: list of (:class:`Set`, :class:`Aff`)
        """

        result = []

        def append_tuple(*args):
            result.append(args)

        self.foreach_piece(append_tuple)
        return result

    def pwaff_get_aggregate_domain(self):
        """
        :return: a :class:`Set` that is the union of the domains of all pieces
        """

        result = Set.empty(self.get_domain_space())
        for dom, _ in self.get_pieces():
            result = result.union(dom)

        return result

    PwAff.get_aggregate_domain = pwaff_get_aggregate_domain
    PwAff.get_pieces = pwaff_get_pieces

    # }}}

    # {{{ aff arithmetic

    def _number_to_aff(template, num):
        number_aff = Aff.zero_on_domain(template.get_domain_space())
        number_aff = number_aff.set_constant_val(num)

        if isinstance(template, PwAff):
            result = PwAff.empty(template.get_space())
            for set, _ in template.get_pieces():
                result = set.indicator_function().cond(number_aff, result)
            return result

        else:
            return number_aff

    def aff_add(self, other):
        if not isinstance(other, (Aff, PwAff)):
            other = _number_to_aff(self, other)

        try:
            return self.add(other)
        except TypeError:
            return NotImplemented

    def aff_sub(self, other):
        if not isinstance(other, (Aff, PwAff)):
            other = _number_to_aff(self, other)

        try:
            return self.sub(other)
        except TypeError:
            return NotImplemented

    def aff_rsub(self, other):
        if not isinstance(other, (Aff, PwAff)):
            other = _number_to_aff(self, other)

        return -self + other

    def aff_mul(self, other):
        if not isinstance(other, (Aff, PwAff)):
            other = _number_to_aff(self, other)

        try:
            return self.mul(other)
        except TypeError:
            return NotImplemented

    def aff_flordiv(self, other):
        return self.scale_down_val(other).floor()

    for aff_class in [Aff, PwAff]:
        aff_class.__add__ = aff_add
        aff_class.__radd__ = aff_add
        aff_class.__sub__ = aff_sub
        aff_class.__rsub__ = aff_rsub
        aff_class.__mul__ = aff_mul
        aff_class.__rmul__ = aff_mul
        aff_class.__neg__ = aff_class.neg
        aff_class.__mod__ = aff_class.mod_val
        aff_class.__floordiv__ = aff_flordiv

    # }}}

    # {{{ Val

    def val_new(cls, src, context=None):
        if context is None:
            context = _DEFAULT_CONTEXT

        if isinstance(src, (str, unicode)):
            result = cls.read_from_str(context, src)
        elif isinstance(src, (int, long)):
            result = cls.int_from_si(context, src)
        else:
            raise TypeError("'src' must be int or string")

        result._made_from_python = True
        return result

    def val_bogus_init(self, src, context=None):
        assert self._made_from_python
        del self._made_from_python

    def val_rsub(self, other):
        return -self + other

    def val_nonzero(self):
        return not self.is_zero()

    def val_repr(self):
        return "%s(\"%s\")" % (type(self).__name__, self.to_str())

    def val_to_python(self):
        if not self.is_int():
            raise ValueError("can only convert integer Val to python")

        return long(self.to_str())

    Val.__new__ = staticmethod(val_new)
    Val.__init__ = val_bogus_init
    Val.__add__ = Val.add
    Val.__radd__ = Val.add
    Val.__sub__ = Val.sub
    Val.__rsub__ = val_rsub
    Val.__mul__ = Val.mul
    Val.__rmul__ = Val.mul
    Val.__neg__ = Val.neg
    Val.__mod__ = Val.mod
    Val.__bool__ = Val.__nonzero__ = val_nonzero

    Val.__lt__ = Val.lt
    Val.__gt__ = Val.gt
    Val.__le__ = Val.le
    Val.__ge__ = Val.ge
    Val.__eq__ = Val.eq
    Val.__ne__ = Val.ne

    Val.__repr__ = val_repr
    Val.__str__ = Val.to_str
    Val.to_python = val_to_python

    # }}}

    # {{{ add automatic 'self' upcasts

    # note: automatic upcasts for method arguments are provided through
    # 'implicitly_convertible' on the C++ side of the wrapper.

    class UpcastWrapper(object):
        def __init__(self, method, upcast):
            self.method = method
            self.upcast = upcast

    def add_upcasts(basic_class, special_class, upcast_method):
        from functools import update_wrapper
        from inspect import ismethod

        for method_name in dir(special_class):
            # do not overwrite existing methods
            if hasattr(basic_class, method_name):
                continue

            method = getattr(special_class, method_name)

            my_ismethod = ismethod(method)
            for meth_superclass in type(method).__mro__:
                if "function" in meth_superclass.__name__:
                    # inspect.ismethod does not work on Boost.Py callables in Py3,
                    # hence this hack.
                    my_ismethod = True
                    break

            if my_ismethod:
                def make_wrapper(method, upcast):
                    # This function provides a scope in which method and upcast
                    # are not changed from one iteration of the enclosing for
                    # loop to the next.

                    def wrapper(basic_instance, *args, **kwargs):
                        special_instance = upcast(basic_instance)
                        return method(special_instance, *args, **kwargs)

                    return wrapper

                wrapper = make_wrapper(method, upcast_method)
                setattr(basic_class, method_name, update_wrapper(wrapper, method))

    for args_triple in [
            (BasicSet, Set, Set.from_basic_set),
            (BasicMap, Map, Map.from_basic_map),
            (Set, UnionSet, UnionSet.from_set),
            (Map, UnionMap, UnionMap.from_map),

            (BasicSet, UnionSet, lambda x: UnionSet.from_set(Set.from_basic_set(x))),
            (BasicMap, UnionMap, lambda x: UnionMap.from_map(Map.from_basic_map(x))),

            (Aff, PwAff, PwAff.from_aff),
            (Space, LocalSpace, LocalSpace.from_space),
            ]:
        add_upcasts(*args_triple)

    # }}}

    # {{{ project_out_except

    def obj_project_out_except(obj, names, types):
        """
        :param types: list of :class:`dim_type` determining
            the types of axes to project out
        :param names: names of axes matching the above which
            should be left alone by the projection

        .. versionadded:: 2011.3
        """

        for tp in types:
            while True:
                space = obj.get_space()
                var_dict = space.get_var_dict(tp)

                all_indices = set(xrange(space.dim(tp)))
                leftover_indices = set(var_dict[name][1] for name in names
                        if name in var_dict)
                project_indices = all_indices-leftover_indices
                if not project_indices:
                    break

                min_index = min(project_indices)
                count = 1
                while min_index+count in project_indices:
                    count += 1

                obj = obj.project_out(tp, min_index, count)

        return obj

    # }}}

    # {{{ eliminate_except

    def obj_eliminate_except(obj, names, types):
        """
        :param types: list of :class:`dim_type` determining
            the types of axes to eliminate
        :param names: names of axes matching the above which
            should be left alone by the eliminate

        .. versionadded:: 2011.3
        """

        for tp in types:
            space = obj.get_space()
            var_dict = space.get_var_dict(tp)
            to_eliminate = (
                    set(xrange(space.dim(tp)))
                    - set(var_dict[name][1] for name in names
                        if name in var_dict))

            while to_eliminate:
                min_index = min(to_eliminate)
                count = 1
                while min_index+count in to_eliminate:
                    count += 1

                obj = obj.eliminate(tp, min_index, count)

                to_eliminate -= set(xrange(min_index, min_index+count))

        return obj

    # }}}

    # {{{ add_constraints

    def obj_add_constraints(obj, constraints):
        """
        .. versionadded:: 2011.3
        """

        for cns in constraints:
            obj = obj.add_constraint(cns)

        return obj

    # }}}

    for c in [BasicSet, BasicMap, Set, Map]:
        c.project_out_except = obj_project_out_except
        c.add_constraints = obj_add_constraints

    for c in [BasicSet, Set]:
        c.eliminate_except = obj_eliminate_except


_add_functionality()


def _align_dim_type(tgt_dt, obj, tgt, obj_bigger_ok, obj_names, tgt_names):
    if None in tgt_names:
        all_nones = [None] * len(tgt_names)
        if tgt_names == all_nones and obj_names == all_nones:
            # that's ok
            return obj

        raise RuntimeError("tgt may not contain any unnamed dimensions")

    obj_names = set(obj_names) - set([None])
    tgt_names = set(tgt_names) - set([None])

    names_in_both = obj_names & tgt_names

    tgt_idx = 0
    while tgt_idx < tgt.dim(tgt_dt):
        tgt_id = tgt.get_dim_id(tgt_dt, tgt_idx)
        tgt_name = tgt_id.name

        if tgt_name in names_in_both:
            if (obj.dim(tgt_dt) > tgt_idx
                    and tgt_name == obj.get_dim_name(tgt_dt, tgt_idx)):
                tgt_idx += 1
            else:
                src_dt, src_idx = obj.get_var_dict()[tgt_name]

                if src_dt == tgt_dt:
                    assert src_idx > tgt_idx

                    # isl requires move_dims to be between different types.
                    # Not sure why. Let's make it happy.
                    other_dt = dim_type.param
                    if src_dt == other_dt:
                        other_dt = dim_type.out

                    other_dt_dim = obj.dim(other_dt)
                    obj = obj.move_dims(other_dt, other_dt_dim, src_dt, src_idx, 1)
                    obj = obj.move_dims(tgt_dt, tgt_idx, other_dt, other_dt_dim, 1)
                else:
                    obj = obj.move_dims(tgt_dt, tgt_idx, src_dt, src_idx, 1)

                tgt_idx += 1
        else:
            obj = obj.insert_dims(tgt_dt, tgt_idx, 1)
            obj = obj.set_dim_id(tgt_dt, tgt_idx, tgt_id)
            tgt_idx += 1

    if tgt_idx < obj.dim(tgt_dt) and not obj_bigger_ok:
        raise ValueError("obj has leftover dimensions")

    return obj


def align_spaces(obj, tgt, obj_bigger_ok=False, across_dim_types=False):
    """
    Try to make the space in which *obj* lives the same as that of *tgt* by
    adding/matching named dimensions.

    :param obj_bigger_ok: If *True*, no error is raised if the resulting *obj*
        has more dimensions than *tgt*.
    """

    have_any_param_domains = (
            isinstance(obj, (Set, BasicSet))
            and isinstance(tgt, (Set, BasicSet))
            and (obj.is_params() or tgt.is_params()))
    if have_any_param_domains:
        if obj.is_params():
            obj = type(obj).from_params(obj)
        if tgt.is_params():
            tgt = type(tgt).from_params(tgt)

    if isinstance(tgt, EXPR_CLASSES):
        dim_types = _CHECK_DIM_TYPES[:]
        dim_types.remove(dim_type.out)
    else:
        dim_types = _CHECK_DIM_TYPES

    if across_dim_types:
        obj_names = [
                obj.get_dim_name(dt, i)
                for dt in dim_types
                for i in xrange(obj.dim(dt))
                ]
        tgt_names = [
                tgt.get_dim_name(dt, i)
                for dt in dim_types
                for i in xrange(tgt.dim(dt))
                ]

        for dt in dim_types:
            obj = _align_dim_type(dt, obj, tgt, obj_bigger_ok, obj_names, tgt_names)
    else:
        for dt in dim_types:
            obj_names = [obj.get_dim_name(dt, i) for i in xrange(obj.dim(dt))]
            tgt_names = [tgt.get_dim_name(dt, i) for i in xrange(tgt.dim(dt))]

            obj = _align_dim_type(dt, obj, tgt, obj_bigger_ok, obj_names, tgt_names)

    return obj


def align_two(obj1, obj2, across_dim_types=False):
    """Align the spaces of two objects, potentially modifying both of them.

    See also :func:`align_spaces`.
    """

    obj1 = align_spaces(obj1, obj2, obj_bigger_ok=True,
            across_dim_types=across_dim_types)
    obj2 = align_spaces(obj2, obj1, obj_bigger_ok=True,
            across_dim_types=across_dim_types)
    return (obj1, obj2)


# vim: foldmethod=marker
