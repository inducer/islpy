__copyright__ = "Copyright (C) 2011-20 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import islpy._isl as _isl
from islpy.version import VERSION, VERSION_TEXT  # noqa
import six
from six.moves import range


Error = _isl.Error

# {{{ name imports

Context = _isl.Context
IdList = _isl.IdList
ValList = _isl.ValList
BasicSetList = _isl.BasicSetList
BasicMapList = _isl.BasicMapList
SetList = _isl.SetList
MapList = _isl.MapList
UnionSetList = _isl.UnionSetList
ConstraintList = _isl.ConstraintList
AffList = _isl.AffList
PwAffList = _isl.PwAffList
AstExprList = _isl.AstExprList
AstNodeList = _isl.AstNodeList
IdToAstExpr = _isl.IdToAstExpr
Printer = _isl.Printer
Val = _isl.Val
MultiVal = _isl.MultiVal
Vec = _isl.Vec
Mat = _isl.Mat
Aff = _isl.Aff
PwAff = _isl.PwAff
UnionPwAff = _isl.UnionPwAff
MultiAff = _isl.MultiAff
MultiPwAff = _isl.MultiPwAff
PwMultiAff = _isl.PwMultiAff
UnionPwMultiAff = _isl.UnionPwMultiAff
UnionPwAffList = _isl.UnionPwAffList
MultiUnionPwAff = _isl.MultiUnionPwAff
Id = _isl.Id
Constraint = _isl.Constraint
Space = _isl.Space
LocalSpace = _isl.LocalSpace
BasicSet = _isl.BasicSet
BasicMap = _isl.BasicMap
Set = _isl.Set
Map = _isl.Map
UnionMap = _isl.UnionMap
UnionSet = _isl.UnionSet
Point = _isl.Point
Vertex = _isl.Vertex
Cell = _isl.Cell
Vertices = _isl.Vertices
StrideInfo = _isl.StrideInfo
QPolynomialFold = _isl.QPolynomialFold
PwQPolynomialFold = _isl.PwQPolynomialFold
UnionPwQPolynomialFold = _isl.UnionPwQPolynomialFold
UnionPwQPolynomial = _isl.UnionPwQPolynomial
QPolynomial = _isl.QPolynomial
PwQPolynomial = _isl.PwQPolynomial
Term = _isl.Term
ScheduleConstraints = _isl.ScheduleConstraints
ScheduleNode = _isl.ScheduleNode
Schedule = _isl.Schedule
AccessInfo = _isl.AccessInfo
Flow = _isl.Flow
Restriction = _isl.Restriction
UnionAccessInfo = _isl.UnionAccessInfo
UnionFlow = _isl.UnionFlow
AstExpr = _isl.AstExpr
AstNode = _isl.AstNode
AstPrintOptions = _isl.AstPrintOptions
AstBuild = _isl.AstBuild

error = _isl.error
stat = _isl.stat
dim_type = _isl.dim_type
schedule_node_type = _isl.schedule_node_type
ast_expr_op_type = _isl.ast_expr_op_type
ast_expr_type = _isl.ast_expr_type
ast_node_type = _isl.ast_node_type
ast_loop_type = _isl.ast_loop_type
fold = _isl.fold
format = _isl.format
yaml_style = _isl.yaml_style
bound = _isl.bound
on_error = _isl.on_error
schedule_algorithm = _isl.schedule_algorithm

# backward compatibility
ast_op_type = _isl.ast_expr_op_type

ALL_CLASSES = [Context, IdList, ValList, BasicSetList, BasicMapList, SetList,
        MapList, UnionSetList, ConstraintList, AffList, PwAffList, AstExprList,
        AstNodeList, IdToAstExpr, Printer, Val, MultiVal, Vec, Mat, Aff, PwAff,
        UnionPwAff, MultiAff, MultiPwAff, PwMultiAff, UnionPwMultiAff,
        UnionPwAffList, MultiUnionPwAff, Id, Constraint, Space, LocalSpace,
        BasicSet, BasicMap, Set, Map, UnionMap, UnionSet, Point, Vertex, Cell,
        Vertices, StrideInfo, QPolynomialFold, PwQPolynomialFold,
        UnionPwQPolynomialFold, UnionPwQPolynomial, QPolynomial, PwQPolynomial,
        Term, ScheduleConstraints, ScheduleNode, Schedule, AccessInfo,
        Flow, Restriction, UnionAccessInfo, UnionFlow, AstExpr, AstNode,
        AstPrintOptions, AstBuild]

