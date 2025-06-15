import os
import re
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from functools import update_wrapper
from sys import intern
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Concatenate,
    Literal,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
)
from warnings import warn


if TYPE_CHECKING:
    import islpy._isl as _isl
else:
    import sys
    if "_isl" not in sys.modules:
        import islpy._isl as _isl
    else:
        # This is used for monkeypatching during stub generation.
        # See stubgen/stubgen.py and CMakeLists for orchestration details.
        import _isl


ALL_CLASSES: tuple[type, ...] = tuple(
        getattr(_isl, cls) for cls in dir(_isl) if cls[0].isupper())
EXPR_CLASSES: tuple[type, ...] = tuple(cls for cls in ALL_CLASSES
        if "Aff" in cls.__name__ or "Polynomial" in cls.__name__)
ARITH_CLASSES: tuple[type, ...] = (
    _isl.Aff, _isl.PwAff, _isl.QPolynomial, _isl.PwQPolynomial)

_CHECK_DIM_TYPES: tuple[_isl.dim_type, ...] = (
        _isl.dim_type.in_, _isl.dim_type.param, _isl.dim_type.set)


# {{{ typing helpers

T = TypeVar("T")
P = ParamSpec("P")
ResultT = TypeVar("ResultT")

SelfT = TypeVar("SelfT")

BasicT = TypeVar("BasicT", _isl.BasicSet, _isl.BasicMap)

AffOrConstraintT = TypeVar("AffOrConstraintT", _isl.Aff, _isl.Constraint)
AffLikeT = TypeVar("AffLikeT", _isl.Aff, _isl.PwAff)
ExprLike: TypeAlias = _isl.Aff | _isl.PwAff | _isl.QPolynomial | _isl.PwQPolynomial
ExprLikeT = TypeVar("ExprLikeT", _isl.Aff, _isl.PwAff,
                   _isl.QPolynomial, _isl.PwQPolynomial
               )
SetLikeT = TypeVar("SetLikeT", bound=_isl.BasicSet | _isl.Set)

SetOrBasic: TypeAlias = _isl.BasicSet | _isl.Set
SetOrBasicT = TypeVar("SetOrBasicT", bound=SetOrBasic)

MapOrBasic: TypeAlias = _isl.BasicMap | _isl.Map
MapOrBasicT = TypeVar("MapOrBasicT", bound=MapOrBasic)

SetOrMap: TypeAlias = _isl.BasicSet | _isl.Set | _isl.BasicMap | _isl.Map
SetOrMapT = TypeVar("SetOrMapT", _isl.BasicSet, _isl.Set, _isl.BasicMap, _isl.Map)

HasSpace: TypeAlias = (
    _isl.Space
    | _isl.Constraint
    | _isl.LocalSpace
    | _isl.Aff
    | _isl.MultiAff
    | _isl.PwAff
    | _isl.PwMultiAff
    | _isl.BasicMap
    | _isl.BasicSet
    | _isl.Set
    | _isl.Map
    )


class IslObject(Protocol):
    def get_ctx(self) -> _isl.Context:
        ...

    def _wraps_same_instance_as(self, other: object) -> bool:
        ...

    _base_name: ClassVar[str]

# }}}


# {{{ copied verbatim from pytools to avoid numpy/pytools dependency

class _HasKwargs:
    pass


