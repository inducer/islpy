from islpy._isl import *
from islpy.version import *

def _add_functionality():
    import islpy._isl as _isl

    ALL_CLASSES = [getattr(_isl, cls) for cls in dir(_isl) if cls[0].isupper()]

    # {{{ printing

    def generic_str(self):
        prn = Printer.to_str(self.get_ctx())
        getattr(prn, "print_"+self._base_name)(self)
        return prn.get_str()

    for cls in ALL_CLASSES:
        if hasattr(Printer, "print_"+cls._base_name):
            cls.__str__ = generic_str

    # }}}

    # {{{ Dim

    def dim_get_var_dict(self):
        result = {}

        def set_name(name, tp, idx):

            if name in result:
                raise RuntimeError("non-unique var name '%s' encountered")
            result[name] = tp, idx

        dt = dim_type
        for tp in [dt.cst, dt.param, dt.in_, dt.out, dt.div]:
            for i in range(self.size(tp)):
                name = self.get_name(tp, i)
                if name is not None:
                    set_name(name, tp, i)

        return result

    Dim.get_var_dict = dim_get_var_dict

    # }}}

    # {{{ Constraint

    def constraint_set_coefficients(self, dim_tp, args):
        for i, coeff in enumerate(args):
            self.set_coefficient(dim_tp, i, coeff)

        return self

    def constraint_set_coefficients_by_name(self, iterable):
        try:
            iterable = iterable.iteritems()
        except AttributeError:
            pass

        var2idx = self.get_dim().get_var_dict()

        for name, coeff in iterable:
            tp, idx = var2idx[name]
            self.set_coefficient(tp, idx, coeff)

        return self

    Constraint.set_coefficients = constraint_set_coefficients
    Constraint.set_coefficients_by_name = constraint_set_coefficients_by_name

    # }}}



_add_functionality()

def create_dim(ctx, set=None, in_=None, out=None, params=[]):
    dt = dim_type

    if set is not None:
        if in_ is not None or out is not None:
            raise RuntimeError("must pass only one of set / (in_,out)")

        result = Dim.set_alloc(ctx, nparam=len(params),
                dim=len(set))

        for i, name in enumerate(set):
            result.set_name(dt.set, i, name)

    elif in_ is not None and out is not None:
        if dim is not None:
            raise RuntimeError("must pass only one of set / (in_,out)")

        result = Dim.alloc(ctx, nparam=len(params),
                n_in=len(in_), n_out=len(out))

        for i, name in enumerate(in_):
            result.set_name(dt.in_, i, name)

        for i, name in enumerate(out):
            result.set_name(dt.out, i, name)
    else:
        raise RuntimeError("invalid parameter combination")

    for i, name in enumerate(params):
        result.set_name(dt.param, i, name)

    return result

def create_eq_by_names(dim, const=0, coefficients={}):
    c = Constraint.equality_alloc(dim.copy())
    c.set_constant(const)
    return c.set_coefficients_by_name(coefficients)

def create_ineq_by_names(dim, const=0, coefficients={}):
    c = Constraint.inequality_alloc(dim.copy())
    c.set_constant(const)
    return c.set_coefficients_by_name(coefficients)

# vim: foldmethod=marker