# }}}


_CHECK_DIM_TYPES = [
        dim_type.in_, dim_type.param, dim_type.set]

ALL_CLASSES = tuple(getattr(_isl, cls) for cls in dir(_isl) if cls[0].isupper())
EXPR_CLASSES = tuple(cls for cls in ALL_CLASSES
        if "Aff" in cls.__name__ or "Polynomial" in cls.__name__)

DEFAULT_CONTEXT = Context()


def _get_default_context():
    """A callable to get the default context for the benefit of Python's
    ``__reduce__`` protocol.
    """
    return DEFAULT_CONTEXT


def _read_from_str_wrapper(cls, context, s):
    """A callable to reconstitute instances from strings for the benefit
    of Python's ``__reduce__`` protocol.
    """
    return cls.read_from_str(context, s)


def _add_functionality():
    import islpy._isl as _isl  # noqa

    # {{{ Context

    def context_reduce(self):
        if self._wraps_same_instance_as(DEFAULT_CONTEXT):
            return (_get_default_context, ())
        else:
            return (Context, ())

    def context_eq(self, other):
        return isinstance(other, Context) and self._wraps_same_instance_as(other)

    def context_ne(self, other):
        return not self.__eq__(other)

    Context.__reduce__ = context_reduce
    Context.__eq__ = context_eq
    Context.__ne__ = context_ne

    # }}}

    # {{{ generic initialization, pickling

    def obj_new(cls, s=None, context=None):
        """Construct a new object from :class:`str` s.

        :arg context: a :class:`islpy.Context` to use. If not supplied, use a
            global default context.
        """
        if not isinstance(s, str):
            return cls._prev_new(cls)

        if context is None:
            context = DEFAULT_CONTEXT

        result = cls.read_from_str(context, s)
        return result

    def obj_bogus_init(self, s, context=None):
        if not isinstance(s, str) and self._prev_init is not None:
            self._prev_init(s)

    def generic_reduce(self):
        ctx = self.get_ctx()
        prn = Printer.to_str(ctx)
        prn = getattr(prn, "print_"+self._base_name)(self)
        return (_read_from_str_wrapper, (type(self), ctx, prn.get_str()))

    for cls in ALL_CLASSES:
        if hasattr(cls, "read_from_str"):
            cls._prev_new = cls.__new__
            cls.__new__ = obj_new
            cls._prev_init = getattr(cls, "__init__", None)
            cls.__init__ = obj_bogus_init
            cls.__reduce__ = generic_reduce

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

    def generic_hash(self):
        return hash((type(self), str(self)))

    def generic_isl_hash(self):
        return self.get_hash()

    for cls in ALL_CLASSES:
        if hasattr(cls, "_base_name") and hasattr(Printer, "print_"+cls._base_name):
            cls.__str__ = generic_str
            cls.__repr__ = generic_repr

            if not hasattr(cls, "get_hash"):
                cls.__hash__ = generic_hash

        if hasattr(cls, "get_hash"):
            cls.__hash__ = generic_isl_hash

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

    # }}}

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

    def space_get_var_dict(self, dimtype=None, ignore_out=False):
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
            if ignore_out:
                types = types[:]
                types.remove(dim_type.out)
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
        :param params: names of parameter-type variables.
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
            iterable = list(iterable.items())
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
                coeff = self.get_coefficient_val(tp, i)
                if coeff:
                    if dim_to_name is None:
                        name = self.get_dim_name(tp, i)
                    else:
                        name = dim_to_name[(tp, i)]

                    result[name] = coeff

        const = self.get_constant_val()
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
            context = DEFAULT_CONTEXT

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
        return self.get_space().get_var_dict(
                dimtype, ignore_out=isinstance(self, EXPR_CLASSES))

    def obj_get_var_ids(self, dimtype):
        """Return a list of :class:`Id` instances for :class:`dim_type` *dimtype*."""
        return [self.get_dim_name(dimtype, i) for i in range(self.dim(dimtype))]

    def obj_get_var_names(self, dimtype):
        """Return a list of dim names (in order) for :class:`dim_type` *dimtype*."""
        return [self.get_dim_name(dimtype, i) for i in range(self.dim(dimtype))]

    for cls in ALL_CLASSES:
        if hasattr(cls, "get_space") and cls is not Space:
            cls.get_id_dict = obj_get_id_dict
            cls.get_var_dict = obj_get_var_dict
            cls.get_var_ids = obj_get_var_ids
            cls.get_var_names = obj_get_var_names
            cls.space = property(cls.get_space)

    # }}}

    # {{{ piecewise

    def pwaff_get_pieces(self):
        """
        :return: list of (:class:`Set`, :class:`Aff`)
        """

        result = []

        def append_tuple(*args):
            result.append(args)

        self.foreach_piece(append_tuple)
        return result

    def pwqpolynomial_get_pieces(self):
        """
        :return: list of (:class:`Set`, :class:`QPolynomial`)
        """

        result = []

        def append_tuple(*args):
            result.append(args)

        self.foreach_piece(append_tuple)
        return result

    def pw_get_aggregate_domain(self):
        """
        :return: a :class:`Set` that is the union of the domains of all pieces
        """

        result = Set.empty(self.get_domain_space())
        for dom, _ in self.get_pieces():
            result = result.union(dom)

        return result

    PwAff.get_pieces = pwaff_get_pieces
    PwAff.get_aggregate_domain = pw_get_aggregate_domain

    PwQPolynomial.get_pieces = pwqpolynomial_get_pieces
    PwQPolynomial.get_aggregate_domain = pw_get_aggregate_domain

    # }}}

    # {{{ QPolynomial

    def qpolynomial_get_terms(self):
        """Get the list of :class:`Term` instances in this :class:`QPolynomial`."""
        result = []
        self.foreach_term(result.append)
        return result

    QPolynomial.get_terms = qpolynomial_get_terms

    # }}}

    # {{{ PwQPolynomial

    def pwqpolynomial_eval_with_dict(self, value_dict):
        """Evaluates *self* for the parameters specified by
        *value_dict*, which maps parameter names to their values.
        """

        pt = Point.zero(self.space.params())

        for i in range(self.space.dim(dim_type.param)):
            par_name = self.space.get_dim_name(dim_type.param, i)
            pt = pt.set_coordinate_val(
                dim_type.param, i, value_dict[par_name])

        return self.eval(pt).to_python()

    PwQPolynomial.eval_with_dict = pwqpolynomial_eval_with_dict

    # }}}

    # {{{ arithmetic

    def _number_to_expr_like(template, num):
        number_aff = Aff.zero_on_domain(template.get_domain_space())
        number_aff = number_aff.set_constant_val(num)

        if isinstance(template, Aff):
            return number_aff
        if isinstance(template, QPolynomial):
            return QPolynomial.from_aff(number_aff)

        # everything else is piecewise

        if template.get_pieces():
            number_pw_aff = PwAff.empty(template.get_space())
            for set, _ in template.get_pieces():
                number_pw_aff = set.indicator_function().cond(
                        number_aff, number_pw_aff)
        else:
            number_pw_aff = PwAff.alloc(
                    Set.universe(template.domain().space),
                    number_aff)

        if isinstance(template, PwAff):
            return number_pw_aff

        elif isinstance(template, PwQPolynomial):
            return PwQPolynomial.from_pw_aff(number_pw_aff)

        else:
            raise TypeError("unexpected template type")

    ARITH_CLASSES = (Aff, PwAff, QPolynomial, PwQPolynomial)  # noqa

    def expr_like_add(self, other):
        if not isinstance(other, ARITH_CLASSES):
            other = _number_to_expr_like(self, other)

        try:
            return self.add(other)
        except TypeError:
            return NotImplemented

    def expr_like_sub(self, other):
        if not isinstance(other, ARITH_CLASSES):
            other = _number_to_expr_like(self, other)

        try:
            return self.sub(other)
        except TypeError:
            return NotImplemented

    def expr_like_rsub(self, other):
        if not isinstance(other, ARITH_CLASSES):
            other = _number_to_expr_like(self, other)

        return -self + other

    def expr_like_mul(self, other):
        if not isinstance(other, ARITH_CLASSES):
            other = _number_to_expr_like(self, other)

        try:
            return self.mul(other)
        except TypeError:
            return NotImplemented

    def expr_like_floordiv(self, other):
        return self.scale_down_val(other).floor()

    for expr_like_class in ARITH_CLASSES:
        expr_like_class.__add__ = expr_like_add
        expr_like_class.__radd__ = expr_like_add
        expr_like_class.__sub__ = expr_like_sub
        expr_like_class.__rsub__ = expr_like_rsub
        expr_like_class.__mul__ = expr_like_mul
        expr_like_class.__rmul__ = expr_like_mul
        expr_like_class.__neg__ = expr_like_class.neg

    for qpoly_class in [QPolynomial, PwQPolynomial]:
        expr_like_class.__pow__ = expr_like_class.pow

    for aff_class in [Aff, PwAff]:
        aff_class.__mod__ = aff_class.mod_val
        aff_class.__floordiv__ = expr_like_floordiv

    # }}}

    # {{{ Val

    def val_new(cls, src, context=None):
        if context is None:
            context = DEFAULT_CONTEXT

        if isinstance(src, six.string_types):
            result = cls.read_from_str(context, src)
        elif isinstance(src, six.integer_types):
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

    def val_bool(self):
        return not self.is_zero()

    def val_repr(self):
        return "%s(\"%s\")" % (type(self).__name__, self.to_str())

    def val_to_python(self):
        if not self.is_int():
            raise ValueError("can only convert integer Val to python")

        import sys
        if sys.version_info >= (3,):
            return int(self.to_str())
        else:
            return int(self.to_str())

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
    Val.__bool__ = Val.__nonzero__ = val_bool

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

    def make_new_upcast_wrapper(method, upcast):
        # This function provides a scope in which method and upcast
        # are not changed from one iteration of the enclosing for
        # loop to the next.

        def wrapper(basic_instance, *args, **kwargs):
            special_instance = upcast(basic_instance)
            return method(special_instance, *args, **kwargs)

        return wrapper

    def make_existing_upcast_wrapper(basic_method, special_method, upcast):
        # This function provides a scope in which method and upcast
        # are not changed from one iteration of the enclosing for
        # loop to the next.

        def wrapper(basic_instance, *args, **kwargs):
            try:
                return basic_method(basic_instance, *args, **kwargs)
            except TypeError:
                pass

            special_instance = upcast(basic_instance)
            return special_method(special_instance, *args, **kwargs)

        return wrapper

    def add_upcasts(basic_class, special_class, upcast_method):
        from functools import update_wrapper

        def my_ismethod(class_, method_name):
            if method_name.startswith("_"):
                return False

            method = getattr(class_, method_name)

            if not callable(method):
                return False

            # Here we're desperately trying to filter out static methods,
            # based on what seems to be a common feature.
            if any("builtin_function_or_method" in meth_superclass.__name__
                    for meth_superclass in type(method).__mro__):
                return False

            return True

        for method_name in dir(special_class):
            special_method = getattr(special_class, method_name)

            if not my_ismethod(special_class, method_name):
                continue

            if hasattr(basic_class, method_name):
                # method already exists in basic class
                basic_method = getattr(basic_class, method_name)

                if not my_ismethod(basic_class, method_name):
                    continue

                wrapper = make_existing_upcast_wrapper(
                        basic_method, special_method, upcast_method)
                setattr(
                        basic_class, method_name,
                        update_wrapper(wrapper, basic_method))
            else:
                # method does not yet exists in basic class

                wrapper = make_new_upcast_wrapper(special_method, upcast_method)
                setattr(
                        basic_class, method_name,
                        update_wrapper(wrapper, special_method))

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

    # ORDERING DEPENDENCY: The availability of some of the 'is_equal'
    # used by rich comparison below depends on the self upcasts created
    # above.

    # {{{ rich comparisons

    def obj_eq(self, other):
        assert self.get_ctx() == other.get_ctx(), (
                "Equality-comparing two objects from different ISL Contexts "
                "will likely lead to entertaining (but never useful) results. "
                "In particular, Spaces with matching names will no longer be "
                "equal.")

        return self.is_equal(other)

    def obj_ne(self, other):
        return not self.__eq__(other)

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

                all_indices = set(range(space.dim(tp)))
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
                    set(range(space.dim(tp)))
                    - set(var_dict[name][1] for name in names
                        if name in var_dict))

            while to_eliminate:
                min_index = min(to_eliminate)
                count = 1
                while min_index+count in to_eliminate:
                    count += 1

                obj = obj.eliminate(tp, min_index, count)

                to_eliminate -= set(range(min_index, min_index+count))

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