def _memoize_on_first_arg(
        function: Callable[Concatenate[T, P], ResultT], *,
        cache_dict_name: str | None = None) -> Callable[Concatenate[T, P], ResultT]:
    """Like :func:`memoize_method`, but for functions that take the object
    in which do memoization information is stored as first argument.

    Supports cache deletion via ``function_name.clear_cache(self)``.
    """

    if cache_dict_name is None:
        cache_dict_name = intern(
                f"_memoize_dic_{function.__module__}{function.__name__}"
                )

    def wrapper(obj: T, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        key = (_HasKwargs, frozenset(kwargs.items()), *args) if kwargs else args

        assert cache_dict_name is not None
        try:
            return cast("ResultT", getattr(obj, cache_dict_name)[key])
        except AttributeError:
            attribute_error = True
        except KeyError:
            attribute_error = False

        result = function(obj, *args, **kwargs)
        if attribute_error:
            object.__setattr__(obj, cache_dict_name, {key: result})
            return result
        getattr(obj, cache_dict_name)[key] = result
        return result

    def clear_cache(obj: object):
        object.__delattr__(obj, cache_dict_name)

    from functools import update_wrapper
    new_wrapper = update_wrapper(wrapper, function)

    # type-ignore because mypy has a point here, stuffing random attributes
    # into the function's dict is moderately sketchy.
    new_wrapper.clear_cache = clear_cache  # type: ignore[attr-defined]

    return new_wrapper


# }}}


def _read_from_str_wrapper(cls, context, s, dims_with_apostrophes):
    """A callable to reconstitute instances from strings for the benefit
    of Python's ``__reduce__`` protocol.
    """
    cls_from_str = cls.read_from_str(context, s)

    # Apostrophes in dim names have been lost, put them back
    for dim_name, (dt, dim_idx) in dims_with_apostrophes.items():
        cls_from_str = cls_from_str.set_dim_name(dt, dim_idx, dim_name)

    return cls_from_str


def dim_type_reduce(self: _isl.dim_type):
    return (_isl.dim_type, (int(self),))


def context_reduce(self: _isl.Context):
    from islpy import DEFAULT_CONTEXT, _get_default_context
    if self._wraps_same_instance_as(DEFAULT_CONTEXT):
        return (_get_default_context, ())
    else:
        return (_isl.Context, ())


def context_eq(self: IslObject, other: object):
    return isinstance(other, _isl.Context) and self._wraps_same_instance_as(other)


def context_ne(self: object, other: object) -> bool:
    return not self.__eq__(other)


def generic_reduce(self: HasSpace):
    ctx = self.get_ctx()
    prn = _isl.Printer.to_str(ctx)
    prn = getattr(prn, f"print_{self._base_name}")(self)

    # Reconstructing from string will remove apostrophes in dim names,
    # so keep track of dim names with apostrophes
    dims_with_apostrophes = {
        dname: pos for dname, pos in self.get_var_dict().items()
        if "'" in dname}

    return (
        _read_from_str_wrapper,
        (type(self), ctx, prn.get_str(), dims_with_apostrophes))


def generic_str(self: IslObject) -> str:
    prn = _isl.Printer.to_str(self.get_ctx())
    getattr(prn, f"print_{self._base_name}")(self)
    return prn.get_str()


def generic_repr(self: IslObject) -> str:
    prn = _isl.Printer.to_str(self.get_ctx())
    getattr(prn, f"print_{self._base_name}")(self)
    return f'{type(self).__name__}("{prn.get_str()}")'


def space_get_id_dict(
            self: _isl.Space,
            dimtype: _isl.dim_type | None = None
        ) -> Mapping[_isl.Id, tuple[_isl.dim_type, int]]:
    """Return a dictionary mapping variable :class:`Id` instances to tuples
    of (:class:`dim_type`, index).

    :param dimtype: None to get all variables, otherwise
        one of :class:`dim_type`.
    """
    result = {}

    def set_dim_id(name, tp, idx):
        if name in result:
            raise RuntimeError(f"non-unique var id '{name}' encountered")
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


def space_get_var_dict(
            self: _isl.Space,
            dimtype: _isl.dim_type | None = None,
            ignore_out: bool = False
        ) -> Mapping[str, tuple[_isl.dim_type, int]]:
    """Return a dictionary mapping variable names to tuples of
    (:class:`dim_type`, index).

    :param dimtype: None to get all variables, otherwise
        one of :class:`dim_type`.
    """
    result: dict[str, tuple[_isl.dim_type, int]] = {}

    def set_dim_name(name: str, tp: _isl.dim_type, idx: int):
        if name in result:
            raise RuntimeError(f"non-unique var name '{name}' encountered")
        result[name] = tp, idx

    if dimtype is None:
        types = list(_CHECK_DIM_TYPES)
        if ignore_out:
            types = types[:]
            types.remove(_isl.dim_type.out)
    else:
        types = [dimtype]

    for tp in types:
        for i in range(self.dim(tp)):
            name = self.get_dim_name(tp, i)
            if name is not None:
                set_dim_name(name, tp, i)

    return result


def space_create_from_names(
            ctx: _isl.Context,
            set: Sequence[str] | None = None,
            in_: Sequence[str] | None = None,
            out: Sequence[str] | None = None,
            params: Sequence[str] = ()
        ) -> _isl.Space:
    """Create a :class:`Space` from lists of variable names.

    :param set_: names of `set`-type variables.
    :param in_: names of `in`-type variables.
    :param out: names of `out`-type variables.
    :param params: names of parameter-type variables.
    """
    dt = _isl.dim_type

    if set is not None:
        if in_ is not None or out is not None:
            raise RuntimeError("must pass only one of set / (in_,out)")

        result = _isl.Space.set_alloc(ctx, nparam=len(params),
                dim=len(set))

        for i, name in enumerate(set):
            result = result.set_dim_name(dt.set, i, name)

    elif in_ is not None and out is not None:
        if set is not None:
            raise RuntimeError("must pass only one of set / (in_,out)")

        result = _isl.Space.alloc(ctx, nparam=len(params),
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


def set_or(
            self: _isl.Set,
            other: _isl.Set | _isl.BasicSet,
        ) -> _isl.Set:
    try:
        return self.union(other)
    except TypeError:
        return NotImplemented


def bset_and(
            self: _isl.BasicSet,
            other: SetOrBasicT,
        ) -> SetOrBasicT:
    if isinstance(other, _isl.Set):
        try:
            return self.to_set().intersect(other)
        except TypeError:
            return NotImplemented
    else:
        try:
            return self.intersect(other)
        except TypeError:
            return NotImplemented


def set_and(
            self: _isl.Set,
            other: _isl.Set | _isl.BasicSet,
        ) -> _isl.Set:
    if isinstance(self, _isl.BasicSet):
        self = self.to_set()
    try:
        return self.intersect(other)
    except TypeError:
        return NotImplemented


def set_sub(
            self: _isl.Set | _isl.BasicSet,
            other: _isl.Set | _isl.BasicSet,
        ) -> _isl.Set:
    if isinstance(self, _isl.BasicSet):
        self = self.to_set()
    try:
        return self.subtract(other)
    except TypeError:
        return NotImplemented


def map_or(
            self: _isl.Map | _isl.BasicMap,
            other: _isl.Map | _isl.BasicMap,
        ) -> _isl.Map:
    if isinstance(self, _isl.BasicMap):
        self = self.to_map()
    try:
        return self.union(other)
    except TypeError:
        return NotImplemented


def bmap_and(
            self: _isl.BasicMap,
            other: MapOrBasicT,
        ) -> MapOrBasicT:
    if isinstance(other, _isl.Map):
        try:
            return self.to_map().intersect(other)
        except TypeError:
            return NotImplemented
    else:
        try:
            return self.intersect(other)
        except TypeError:
            return NotImplemented


def map_and(
            self: _isl.Map,
            other: _isl.Map | _isl.BasicMap,
        ) -> _isl.Map:
    try:
        return self.intersect(other)
    except TypeError:
        return NotImplemented


def map_sub(
            self: _isl.Map | _isl.BasicMap,
            other: _isl.Map | _isl.BasicMap,
        ) -> _isl.Map:
    if isinstance(self, _isl.BasicMap):
        self = self.to_map()
    try:
        return self.subtract(other)
    except TypeError:
        return NotImplemented


def obj_set_coefficients(
            self: AffOrConstraintT,
            dim_tp: _isl.dim_type,
            args: Sequence[_isl.Val | int],
        ) -> AffOrConstraintT:
    """
    :param dim_tp: :class:`dim_type`
    :param args: :class:`list` of coefficients, for indices `0..len(args)-1`.

    .. versionchanged:: 2011.3
        New for :class:`Aff`
    """
    for i, coeff in enumerate(args):
        self = self.set_coefficient_val(dim_tp, i, coeff)

    return self


def obj_set_coefficients_by_name(
            self: AffOrConstraintT,
            iterable: Iterable[tuple[str | Literal[1], _isl.Val | int]]
                | Mapping[str | Literal[1], _isl.Val | int],
            name_to_dim: Mapping[str, tuple[_isl.dim_type, int]] | None = None,
        ) -> AffOrConstraintT:
    """Set the coefficients and the constant.

    :param iterable: a :class:`dict` or iterable of :class:`tuple`
        instances mapping variable names to their coefficients.
        The constant is set to the value of the key '1'.

    .. versionchanged:: 2011.3
        New for :class:`Aff`
    """
    try:
        coeff_iterable: Iterable[tuple[str | Literal[1], _isl.Val | int]] = \
            list(iterable.items())
    except AttributeError:
        coeff_iterable = \
            cast("Iterable[tuple[str | Literal[1], _isl.Val | int]]", iterable)

    if name_to_dim is None:
        name_to_dim = obj_get_var_dict(self)

    for name, coeff in coeff_iterable:
        if name == 1:
            self = self.set_constant_val(coeff)
        else:
            assert name
            tp, idx = name_to_dim[name]
            self = self.set_coefficient_val(tp, idx, coeff)

    return self


def obj_get_coefficients_by_name(
            self: _isl.Constraint | _isl.Aff,
            dimtype: _isl.dim_type | None = None,
            dim_to_name: Mapping[tuple[_isl.dim_type, int], str] | None = None,
        ) -> dict[str | Literal[1], _isl.Val]:
    """Return a dictionary mapping variable names to coefficients.

    :param dimtype: None to get all variables, otherwise
        one of :class:`dim_type`.

    .. versionchanged:: 2011.3
        New for :class:`Aff`
    """
    if dimtype is None:
        types: Sequence[_isl.dim_type] = _CHECK_DIM_TYPES
    else:
        types = [dimtype]

    result: dict[Literal[1] | str, _isl.Val] = {}
    for tp in types:
        for i in range(self.get_space().dim(tp)):
            coeff = self.get_coefficient_val(tp, i)
            if coeff:
                if dim_to_name is None:
                    name = self.get_dim_name(tp, i)
                    assert name
                else:
                    name = dim_to_name[tp, i]

                result[name] = coeff

    const = self.get_constant_val()
    if const:
        result[1] = const

    return result


def eq_from_names(
            space: _isl.Space,
            coefficients: Mapping[str | Literal[1], _isl.Val | int] | None = None
        ) -> _isl.Constraint:
    """Create a constraint `const + coeff_1*var_1 +... == 0`.

    :param space: :class:`Space`
    :param coefficients: a :class:`dict` or iterable of :class:`tuple`
        instances mapping variable names to their coefficients
        The constant is set to the value of the key '1'.

    .. versionchanged:: 2011.3
        Eliminated the separate *const* parameter.
    """
    if coefficients is None:
        coefficients = {}
    c = _isl.Constraint.equality_alloc(space)
    return obj_set_coefficients_by_name(c, coefficients)


def ineq_from_names(
            space: _isl.Space,
            coefficients: Mapping[str | Literal[1], _isl.Val | int] | None = None
        ) -> _isl.Constraint:
    """Create a constraint `const + coeff_1*var_1 +... >= 0`.

    :param space: :class:`Space`
    :param coefficients: a :class:`dict` or iterable of :class:`tuple`
        instances mapping variable names to their coefficients
        The constant is set to the value of the key '1'.

    .. versionchanged:: 2011.3
        Eliminated the separate *const* parameter.
    """
    if coefficients is None:
        coefficients = {}
    c = _isl.Constraint.inequality_alloc(space)
    return obj_set_coefficients_by_name(c, coefficients)


def basic_obj_get_constraints(
            self: _isl.BasicSet | _isl.BasicMap
        ) -> list[_isl.Constraint]:
    """Get a list of constraints."""
    result: list[_isl.Constraint] = []
    self.foreach_constraint(result.append)
    return result


def set_get_basic_sets(self: _isl.Set | _isl.BasicSet) -> list[_isl.BasicSet]:
    """Get the list of :class:`BasicSet` instances in this :class:`Set`."""
    result: list[_isl.BasicSet] = []
    self.foreach_basic_set(result.append)
    return result


def map_get_basic_maps(self: _isl.Map) -> list[_isl.BasicMap]:
    """Get the list of :class:`BasicMap` instances in this :class:`Map`."""
    result: list[_isl.BasicMap] = []
    self.foreach_basic_map(result.append)
    return result


def obj_get_id_dict(
            self: HasSpace,
            dimtype: _isl.dim_type | None = None
        ) -> Mapping[_isl.Id, tuple[_isl.dim_type, int]]:
    """Return a dictionary mapping :class:`Id` instances to tuples of
    (:class:`dim_type`, index).

    :param dimtype: None to get all variables, otherwise
        one of :class:`dim_type`.
    """
    return self.get_space().get_id_dict(dimtype)


@_memoize_on_first_arg
def obj_get_var_dict(
            self: HasSpace,
            dimtype: _isl.dim_type | None = None
        ) -> Mapping[str, tuple[_isl.dim_type, int]]:
    """Return a dictionary mapping variable names to tuples of
    (:class:`dim_type`, index).

    :param dimtype: None to get all variables, otherwise
        one of :class:`dim_type`.
    """
    return self.get_space().get_var_dict(
            dimtype, ignore_out=isinstance(self, EXPR_CLASSES))


def obj_get_var_ids(
            self: HasSpace,
            dimtype: _isl.dim_type
        ) -> Sequence[str | None]:
    """Return a list of :class:`Id` instances for :class:`dim_type` *dimtype*."""
    return [
        self.get_dim_name(dimtype, i)
        for i in range(self.dim(dimtype))]


@_memoize_on_first_arg
def obj_get_var_names_not_none(
            self: HasSpace,
            dimtype: _isl.dim_type,
        ) -> Sequence[str]:
    """Return a list of dim names (in order) for :class:`dim_type` *dimtype*.

    Raise :exc:`ValueError` if any of the names is *None*.

    .. versionadded:: 2025.2.5
    """
    ndim = self.dim(dimtype)
    res = [n
        for i in range(ndim)
        if (n := self.get_dim_name(dimtype, i)) is not None]
    if len(res) != ndim:
        raise ValueError("None encountered in dim names")
    return res


@_memoize_on_first_arg
def obj_get_var_names(
            self: HasSpace,
            dimtype: _isl.dim_type,
        ) -> Sequence[str | None]:
    """Return a list of dim names (in order) for :class:`dim_type` *dimtype*.
    """
    return [self.get_dim_name(dimtype, i)
            for i in range(self.dim(dimtype))]


def pwaff_get_pieces(self: _isl.PwAff | _isl.Aff) -> list[tuple[_isl.Set, _isl.Aff]]:
    if isinstance(self, _isl.Aff):
        self = self.to_pw_aff()
    result: list[tuple[_isl.Set, _isl.Aff]] = []

    def append_tuple(s: _isl.Set, v: _isl.Aff):
        result.append((s, v))

    self.foreach_piece(append_tuple)
    return result


def pwqpolynomial_get_pieces(
            self: _isl.PwQPolynomial
        ) -> list[tuple[_isl.Set, _isl.QPolynomial]]:
    """
    :return: list of (:class:`Set`, :class:`QPolynomial`)
    """

    result: list[tuple[_isl.Set, _isl.QPolynomial]] = []

    def append_tuple(s: _isl.Set, v: _isl.QPolynomial):
        result.append((s, v))

    self.foreach_piece(append_tuple)
    return result


def pw_get_aggregate_domain(self: _isl.PwAff | _isl.PwQPolynomial) -> _isl.Set:
    """
    :return: a :class:`Set` that is the union of the domains of all pieces
    """

    result = _isl.Set.empty(self.get_domain_space())
    for dom, _ in self.get_pieces():
        result = result.union(dom)

    return result


def qpolynomial_get_terms(self: _isl.QPolynomial) -> list[_isl.Term]:
    """Get the list of :class:`Term` instances in this :class:`QPolynomial`."""
    result: list[_isl.Term] = []
    self.foreach_term(result.append)
    return result


def pwqpolynomial_eval_with_dict(
            self: _isl.PwQPolynomial,
            value_dict: Mapping[str, int | _isl.Val]
        ) -> int:
    """Evaluates *self* for the parameters specified by
    *value_dict*, which maps parameter names to their values.
    """

    pt = _isl.Point.zero(self.space.params())

    for i in range(self.space.dim(_isl.dim_type.param)):
        par_name = self.space.get_dim_name(_isl.dim_type.param, i)
        assert par_name
        pt = pt.set_coordinate_val(
            _isl.dim_type.param, i, value_dict[par_name])

    return self.eval(pt).to_python()


def _number_to_expr_like(template: ExprLikeT, num: int | _isl.Val) -> ExprLikeT:
    number_aff = _isl.Aff.zero_on_domain(template.get_domain_space())
    number_aff = number_aff.set_constant_val(num)

    if isinstance(template, _isl.Aff):
        return number_aff
    if isinstance(template, _isl.QPolynomial):
        return _isl.QPolynomial.from_aff(number_aff)

    # everything else is piecewise

    if template.get_pieces():
        number_pw_aff = _isl.PwAff.empty(template.get_space())
        for set, _ in template.get_pieces():
            number_pw_aff = set.indicator_function().cond(
                    number_aff, number_pw_aff)
    else:
        number_pw_aff = _isl.PwAff.alloc(
                _isl.Set.universe(template.domain().space),
                number_aff)

    if isinstance(template, _isl.PwAff):
        return number_pw_aff

    elif isinstance(template, _isl.PwQPolynomial):
        return _isl.PwQPolynomial.from_pw_aff(number_pw_aff)

    else:
        raise TypeError("unexpected template type")


def expr_like_add(self: ExprLikeT, other: ExprLikeT | int | _isl.Val) -> ExprLikeT:
    if not isinstance(other, ExprLike):
        other = _number_to_expr_like(self, other)

    try:
        return self.add(other)
    except TypeError:
        return NotImplemented


def expr_like_sub(self: ExprLikeT, other: ExprLikeT | int | _isl.Val) -> ExprLikeT:
    if not isinstance(other, ExprLike):
        other = _number_to_expr_like(self, other)

    try:
        return self.sub(other)
    except TypeError:
        return NotImplemented


def expr_like_rsub(self: ExprLikeT, other: ExprLikeT | int | _isl.Val) -> ExprLikeT:
    if not isinstance(other, ExprLike):
        other = _number_to_expr_like(self, other)

    return -self + other


def expr_like_mul(self: ExprLikeT, other: ExprLikeT | int | _isl.Val) -> ExprLikeT:
    if not isinstance(other, ExprLike):
        other = _number_to_expr_like(self, other)

    try:
        return self.mul(other)
    except TypeError:
        return NotImplemented


def expr_like_floordiv(self: AffLikeT, other: _isl.Val) -> AffLikeT:
    return self.scale_down_val(other).floor()


def val_rsub(self: _isl.Val, other: _isl.Val) -> _isl.Val:
    return -self + other


def val_bool(self: _isl.Val) -> bool:
    return not self.is_zero()


def val_repr(self: _isl.Val) -> str:
    return f'{type(self).__name__}("{self.to_str()}")'


def val_to_python(self: _isl.Val) -> int:
    if not self.is_int():
        raise ValueError("can only convert integer Val to python")

    return int(self.to_str())


def obj_eq(self: IslObject, other: object) -> bool:
    assert self.get_ctx() == other.get_ctx(), (
            "Equality-comparing two objects from different ISL Contexts "
            "will likely lead to entertaining (but never useful) results. "
            "In particular, Spaces with matching names will no longer be "
            "equal.")

    return self.is_equal(other)


def obj_ne(self: object, other: object) -> bool:
    return not self.__eq__(other)


for cls in ALL_CLASSES:
    if hasattr(cls, "is_equal"):
        cls.__eq__ = obj_eq
        cls.__ne__ = obj_ne


def set_lt(self: _isl.BasicSet | _isl.Set, other: _isl.BasicSet | _isl.Set) -> bool:
    return self.is_strict_subset(other)


def set_le(self: _isl.BasicSet | _isl.Set, other: _isl.BasicSet | _isl.Set) -> bool:
    return self.is_subset(other)


def set_gt(self: _isl.BasicSet | _isl.Set, other: _isl.BasicSet | _isl.Set) -> bool:
    return other.is_strict_subset(self)


def set_ge(self: _isl.BasicSet | _isl.Set, other: _isl.BasicSet | _isl.Set) -> bool:
    return other.is_subset(self)


def map_lt(self: _isl.BasicMap | _isl.Map, other: _isl.BasicMap | _isl.Map) -> bool:
    return self.is_strict_subset(other)


def map_le(self: _isl.BasicMap | _isl.Map, other: _isl.BasicMap | _isl.Map) -> bool:
    return self.is_subset(other)


def map_gt(self: _isl.BasicMap | _isl.Map, other: _isl.BasicMap | _isl.Map) -> bool:
    return other.is_strict_subset(self)


def map_ge(self: _isl.BasicMap | _isl.Map, other: _isl.BasicMap | _isl.Map) -> bool:
    return other.is_subset(self)


# {{{ project_out_except

def obj_project_out_except(
            obj: SetOrMapT,
            names: Collection[str],
            types: Collection[_isl.dim_type]
        ) -> SetOrMapT:
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
            leftover_indices = {var_dict[name][1] for name in names
                    if name in var_dict}
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

def obj_eliminate_except(
            obj: SetOrMapT,
            names: Collection[str],
            types: Collection[_isl.dim_type]
        ) -> SetOrMapT:
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
                - {var_dict[name][1] for name in names
                    if name in var_dict})

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

def obj_add_constraints(obj: BasicT, constraints: Iterable[_isl.Constraint]) -> BasicT:
    """
    .. versionadded:: 2011.3
    """

    for cns in constraints:
        obj = obj.add_constraint(cns)

    return obj

# }}}


def _add_functionality() -> None:
    _isl.dim_type.__reduce__ = dim_type_reduce

    # {{{ Context

    _isl.Context.__reduce__ = context_reduce
    _isl.Context.__eq__ = context_eq
    _isl.Context.__ne__ = context_ne

    # }}}

    # {{{ generic initialization, pickling

    for cls in ALL_CLASSES:
        if hasattr(cls, "read_from_str"):
            cls.__reduce__ = generic_reduce

    # }}}

    # {{{ printing

    for cls in ALL_CLASSES:
        if (hasattr(cls, "_base_name")
                and hasattr(_isl.Printer, f"print_{cls._base_name}")):
            cls.__str__ = generic_str
            cls.__repr__ = generic_repr

        if not hasattr(cls, "__hash__"):
            raise AssertionError(f"not hashable: {cls}")

    # }}}

    # {{{ Python set-like behavior

    _isl.BasicSet.__and__ = bset_and
    _isl.BasicSet.__rand__ = bset_and
    _isl.Set.__and__ = set_and
    _isl.Set.__rand__ = set_and
    for cls in [_isl.BasicSet, _isl.Set]:
        cls.__or__ = set_or
        cls.__ror__ = set_or
        cls.__sub__ = set_sub

    _isl.BasicMap.__and__ = bmap_and
    _isl.BasicMap.__rand__ = bmap_and
    _isl.Map.__and__ = map_and
    _isl.Map.__rand__ = map_and
    for cls in [_isl.BasicMap, _isl.Map]:
        cls.__or__ = map_or
        cls.__ror__ = map_or
        cls.__sub__ = map_sub

    # }}}

    # {{{ Space

    _isl.Space.create_from_names = staticmethod(space_create_from_names)
    _isl.Space.get_var_dict = space_get_var_dict
    _isl.Space.get_id_dict = space_get_id_dict

    # }}}

    # {{{ coefficient wrangling

    for coeff_class in [_isl.Constraint, _isl.Aff]:
        coeff_class.set_coefficients = obj_set_coefficients
        coeff_class.set_coefficients_by_name = obj_set_coefficients_by_name
        coeff_class.get_coefficients_by_name = obj_get_coefficients_by_name

    # }}}

    # {{{ Constraint

    _isl.Constraint.eq_from_names = staticmethod(eq_from_names)
    _isl.Constraint.ineq_from_names = staticmethod(ineq_from_names)

    # }}}

    # {{{ BasicSet

    _isl.BasicSet.get_constraints = basic_obj_get_constraints

    # }}}

    # {{{ BasicMap

    _isl.BasicMap.get_constraints = basic_obj_get_constraints

    # }}}

    # {{{ Set

    _isl.Set.get_basic_sets = set_get_basic_sets
    _isl.BasicSet.get_basic_sets = set_get_basic_sets

    # }}}

    # {{{ Map

    _isl.Map.get_basic_maps = map_get_basic_maps

    # }}}


# {{{ common functionality

for cls in ALL_CLASSES:
    if hasattr(cls, "get_space") and cls is not _isl.Space:
        cls.get_id_dict = obj_get_id_dict
        cls.get_var_dict = obj_get_var_dict
        cls.get_var_ids = obj_get_var_ids
        cls.get_var_names = obj_get_var_names
        cls.get_var_names_not_none = obj_get_var_names_not_none

    # }}}

    # {{{ piecewise

    _isl.PwAff.get_pieces = pwaff_get_pieces
    _isl.Aff.get_pieces = pwaff_get_pieces
    _isl.PwAff.get_aggregate_domain = pw_get_aggregate_domain

    _isl.PwQPolynomial.get_pieces = pwqpolynomial_get_pieces
    _isl.PwQPolynomial.get_aggregate_domain = pw_get_aggregate_domain

    # }}}

    _isl.QPolynomial.get_terms = qpolynomial_get_terms

    _isl.PwQPolynomial.eval_with_dict = pwqpolynomial_eval_with_dict

    # {{{ arithmetic

    for expr_like_class in ARITH_CLASSES:
        expr_like_class.__add__ = expr_like_add
        expr_like_class.__radd__ = expr_like_add
        expr_like_class.__sub__ = expr_like_sub
        expr_like_class.__rsub__ = expr_like_rsub
        expr_like_class.__mul__ = expr_like_mul
        expr_like_class.__rmul__ = expr_like_mul
        expr_like_class.__neg__ = expr_like_class.neg

    for qpoly_class in [_isl.QPolynomial, _isl.PwQPolynomial]:
        qpoly_class.__pow__ = qpoly_class.pow

    for aff_class in [_isl.Aff, _isl.PwAff]:
        aff_class.__mod__ = aff_class.mod_val
        aff_class.__floordiv__ = expr_like_floordiv

    # }}}

    # {{{ Val

    val_cls = _isl.Val

    val_cls.__add__ = val_cls.add
    val_cls.__radd__ = val_cls.add
    val_cls.__sub__ = val_cls.sub
    val_cls.__rsub__ = val_rsub
    val_cls.__mul__ = val_cls.mul
    val_cls.__rmul__ = val_cls.mul
    val_cls.__neg__ = val_cls.neg
    val_cls.__mod__ = val_cls.mod
    val_cls.__bool__ = val_cls.__nonzero__ = val_bool

    val_cls.__lt__ = val_cls.lt
    val_cls.__gt__ = val_cls.gt
    val_cls.__le__ = val_cls.le
    val_cls.__ge__ = val_cls.ge
    val_cls.__eq__ = val_cls.eq
    val_cls.__ne__ = val_cls.ne

    val_cls.__repr__ = val_repr
    val_cls.__str__ = val_cls.to_str
    val_cls.to_python = val_to_python

    # }}}

    # {{{ rich comparisons

    for cls in [_isl.BasicSet, _isl.Set]:
        cls.__lt__ = set_lt
        cls.__le__ = set_le
        cls.__gt__ = set_gt
        cls.__ge__ = set_ge

    for cls in [_isl.BasicMap, _isl.Map]:
        cls.__lt__ = map_lt
        cls.__le__ = map_le
        cls.__gt__ = map_gt
        cls.__ge__ = map_ge

    # }}}

    for c in [_isl.BasicSet, _isl.BasicMap, _isl.Set, _isl.Map]:
        c.project_out_except = obj_project_out_except
        c.add_constraints = obj_add_constraints

    for c in [_isl.BasicSet, _isl.Set]:
        c.eliminate_except = obj_eliminate_except


_add_functionality()


_DOWNCAST_RE = re.compile(
          r"Downcast from :class:`([A-Za-z]+)` to :class:`([A-Za-z]+)`.")


_TO_METHODS = {
    "PwAff": "to_pw_aff",
    "PwMultiAff": "to_pw_multi_aff",
    "UnionPwAff": "to_union_pw_aff",
    "UnionPwMultiAff": "to_union_pw_multi_aff",
    "LocalSpace": "to_local_space",
    "Set": "to_set",
    "UnionSet": "to_union_set",
    "Map": "to_map",
    "UnionMap": "to_union_map",
}


def _depr_downcast_wrapper(
            f: Callable[Concatenate[object, P], ResultT],
        ) -> Callable[Concatenate[object, P], ResultT]:
    doc = f.__doc__
    assert doc is not None
    m = _DOWNCAST_RE.search(doc)
    assert m, doc
    basic_cls_name = intern(m.group(1))
    tgt_cls_name = m.group(2)

    tgt_cls = cast("type", getattr(_isl, tgt_cls_name))
    is_overload = "Overloaded function" in doc
    msg = (f"{basic_cls_name}.{f.__name__} "
            f"with implicit conversion of self to {tgt_cls_name} is deprecated "
            "and will stop working in 2026. "
            f"Explicitly convert to {tgt_cls_name}, "
            f"using .{_TO_METHODS[tgt_cls_name]}().")

    if is_overload:
        def wrapper(self: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
            # "Try to" detect bad invocations of, e.g., Set.union, which is
            # an overload of normal union and UnionSet.union.
            if (
                    any(isinstance(arg, tgt_cls) for arg in args)
                    or
                    any(isinstance(arg, tgt_cls) for arg in kwargs.values())
                    ):
                warn(msg, DeprecationWarning, stacklevel=2)

            return f(self, *args, **kwargs)
    else:
        def wrapper(self: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
            warn(msg, DeprecationWarning, stacklevel=2)

            return f(self, *args, **kwargs)
    update_wrapper(wrapper, f)
    return wrapper


def _monkeypatch_self_downcast_deprecation():
    for cls in ALL_CLASSES:
        for attr_name in dir(cls):
            val = cast("object", getattr(cls, attr_name))
            doc = getattr(val, "__doc__", None)
            if doc and "\nDowncast from " in doc:
                setattr(cls, attr_name, _depr_downcast_wrapper(
                        cast("Callable", val),  # pyright: ignore[reportMissingTypeArgument]
                        ))


if not os.environ.get("ISLPY_NO_DOWNCAST_DEPRECATION", None):
    _monkeypatch_self_downcast_deprecation()
