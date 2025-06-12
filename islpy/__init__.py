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

from collections.abc import Collection, Sequence
from typing import Literal, TypeAlias, TypeVar, cast

from islpy.version import VERSION, VERSION_TEXT


__version__ = VERSION_TEXT

# {{{ name imports

from islpy._isl import (
    AccessInfo,
    Aff,
    AffList,
    AstBuild,
    AstExpr,
    AstExprList,
    AstNode,
    AstNodeList,
    AstPrintOptions,
    BasicMap,
    BasicMapList,
    BasicSet,
    BasicSetList,
    Cell,
    Constraint,
    ConstraintList,
    Context,
    Error,
    FixedBox,
    Flow,
    Id,
    IdList,
    IdToAstExpr,
    LocalSpace,
    Map,
    MapList,
    Mat,
    MultiAff,
    MultiId,
    MultiPwAff,
    MultiUnionPwAff,
    MultiVal,
    Point,
    Printer,
    PwAff,
    PwAffList,
    PwMultiAff,
    PwMultiAffList,
    PwQPolynomial,
    PwQPolynomialFold,
    PwQPolynomialFoldList,
    PwQPolynomialList,
    QPolynomial,
    QPolynomialFold,
    QPolynomialList,
    Restriction,
    Schedule,
    ScheduleConstraints,
    ScheduleNode,
    Set,
    SetList,
    Space,
    StrideInfo,
    Term,
    UnionAccessInfo,
    UnionFlow,
    UnionMap,
    UnionMapList,
    UnionPwAff,
    UnionPwAffList,
    UnionPwMultiAff,
    UnionPwMultiAffList,
    UnionPwQPolynomial,
    UnionPwQPolynomialFold,
    UnionSet,
    UnionSetList,
    Val,
    ValList,
    Vec,
    Vertex,
    Vertices,
    ast_expr_op_type,
    ast_expr_type,
    ast_loop_type,
    ast_node_type,
    bound,
    dim_type,
    error,
    fold,
    format,
    isl_version,
    on_error,
    schedule_algorithm,
    schedule_node_type,
    stat,
    yaml_style,
)

# importing _monkeypatch has the side effect of actually monkeypatching
from islpy._monkeypatch import _CHECK_DIM_TYPES, EXPR_CLASSES


# }}}


# {{{ typing helpers

Alignable: TypeAlias = (
    Space
    | Set | Map
    | BasicSet | BasicMap
    | Aff | PwAff
)
AlignableT = TypeVar("AlignableT", bound=Alignable)
AlignableT2 = TypeVar("AlignableT2", bound=Alignable)

# }}}


DEFAULT_CONTEXT = Context()


def _get_default_context() -> Context:
    """A callable to get the default context for the benefit of Python's
    ``__reduce__`` protocol.
    """
    return DEFAULT_CONTEXT


def _set_dim_id(obj: AlignableT, dt: dim_type, idx: int, id: Id) -> AlignableT:
    if isinstance(obj, BasicSet):
        s = obj.to_set().set_dim_id(dt, idx, id)
        basicsets = s.get_basic_sets()
        if not basicsets:
            result = BasicSet.empty(s.space)
        else:
            result, = basicsets
        return cast("AlignableT", result)
    elif isinstance(obj, BasicMap):
        m = obj.to_map().set_dim_id(dt, idx, id)
        basicmaps = m.get_basic_maps()
        if not basicmaps:
            result = BasicMap.empty(m.space)
        else:
            result, = basicmaps
        return cast("AlignableT", result)

    return cast("AlignableT", obj.set_dim_id(dt, idx, id))


def _align_dim_type(
            template_dt: dim_type,
            obj: AlignableT,
            template: Alignable,
            obj_bigger_ok: bool,
            obj_names: Collection[str],
            template_names: Collection[str],
        ) -> AlignableT:

    # convert to a type that has get_dim_id
    if isinstance(template, BasicSet):
        template = template.to_set()
    elif isinstance(template, BasicMap):
        template = template.to_map()
    elif isinstance(template, Aff):
        template = template.to_pw_aff()

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

    obj_names = set(obj_names) - {None}
    template_names = set(template_names) - {None}

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


def align_spaces(
             obj: AlignableT,
             template: Alignable,
             obj_bigger_ok: bool = False,
         ) -> AlignableT:
    """
    Try to make the space in which *obj* lives the same as that of *template* by
    adding/matching named dimensions.

    :param obj_bigger_ok: If *True*, no error is raised if the resulting *obj*
        has more dimensions than *template*.
    """

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
        dim_types = list(_CHECK_DIM_TYPES)
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


def align_two(
            obj1: AlignableT,
            obj2: AlignableT2,
        ) -> tuple[AlignableT, AlignableT2]:
    """Align the spaces of two objects, potentially modifying both of them.

    See also :func:`align_spaces`.
    """

    obj1 = align_spaces(obj1, obj2, obj_bigger_ok=True)
    obj2 = align_spaces(obj2, obj1, obj_bigger_ok=True)
    return (obj1, obj2)


def make_zero_and_vars(
           set_vars: Sequence[str],
           params: Sequence[str] = (),
           ctx: Context | None = None
       )  -> dict[str | Literal[0], PwAff]:
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


def affs_from_space(space: Space) -> dict[Literal[0] | str, PwAff]:
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


__all__ = (
    "VERSION",
    "VERSION_TEXT",
    "AccessInfo",
    "Aff",
    "AffList",
    "AstBuild",
    "AstExpr",
    "AstExprList",
    "AstNode",
    "AstNodeList",
    "AstPrintOptions",
    "BasicMap",
    "BasicMapList",
    "BasicSet",
    "BasicSetList",
    "Cell",
    "Constraint",
    "ConstraintList",
    "Context",
    "Error",
    "FixedBox",
    "Flow",
    "Id",
    "IdList",
    "IdToAstExpr",
    "LocalSpace",
    "Map",
    "MapList",
    "Mat",
    "MultiAff",
    "MultiId",
    "MultiPwAff",
    "MultiUnionPwAff",
    "MultiVal",
    "Point",
    "Printer",
    "PwAff",
    "PwAffList",
    "PwMultiAff",
    "PwMultiAffList",
    "PwQPolynomial",
    "PwQPolynomialFold",
    "PwQPolynomialFoldList",
    "PwQPolynomialList",
    "QPolynomial",
    "QPolynomialFold",
    "QPolynomialList",
    "Restriction",
    "Schedule",
    "ScheduleConstraints",
    "ScheduleNode",
    "Set",
    "SetList",
    "Space",
    "StrideInfo",
    "Term",
    "UnionAccessInfo",
    "UnionFlow",
    "UnionMap",
    "UnionMapList",
    "UnionPwAff",
    "UnionPwAffList",
    "UnionPwAffList",
    "UnionPwMultiAff",
    "UnionPwMultiAffList",
    "UnionPwQPolynomial",
    "UnionPwQPolynomialFold",
    "UnionSet",
    "UnionSetList",
    "UnionSetList",
    "Val",
    "ValList",
    "Vec",
    "Vertex",
    "Vertices",
    "ast_expr_op_type",
    "ast_expr_type",
    "ast_loop_type",
    "ast_node_type",
    "bound",
    "dim_type",
    "error",
    "fold",
    "format",
    "isl_version",
    "on_error",
    "schedule_algorithm",
    "schedule_node_type",
    "stat",
    "yaml_style",
)

# vim: foldmethod=marker