def _back_to_basic(new_obj, old_obj):
    # Work around set_dim_id not being available for Basic{Set,Map}
    if isinstance(old_obj, BasicSet) and isinstance(new_obj, Set):
        bsets = new_obj.get_basic_sets()

        if len(bsets) == 0:
            bset = BasicSet.universe(new_obj.space).complement()
        else:
            bset, = bsets

        return bset

    if isinstance(old_obj, BasicMap) and isinstance(new_obj, Map):
        bmaps = new_obj.get_basic_maps()

        if len(bmaps) == 0:
            bmap = BasicMap.universe(new_obj.space).complement()
        else:
            bmap, = bmaps

        return bmap

    return new_obj


def _set_dim_id(obj, dt, idx, id):
    return _back_to_basic(obj.set_dim_id(dt, idx, id), obj)


def _align_dim_type(template_dt, obj, template, obj_bigger_ok, obj_names,
        template_names):

    # {{{ deal with Aff, PwAff

    # The technique below will not work for PwAff et al, because there is *only*
    # the 'param' dim_type, and we are not allowed to move dims around in there.
    # We'll make isl do the work, using align_params.

    if template_dt == dim_type.param and isinstance(obj, (Aff, PwAff)):
        if not isinstance(template, Space):
            template_space = template.space
        else:
            template_space = template

        if not obj_bigger_ok:
            if (obj.dim(template_dt) > template.dim(template_dt)
                    or not set(obj.get_var_dict()) <= set(template.get_var_dict())):
                raise Error("obj has leftover dimensions after alignment")
        return obj.align_params(template_space)

    # }}}

    if None in template_names:
        all_nones = [None] * len(template_names)
        if template_names == all_nones and obj_names == all_nones:
            # that's ok
            return obj

        raise Error("template may not contain any unnamed dimensions")

    obj_names = set(obj_names) - set([None])
    template_names = set(template_names) - set([None])

    names_in_both = obj_names & template_names

    tgt_idx = 0
    while tgt_idx < template.dim(template_dt):
        tgt_id = template.get_dim_id(template_dt, tgt_idx)
        tgt_name = tgt_id.name

        if tgt_name in names_in_both:
            if (obj.dim(template_dt) > tgt_idx
                    and tgt_name == obj.get_dim_name(template_dt, tgt_idx)):
                pass

            else:
                src_dt, src_idx = obj.get_var_dict()[tgt_name]

                if src_dt == template_dt:
                    assert src_idx > tgt_idx

                    # isl requires move_dims to be between different types.
                    # Not sure why. Let's make it happy.
                    other_dt = dim_type.param
                    if src_dt == other_dt:
                        other_dt = dim_type.out

                    other_dt_dim = obj.dim(other_dt)
                    obj = obj.move_dims(other_dt, other_dt_dim, src_dt, src_idx, 1)
                    obj = obj.move_dims(
                            template_dt, tgt_idx, other_dt, other_dt_dim, 1)
                else:
                    obj = obj.move_dims(template_dt, tgt_idx, src_dt, src_idx, 1)

            # names are same, make Ids the same, too
            obj = _set_dim_id(obj, template_dt, tgt_idx, tgt_id)

            tgt_idx += 1
        else:
            obj = obj.insert_dims(template_dt, tgt_idx, 1)
            obj = _set_dim_id(obj, template_dt, tgt_idx, tgt_id)

            tgt_idx += 1

    if tgt_idx < obj.dim(template_dt) and not obj_bigger_ok:
        raise Error("obj has leftover dimensions after alignment")

    return obj


