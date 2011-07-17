from islpy._isl import *
from islpy.version import *

def _add_functionality():
    import islpy._isl as _isl

    ALL_CLASSES = [getattr(_isl, cls) for cls in dir(_isl) if cls[0].isupper()]

    # {{{ printing

    def generic_repr(self):
        prn = Printer.to_str(self.get_ctx())
        getattr(prn, "print_"+self._base_name)(self)
        return prn.get_str()

    for cls in ALL_CLASSES:
        if hasattr(Printer, "print_"+cls._base_name):
            cls.__repr__ = generic_repr

    # }}}

    # {{{ Dim

    def dim_get_var_dict(self, dimtype=None):
        """Return a dictionary mapping variable names to tuples of (:class:`dim_type`, index).

        :param dim_type: None to get all variables, otherwise
            one of :class:`dim_type`.
        """
        result = {}

        def set_name(name, tp, idx):
            if name in result:
                raise RuntimeError("non-unique var name '%s' encountered" % name)
            result[name] = tp, idx

        if dimtype is None:
            types = [dim_type.cst, dim_type.param, dim_type.in_, 
                    dim_type.out, dim_type.div]
        else:
            types = [dimtype]

        for tp in types:
            for i in range(self.size(tp)):
                name = self.get_name(tp, i)
                if name is not None:
                    set_name(name, tp, i)

        return result

    def dim_create_from_names(ctx, set=None, in_=None, out=None, params=[]):
        """Create a :class:`Dim` from lists of variable names.

        :param set_`: names of `set`-type variables.
        :param in_`: names of `in`-type variables.
        :param out`: names of `out`-type variables.
        :param params`: names of parameter-type variables.
        """
        dt = dim_type

        if set is not None:
            if in_ is not None or out is not None:
                raise RuntimeError("must pass only one of set / (in_,out)")

            result = Dim.set_alloc(ctx, nparam=len(params),
                    dim=len(set))

            for i, name in enumerate(set):
                result = result.set_name(dt.set, i, name)

        elif in_ is not None and out is not None:
            if dim is not None:
                raise RuntimeError("must pass only one of set / (in_,out)")

            result = Dim.alloc(ctx, nparam=len(params),
                    n_in=len(in_), n_out=len(out))

            for i, name in enumerate(in_):
                result = result.set_name(dt.in_, i, name)

            for i, name in enumerate(out):
                result = result.set_name(dt.out, i, name)
        else:
            raise RuntimeError("invalid parameter combination")

        for i, name in enumerate(params):
            result = result.set_name(dt.param, i, name)

        return result

    Dim.create_from_names = staticmethod(dim_create_from_names)
    Dim.get_var_dict = dim_get_var_dict

    # }}}

    # {{{ Constraint

    def constraint_set_coefficients(self, dim_tp, args):
        """
        :param dim_tp: :class:`dim_type`
        :param args: :class:`list` of coefficients, for indices `0..len(args)-1`.
        """
        for i, coeff in enumerate(args):
            self.set_coefficient(dim_tp, i, coeff)

        return self

    def constraint_set_coefficients_by_name(self, iterable):
        """
        :param iterable: a :class:`dict` or iterable of :class:`tuple` instances mapping variable names to their coefficients
        """
        try:
            iterable = iterable.iteritems()
        except AttributeError:
            pass

        var2idx = self.get_dim().get_var_dict()

        for name, coeff in iterable:
            tp, idx = var2idx[name]
            self.set_coefficient(tp, idx, coeff)

        return self

    def eq_from_names(dim, const=0, coefficients={}):
        """Create a constraint `const + coeff_1*var_1 +... == 0`.

        :param dim: :class:`Dim`
        :param const: constant part of the constraint expression
        :param coefficients: a :class:`dict` or iterable of :class:`tuple`
            instances mapping variable names to their coefficients

        """
        c = Constraint.equality_alloc(dim.copy())
        c.set_constant(const)
        return c.set_coefficients_by_name(coefficients)

    def ineq_from_names(dim, const=0, coefficients={}):
        """Create a constraint `const + coeff_1*var_1 +... >= 0`.

        :param dim: :class:`Dim`
        :param const: constant part of the constraint expression
        :param coefficients: a :class:`dict` or iterable of :class:`tuple` 
            instances mapping variable names to their coefficients
        """
        c = Constraint.inequality_alloc(dim.copy())
        c.set_constant(const)
        return c.set_coefficients_by_name(coefficients)

    Constraint.set_coefficients = constraint_set_coefficients
    Constraint.set_coefficients_by_name = constraint_set_coefficients_by_name
    Constraint.eq_from_names = staticmethod(eq_from_names)
    Constraint.ineq_from_names = staticmethod(ineq_from_names)

    # }}}

    # {{{ BasicSet

    def basic_set_as_set(self):
        """Return self as a :class:`Set`."""
        return Set.from_basic_set(self)

    BasicSet.as_set = basic_set_as_set

    # }}}

    # {{{ BasicMap

    def basic_map_as_map(self):
        """Return *self* as a :class:`Map`."""
        return Map.from_basic_map(self)

    BasicMap.as_map = basic_map_as_map

    # }}}

    # {{{ add automatic upcasts

    class UpcastWrapper(object):
        def __init__(self, method, upcast):
            self.method = method
            self.upcast = upcast

    def add_upcasts(basic_class, special_class, upcast_method):
        from functools import update_wrapper

        from inspect import ismethod
        for method_name in dir(special_class):
            if hasattr(basic_class, method_name):
                continue

            method = getattr(special_class, method_name)

            if ismethod(method):
                def make_wrapper(method, upcast):
                    # this function provides a scope in which method and upcast
                    # are not changed

                    def wrapper(basic_instance, *args, **kwargs):
                        special_instance = upcast(basic_instance)
                        return method(special_instance, *args, **kwargs)

                    return wrapper

                wrapper = make_wrapper(method, upcast_method)
                setattr(basic_class, method_name, update_wrapper(wrapper, method))

    for args_triple in [
            (BasicSet, Set, BasicSet.as_set),
            (BasicMap, Map, BasicMap.as_map),
            ]:
        add_upcasts(*args_triple)

    # }}}






_add_functionality()

# vim: foldmethod=marker