def align_spaces(obj, template, obj_bigger_ok=False, across_dim_types=None):
    """
    Try to make the space in which *obj* lives the same as that of *template* by
    adding/matching named dimensions.

    :param obj_bigger_ok: If *True*, no error is raised if the resulting *obj*
        has more dimensions than *template*.
    """

    if across_dim_types is not None:
        from warnings import warn
        warn("across_dim_types is deprecated and should no longer be used. "
                "It never had any effect anyway.",
                DeprecationWarning, stacklevel=2)

    have_any_param_domains = (
            isinstance(obj, (Set, BasicSet))
            and isinstance(template, (Set, BasicSet))
            and (obj.is_params() or template.is_params()))
    if have_any_param_domains:
        if obj.is_params():
            obj = type(obj).from_params(obj)
        if template.is_params():
            template = type(template).from_params(template)

    if isinstance(template, EXPR_CLASSES):
        dim_types = _CHECK_DIM_TYPES[:]
        dim_types.remove(dim_type.out)
    else:
        dim_types = _CHECK_DIM_TYPES

    obj_names = [
            obj.get_dim_name(dt, i)
            for dt in dim_types
            for i in range(obj.dim(dt))
            ]
    template_names = [
            template.get_dim_name(dt, i)
            for dt in dim_types
            for i in range(template.dim(dt))
            ]

    for dt in dim_types:
        obj = _align_dim_type(
                dt, obj, template, obj_bigger_ok, obj_names, template_names)

    return obj


def align_two(obj1, obj2, across_dim_types=None):
    """Align the spaces of two objects, potentially modifying both of them.

    See also :func:`align_spaces`.
    """

    if across_dim_types is not None:
        from warnings import warn
        warn("across_dim_types is deprecated and should no longer be used. "
                "It never had any effect anyway.",
                DeprecationWarning, stacklevel=2)

    obj1 = align_spaces(obj1, obj2, obj_bigger_ok=True)
    obj2 = align_spaces(obj2, obj1, obj_bigger_ok=True)
    return (obj1, obj2)


def make_zero_and_vars(set_vars, params=[], ctx=None):
    """
    :arg set_vars: an iterable of variable names, or a comma-separated string
    :arg params: an iterable of variable names, or a comma-separated string

    :return: a dictionary from variable names (in *set_vars* and *params*)
        to :class:`PwAff` instances that represent each of the
        variables. They key '0' is also include and represents
        a :class:`PwAff` zero constant.

    .. versionadded:: 2016.1.1

    This function is intended to make it relatively easy to construct sets
    programmatically without resorting to string manipulation.

    Usage example::

        v = isl.make_zero_and_vars("i,j,k", "n")

        myset = (
                v[0].le_set(v["i"] + v["j"])
                &
                (v["i"] + v["j"]).lt_set(v["n"])
                &
                (v[0].le_set(v["i"]))
                &
                (v["i"].le_set(13 + v["n"]))
                )
    """
    if ctx is None:
        ctx = DEFAULT_CONTEXT

    if isinstance(set_vars, str):
        set_vars = [s.strip() for s in set_vars.split(",")]
    if isinstance(params, str):
        params = [s.strip() for s in params.split(",")]

    space = Space.create_from_names(ctx, set=set_vars, params=params)
    return affs_from_space(space)


def affs_from_space(space):
    """
    :return: a dictionary from variable names (in *set_vars* and *params*)
        to :class:`PwAff` instances that represent each of the
        variables *in*space*. They key '0' is also include and represents
        a :class:`PwAff` zero constant.

    .. versionadded:: 2016.2

    This function is intended to make it relatively easy to construct sets
    programmatically without resorting to string manipulation.

    Usage example::

        s = isl.Set("[n] -> {[i,j,k]: 0<=i,j,k<n}")
        v = isl.affs_from_space(s.space)

        myset = (
                v[0].le_set(v["i"] + v["j"])
                &
                (v["i"] + v["j"]).lt_set(v["n"])
                &
                (v[0].le_set(v["i"]))
                &
                (v["i"].le_set(13 + v["n"]))
                )
    """

    result = {}

    zero = Aff.zero_on_domain(LocalSpace.from_space(space))
    result[0] = PwAff.from_aff(zero)

    var_dict = zero.get_var_dict()
    for name, (dt, idx) in var_dict.items():
        result[name] = PwAff.from_aff(zero.set_coefficient_val(dt, idx, 1))

    return result


class SuppressedWarnings:
    def __init__(self, ctx):
        self.ctx = ctx

    def __enter__(self):
        self.prev_on_error = self.ctx.get_on_error()
        self.ctx.set_on_error(on_error.CONTINUE)

    def __exit__(self, type, value, traceback):
        self.ctx.set_on_error(self.prev_on_error)


# vim: foldmethod=marker
