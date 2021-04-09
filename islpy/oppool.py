__copyright__ = "Copyright (C) 2021 Kaushik Kulkarni"

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


from pytools import memoize_method
import islpy as isl
from dataclasses import dataclass, field
from typing import Union, Dict, Any, Optional, Tuple, FrozenSet, List
from pytools import UniqueNameGenerator


BaseType = Union[isl.Aff, isl.BasicSet, isl.Set, isl.BasicMap, isl.Map]
BASE_CLASSES = (isl.Aff, isl.BasicSet, isl.Set, isl.BasicMap, isl.Map)


def _gen_name(vng: UniqueNameGenerator, dt: isl.dim_type):
    if dt == isl.dim_type.param:
        return vng("param")
    elif dt == isl.dim_type.out:
        return vng("out")
    elif dt == isl.dim_type.in_:
        return vng("in")
    else:
        raise NotImplementedError(dt)


def normalize(obj: BaseType) -> Tuple[BaseType, Dict[str, str]]:
    vng = UniqueNameGenerator(forced_prefix="_islpy")

    lift_map = {}
    new_obj = obj

    for dt in [isl.dim_type.in_, isl.dim_type.out, isl.dim_type.div,
               isl.dim_type.param]:
        for pos in range(obj.dim(dt)):
            new_name = _gen_name(vng, dt)
            old_name = obj.get_dim_name(dt, pos) or new_name
            new_obj = new_obj.set_dim_name(dt, pos, new_name)
            lift_map[new_name] = old_name

    return new_obj, lift_map


def normalize_binary_isl_obj(obj1: "NormalizedISLObj",
                             obj2: "NormalizedISLObj") -> Tuple["NormalizedISLObj",
                                                                "NormalizedISLObj"]:
    vng = UniqueNameGenerator(forced_prefix="_islpy")
    lift_map1 = {}
    lift_map2 = {}
    unlift_map1 = {}

    # FIXME: What if these liftings turn out to be expensive?
    new_obj1 = obj1.lift()
    new_obj2 = obj2.lift()

    for old_name, (dt, pos) in new_obj1.get_var_dict().items():
        new_name = _gen_name(vng, dt)
        if not isinstance(new_obj1, isl.PwAff):
            new_obj1 = new_obj1.set_dim_name(dt, pos, new_name)
        else:
            new_obj1 = new_obj1.set_dim_id(dt, pos,
                                           isl.Id.read_from_str(new_obj1.get_ctx(),
                                                                new_name))
        lift_map1[new_name] = old_name
        unlift_map1[old_name] = new_name

    for old_name, (dt, pos) in new_obj2.get_var_dict().items():
        new_name = unlift_map1.get(old_name) or _gen_name(vng, dt)
        if not isinstance(new_obj2, isl.PwAff):
            new_obj2 = new_obj2.set_dim_name(dt, pos, new_name)
        else:
            new_obj2 = new_obj2.set_dim_id(dt, pos,
                                           isl.Id.read_from_str(new_obj2.get_ctx(),
                                                                new_name))
        lift_map2[new_name] = old_name

    return (obj1.copy(new_obj1, lift_map1),
            obj2.copy(new_obj2, lift_map2))


def normalize_based_on_template(obj: "NormalizedISLObj",
                                tmpl: "NormalizedISLObj") -> "NormalizedISLObj":
    """
    Like :func:`normalize_binary_isl_obj`, but obj1 does not support set_dim_name.
    """
    assert set(obj.lift_map.values()) == set(tmpl.lift_map.values())
    obj_var_dict = obj.ground_obj.get_var_dict()
    new_ground = obj.ground_obj
    for name_in_tmplt_grnd, name in tmpl.lift_map.items():
        name_in_obj_grnd = obj.unlift_map[name]
        dt, pos = obj_var_dict[name_in_obj_grnd]
        new_ground = new_ground.set_dim_name(dt, pos, name_in_tmplt_grnd)

    return obj.copy(new_ground, tmpl.lift_map)


@dataclass
class ISLOpMemoizer:
    """
    A memoizer for ISL operations.
    """
    cache: Dict[Any, Any] = field(default_factory=dict)

    def __call__(self, f, args: Tuple[Any, ...]):
        try:
            return self.cache[(str(f), args)]
        except KeyError:
            result = f(*args)
            self.cache[(str(f), args)] = result
            return result


@dataclass
class NormalizedISLObj:
    ground_obj: BaseType
    lift_map: Dict[str, str]

    def lift(self) -> BaseType:
        new_obj = self.ground_obj

        for old_name, (dt, pos) in new_obj.get_var_dict().items():
            new_obj = new_obj.set_dim_name(dt, pos, self.lift_map[old_name])

        return new_obj

    @classmethod
    def unlift(cls, obj: BaseType) -> "NormalizedISLObj":
        ground_obj, lift_map = normalize(obj)
        return BasicSet(ground_obj, lift_map)

    @property
    @memoize_method
    def unlift_map(self) -> Dict[str, str]:
        return {v: k for k, v in self.lift_map.items()}

    def copy(self, ground_obj: Optional[BaseType] = None,
             lift_map: Optional[Dict[str, str]] = None) -> "NormalizedISLObj":
        if ground_obj is None:
            ground_obj = self.ground_obj
        if lift_map is None:
            lift_map = self.lift_map.copy()

        return type(self)(ground_obj, lift_map)

    def __post_init__(self):
        def _no_user(id: isl.Id):
            try:
                id.user
            except TypeError:
                return True
            else:
                return False

        assert all(isinstance(k, str) and isinstance(v, str)
                   for k, v in self.lift_map.items())
        assert all((self.ground_obj.has_dim_id(dt, pos)
                    and _no_user(self.ground_obj.get_dim_id(dt, pos)))
                   for (dt, pos) in self.ground_obj.get_var_dict().values())
        assert isinstance(self.ground_obj, getattr(isl, self.__class__.__name__))
        assert isinstance(self.lift_map, dict)

    def get_dim_name(self, op_pool: ISLOpMemoizer,
                     type: isl.dim_type, pos: int) -> str:
        base_name = op_pool(self.ground_obj.__class__.get_dim_name,
                           (self.ground_obj, type, pos))
        return self.lift_map[base_name]

    def set_dim_name(self, op_pool: ISLOpMemoizer,
                     type: isl.dim_type, pos: int,
                     s: str) -> "NormalizedISLObj":
        base_name = op_pool(self.ground_obj.__class__.get_dim_name,
                            (self.ground_obj, type, pos))
        lift_map = self.lift_map.copy()
        lift_map[base_name] = s
        return self.copy(lift_map=lift_map)

    def get_dim_id(self, op_pool: ISLOpMemoizer,
                   type: isl.dim_type, pos: int) -> isl.Id:
        base_name = op_pool(type(self.ground_obj).get_dim_name,
                            (self.ground_obj, type, pos))
        return isl.Id(self.lift_map[base_name])

    def set_dim_id(self, op_pool: ISLOpMemoizer,
                   type: isl.dim_type, pos: int,
                   id: isl.Id) -> "NormalizedISLObj":
        try:
            id.user
        except TypeError:
            pass
        else:
            raise ValueError("Normalized ISL object cannot have user object in"
                             "ids.")
        return self.set_dim_name(op_pool, type, pos, id.get_name())

    def get_id_dict(self, op_pool: ISLOpMemoizer):
        ground_dict = op_pool(type(self.ground_obj).get_id_dict, (self.ground_obj,))
        return {isl.Id(self.lift_map[k.name]): v for k, v in ground_dict.items()}

    def get_var_dict(self, op_pool: ISLOpMemoizer,
                     dimtype: Optional[isl.dim_type] = None):
        ground_dict = op_pool(type(self.ground_obj).get_var_dict,
                              (self.ground_obj, dimtype))
        return {self.lift_map[k]: v for k, v in ground_dict.items()}

    def get_var_names(self, op_pool: ISLOpMemoizer,
                      dimtype: Optional[isl.dim_type] = None):
        ground_var_names = op_pool(self.ground_obj.__class__.get_var_names,
                                   (self.ground_obj, dimtype))
        return [self.lift_map[k] for k in ground_var_names]

    def get_ctx(self, op_pool: Optional[ISLOpMemoizer] = None):
        # FIXME: Is op_pool of any use to us here?
        if op_pool is None:
            return self.ground_obj.get_ctx()
        return op_pool(self.ground_obj.__class__.get_ctx, (self.ground_obj,))

    def insert_dims(self, op_pool: ISLOpMemoizer, type: isl.dim_type,
                    pos: int, n: int) -> "NormalizedISLObj":
        updated_grnd_obj = op_pool(self.ground_obj.__class__.insert_dims,
                                   (self.ground_obj, type, pos, n))
        vng = UniqueNameGenerator(set(self.lift_map), forced_prefix="_islpy")

        # {{{ normalize the newly inserted dims

        lift_map = self.lift_map.copy()

        for i in range(pos, pos+n):
            new_name = _gen_name(vng, type)
            old_name = updated_grnd_obj.get_dim_name(type, i) or new_name
            updated_grnd_obj = updated_grnd_obj.set_dim_name(type, i, new_name)
            lift_map[new_name] = old_name

        # }}}

        return self.copy(updated_grnd_obj, lift_map)

    def move_dims(self, *args, **kwargs):
        raise NotImplementedError

    def __str__(self):
        return str(self.lift())

    def __repr__(self):
        return repr(self.lift())


class Space(NormalizedISLObj):
    @staticmethod
    def params_alloc(ctx: isl.Context, nparam: int) -> "Space":
        grnd_obj, lift_map = normalize(isl.Space.params_alloc(ctx, nparam))
        return Space(grnd_obj, lift_map)

    @staticmethod
    def set_alloc(ctx: isl.Context, nparam: int, dim: int) -> "Space":
        grnd_obj, lift_map = normalize(isl.Space.set_alloc(ctx, nparam, dim))
        return Space(grnd_obj, lift_map)

    def dim(self, op_pool, type: isl.dim_type) -> int:
        return op_pool(isl.Space.dim, (self.ground_obj, type))

    def params(self, op_pool: ISLOpMemoizer) -> "Space":
        new_grnd = op_pool(isl.Space.params, (self.ground_obj,))
        new_lift_map = {k: self.lift_map[k]
                        for k in new_grnd.get_var_dict()}
        return Space(new_grnd, new_lift_map)


class LocalSpace(NormalizedISLObj):
    @staticmethod
    def from_space(space: Space):
        return LocalSpace(isl.LocalSpace.from_space(space.ground_obj),
                          space.lift_map)


class Constraint(NormalizedISLObj):
    def __post_init__(self):
        def _no_user(id: isl.Id):
            try:
                id.user
            except TypeError:
                return True
            else:
                return False

        assert all(isinstance(k, str) and isinstance(v, str)
                   for k, v in self.lift_map.items())
        assert isinstance(self.ground_obj, getattr(isl, self.__class__.__name__))
        assert isinstance(self.lift_map, dict)

    @staticmethod
    def equality_from_aff(aff: "Aff") -> "Constraint":
        return Constraint(isl.Constraint.equality_from_aff(aff.ground_obj),
                          aff.lift_map)


class BasicSet(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "BasicSet":
        ground_obj, lift_map = normalize(isl.BasicSet.read_from_str(ctx, s))
        return BasicSet(ground_obj, lift_map)

    @staticmethod
    def from_params(bset: "BasicSet"):
        return BasicSet(isl.BasicSet.from_params(bset.ground_obj), bset.lift_map)

    @staticmethod
    def universe(space: Space):
        ground_obj = isl.BasicSet.universe(space.ground_obj)
        return BasicSet(ground_obj, space.lift_map)

    def intersect(self, op_pool: ISLOpMemoizer,
                  other: Union["BasicSet", "Set"]) -> Union["BasicSet", "Set"]:
        if self.lift_map != other.lift_map:
            raise ValueError("spaces don't match")
        res_ground = op_pool(isl.BasicSet.intersect,
                             (self.ground_obj, other.ground_obj))
        if isinstance(res_ground, isl.Set):
            return Set(res_ground, self.lift_map)
        else:
            assert isinstance(res_ground, isl.BasicSet)
            return BasicSet(res_ground, self.lift_map)

    gist = intersect

    def is_equal(self, op_pool: ISLOpMemoizer, bset2: "BasicSet") -> bool:
        bset1, bset2 = normalize_binary_isl_obj(self, bset2)
        return bset1.ground_obj.is_equal(bset2.ground_obj)

    def is_params(self, op_pool: ISLOpMemoizer) -> bool:
        return op_pool(isl.BasicSet.is_params, (self.ground_obj,))

    def is_empty(self, op_pool: ISLOpMemoizer) -> bool:
        return op_pool(isl.BasicSet.is_empty, (self.ground_obj,))

    def project_out(self, op_pool: ISLOpMemoizer, type: isl.dim_type, first:
                    int, n: int) -> "BasicSet":
        projected_out_grnd = op_pool(isl.BasicSet.project_out, (self.ground_obj,
                                                                type, first, n))
        lift_map = {k: self.lift_map[k]
                    for k in op_pool(isl.BasicSet.get_var_dict,
                                     (projected_out_grnd,))}
        return self.copy(projected_out_grnd, lift_map)

    def project_out_except(self, op_pool: ISLOpMemoizer,
                           names: FrozenSet[str],
                           types: FrozenSet[isl.dim_type]) -> "BasicSet":
        return project_out_except(op_pool, self, names, types)

    def get_space(self, op_pool: ISLOpMemoizer) -> Space:
        return Space(op_pool(isl.BasicSet.get_space, (self.ground_obj,)),
                     self.lift_map)

    def dim(self, op_pool: ISLOpMemoizer, type: isl.dim_type) -> int:
        return op_pool(isl.BasicSet.dim, (self.ground_obj, type))

    def params(self, op_pool: ISLOpMemoizer) -> "BasicSet":
        new_grnd = op_pool(isl.BasicSet.params, (self.ground_obj,))
        new_lift_map = {k: self.lift_map[k]
                        for k in new_grnd.get_var_dict()}
        return BasicSet(new_grnd, new_lift_map)

    def dim_min(self, op_pool: ISLOpMemoizer, pos: int) -> "PwAff":
        grnd_pwaff = op_pool(isl.BasicSet.dim_min, (self.ground_obj, pos))
        new_lift_map = {k: self.lift_map[k]
                        for k in grnd_pwaff.get_var_dict()}
        return PwAff(grnd_pwaff, new_lift_map)

    def dim_max(self, op_pool: ISLOpMemoizer, pos: int) -> "PwAff":
        grnd_pwaff = op_pool(isl.BasicSet.dim_max, (self.ground_obj, pos))
        new_lift_map = {k: self.lift_map[k]
                        for k in grnd_pwaff.get_var_dict()}
        return PwAff(grnd_pwaff, new_lift_map)

    def complement(self, op_pool: ISLOpMemoizer) -> "Set":
        return Set(op_pool(isl.BasicSet.complement, (self.ground_obj,)),
                   self.lift_map)

    def remove_redundancies(self, op_pool: ISLOpMemoizer) -> "BasicSet":
        return BasicSet(op_pool(isl.BasicSet.remove_redundancies,
                                (self.ground_obj,)),
                        self.lift_map)

    def remove_divs(self, op_pool: ISLOpMemoizer) -> "BasicSet":
        return BasicSet(op_pool(isl.BasicSet.remove_divs,
                                (self.ground_obj,)),
                        self.lift_map)

    def get_constraints(self, op_pool: ISLOpMemoizer) -> List[Constraint]:
        return [Constraint(cnst, self.lift_map)
                for cnst in op_pool(isl.BasicSet.get_constraints,
                                    (self.ground_obj,))]

    def plain_is_universe(self, op_pool: ISLOpMemoizer) -> bool:
        return op_pool(isl.BasicSet.plain_is_universe, (self.ground_obj,))

    def add_constraint(self, op_pool: ISLOpMemoizer,
                       constraint: Constraint) -> "BasicSet":
        self = normalize_based_on_template(self, constraint)
        return self.copy(op_pool(isl.BasicSet.add_constraint,
                                 (self.ground_obj, constraint.ground_obj)))


class Set(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "Set":
        ground_obj, lift_map = normalize(isl.Set(s))
        return Set(ground_obj, lift_map)

    @staticmethod
    def universe(space: Space) -> "Set":
        ground_obj = isl.Set.universe(space.ground_obj)
        return Set(ground_obj, space.lift_map)

    @staticmethod
    def from_basic_set(bset: BasicSet):
        ground_obj = isl.Set.from_basic_set(bset.ground_obj)
        return Set(ground_obj, bset.lift_map)

    def intersect(self, op_pool: ISLOpMemoizer,
                  other: "Set") -> "Set":
        if self.lift_map != other.lift_map:
            raise ValueError("spaces don't match")
        res_ground = op_pool(isl.Set.intersect,
                             (self.ground_obj, other.ground_obj))
        if isinstance(res_ground, isl.Set):
            return Set(res_ground, self.lift_map)
        else:
            assert isinstance(res_ground, isl.BasicSet)
            return BasicSet(res_ground, self.lift_map)

    def intersect_params(self, op_pool: ISLOpMemoizer, params: "Set") -> "Set":
        self, params = normalize_binary_isl_obj(self, params)
        grnd_result = op_pool(isl.Set.intersect_params, (self.ground_obj,
                                                         params.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or params.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}

        return Set(grnd_result, lift_map)

    def is_params(self, op_pool: ISLOpMemoizer) -> bool:
        return op_pool(isl.Set.is_params, (self,))

    def is_equal(self, op_pool: ISLOpMemoizer, set2: "Set") -> bool:
        set1, set2 = normalize_binary_isl_obj(self, set2)
        return set1.ground_obj.is_equal(set2.ground_obj)

    def is_empty(self, op_pool: ISLOpMemoizer) -> bool:
        return op_pool(isl.Set.is_empty, (self.ground_obj,))

    def is_subset(self, op_pool: ISLOpMemoizer, set2: "Set") -> bool:
        assert self.lift_map == set2.lift_map
        return op_pool(isl.Set.is_subset, (self.ground_obj, set2.ground_obj))

    def project_out(self, op_pool: ISLOpMemoizer, type: isl.dim_type,
                    first: int, n: int) -> "Set":
        projected_out_grnd = op_pool(isl.Set.project_out, (self.ground_obj,
                                                           type, first, n))
        lift_map = {k: self.lift_map[k]
                    for k in op_pool(isl.Set.get_var_dict,
                                     (projected_out_grnd,))}
        return self.copy(projected_out_grnd, lift_map)

    def eliminate(self, op_pool: ISLOpMemoizer, type: isl.dim_type,
                  first: int, n: int) -> "Set":
        eliminated_grnd = op_pool(isl.Set.eliminate, (type, first, n))
        lift_map = {self.lift_map[k]
                    for k in op_pool(isl.Set.get_var_dict, ())}
        return self.copy(eliminated_grnd, lift_map)

    def project_out_except(self, op_pool: ISLOpMemoizer,
                           names: FrozenSet[str],
                           types: FrozenSet[isl.dim_type]) -> "Set":
        return project_out_except(op_pool, self, names, types)

    def eliminate_except(self, op_pool: ISLOpMemoizer,
                         names: FrozenSet[str],
                         types: FrozenSet[isl.dim_type]) -> "Set":
        return eliminate_except(op_pool, self, names, types)

    def get_space(self, op_pool: ISLOpMemoizer) -> Space:
        return Space(op_pool(isl.Set.get_space, (self.ground_obj,)),
                     self.lift_map)

    def dim(self, op_pool, type: isl.dim_type) -> int:
        return op_pool(isl.Set.dim, (self.ground_obj, type))

    def complement(self, op_pool: ISLOpMemoizer) -> "Set":
        return Set(op_pool(isl.Set.complement, (self.ground_obj,)), self.lift_map)

    def remove_redundancies(self, op_pool: ISLOpMemoizer) -> "Set":
        return Set(op_pool(isl.Set.remove_redundancies,
                           (self.ground_obj,)),
                   self.lift_map)

    def remove_divs(self, op_pool: ISLOpMemoizer) -> "Set":
        return Set(op_pool(isl.Set.remove_divs,
                           (self.ground_obj,)),
                   self.lift_map)

    def gist(self, op_pool: ISLOpMemoizer, context: Union[isl.Set,
                                                          isl.BasicSet]):
        return self.copy(op_pool(isl.Set.gist, (self.ground_obj,
                                                context.ground_obj)))

    def get_basic_sets(self, op_pool: ISLOpMemoizer) -> List[BasicSet]:
        return [BasicSet(bset, self.lift_map)
                for bset in op_pool(isl.Set.get_basic_sets, (self.ground_obj,))]

    def plain_is_universe(self, op_pool: ISLOpMemoizer) -> bool:
        return op_pool(isl.Set.plain_is_universe, (self.ground_obj,))


class NormalizedISLBasicMap(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "NormalizedISLBasicMap":
        ground_obj, lift_map = normalize(isl.BasicMap(s))
        return NormalizedISLBasicMap(ground_obj, lift_map)


class NormalizedISLMap(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "NormalizedISLMap":
        ground_obj, lift_map = normalize(isl.Map(s))
        return NormalizedISLMap(ground_obj, lift_map)


class Aff(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "Aff":
        ground_obj, lift_map = normalize(isl.Aff(s))
        return Aff(ground_obj, lift_map)

    @staticmethod
    def zero_on_domain(space: Space) -> "Aff":
        return Aff(isl.Aff.zero_on_domain(space.ground_obj), space.lift_map)

    def __add__(self, other):
        from warnings import warn
        warn("__add__ does not go through op_pool. Use Aff.add.",
             stacklevel=2)
        assert isinstance(other, int)
        return self.copy(self.ground_obj+other)

    def __sub__(self, other):
        from warnings import warn
        warn("__sub__ does not go through op_pool. Use Aff.sub.",
             stacklevel=2)
        return self-other

    def add(self, op_pool: ISLOpMemoizer, other):
        return self.copy(op_pool(isl.Aff.__add__, (self.ground_obj, )))

    def sub(self, op_pool: ISLOpMemoizer, other):
        return self.copy(op_pool(isl.Aff.__sub__, (self.ground_obj, )))

    def gist(self, op_pool: ISLOpMemoizer, context: Union[isl.Set,
                                                          isl.BasicSet]):
        return self.copy(op_pool(isl.Aff.gist, (self.ground_obj,
                                                 context.ground_obj)))

    def get_denominator_val(self, op_pool: ISLOpMemoizer) -> isl.Val:
        return op_pool(isl.Aff.get_denominator_val, (self.ground_obj,))

    def get_constant_val(self, op_pool: ISLOpMemoizer) -> isl.Val:
        return op_pool(isl.Aff.get_constant_val, (self.ground_obj,))

    def get_coefficient_val(self, op_pool: ISLOpMemoizer, type: isl.dim_type,
                            pos: int) -> isl.Val:
        return op_pool(isl.Aff.get_coefficient_val, (self.ground_obj, type,
                                                     pos))

    def get_div(self, op_pool: ISLOpMemoizer, pos: int) -> isl.Val:
        return op_pool(isl.Aff.get_div, (self.ground_obj, pos))

    def dim(self, op_pool: ISLOpMemoizer, type: isl.dim_type) -> int:
        return op_pool(isl.Aff.dim, (self.ground_obj, type))

    def add_coefficient_val(self, op_pool: ISLOpMemoizer, type: isl.dim_type,
                            pos: int, v: Union[isl.Val, int]):
        return self.copy(op_pool(isl.Aff.add_coefficient_val, (self.ground_obj, type,
                                                               pos, v)))


class PwAff(NormalizedISLObj):
    def lift(self) -> isl.PwAff:
        new_obj = self.ground_obj

        for old_name, (dt, pos) in new_obj.get_var_dict().items():
            new_obj = new_obj.set_dim_id(dt, pos, isl.Id(self.lift_map[old_name]))

        return new_obj

    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "PwAff":
        ground_obj, lift_map = normalize(isl.PwAff(s))
        return PwAff(ground_obj, lift_map)

    @staticmethod
    def alloc(set: Set, aff: Aff):
        assert set.lift_map == aff.lift_map
        return PwAff(isl.PwAff.alloc(set.ground_obj,
                                     aff.ground_obj), aff.lift_map)

    @staticmethod
    def var_on_domain(ls: LocalSpace, type: isl.dim_type, pos: int) -> "PwAff":
        return PwAff(isl.PwAff.var_on_domain(ls.ground_obj, type, pos),
                     ls.lift_map)

    def get_space(self, op_pool: ISLOpMemoizer) -> Space:
        return Space(op_pool(isl.PwAff.get_space, (self.ground_obj,)),
                     self.lift_map)

    def coalesce(self, op_pool: ISLOpMemoizer):
        return self.copy(op_pool(isl.PwAff.coalesce, (self.ground_obj,)))

    def __add__(self, other):
        from warnings import warn
        warn("__add__ does not go through op_pool. Use PwAff.add.",
             stacklevel=2)
        return self+other

    def __sub__(self, other):
        from warnings import warn
        warn("__sub__ does not go through op_pool. Use PwAff.sub.",
             stacklevel=2)
        return self-other

    def add(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff"):
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        grnd_result = op_pool(isl.PwAff.__add__, (self.ground_obj,
                                                  pwaff2.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or pwaff2.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}

        return PwAff(grnd_result, lift_map)

    def sub(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff"):
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        grnd_result = op_pool(isl.PwAff.__sub__, (self.ground_obj,
                                                  pwaff2.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or pwaff2.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}

        return PwAff(grnd_result, lift_map)

    def gist(self, op_pool: ISLOpMemoizer, context: Union[isl.Set,
                                                          isl.BasicSet]):
        return self.copy(op_pool(isl.PwAff.gist, (self.ground_obj,
                                                  context.ground_obj)))

    def gist_params(self, op_pool: ISLOpMemoizer, context: Union[isl.Set,
                                                          isl.BasicSet]):
        return self.copy(op_pool(isl.PwAff.gist_params, (self.ground_obj,
                                                         context.ground_obj)))

    def get_aggregate_domain(self, op_pool: ISLOpMemoizer) -> Set:
        grnd_domain = op_pool(isl.PwAff.get_aggregate_domain,
                              (self.ground_obj,))
        return Set(grnd_domain, self.lift_map)

    def get_pieces(self, op_pool: ISLOpMemoizer) -> List[Tuple[Set, Aff]]:
        grnd_pieces = op_pool(isl.PwAff.get_pieces, (self.ground_obj,))
        return [(Set(s, self.lift_map), Aff(aff, self.lift_map))
                for s, aff in grnd_pieces]

    def union_max(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff"):
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        grnd_result = op_pool(isl.PwAff.union_max, (self.ground_obj,
                                                    pwaff2.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or pwaff2.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}

        return PwAff(grnd_result, lift_map)

    def eq_set(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff") -> Set:
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        grnd_result = op_pool(isl.PwAff.eq_set, (self.ground_obj,
                                                 pwaff2.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or pwaff2.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}
        return Set(grnd_result, lift_map)

    def ge_set(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff") -> Set:
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        grnd_result = op_pool(isl.PwAff.ge_set, (self.ground_obj,
                                                 pwaff2.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or pwaff2.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}
        return Set(grnd_result, lift_map)

    def le_set(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff") -> Set:
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        grnd_result = op_pool(isl.PwAff.le_set, (self.ground_obj,
                                                 pwaff2.ground_obj))

        lift_map = {name: (self.lift_map.get(name) or pwaff2.lift_map.get(name))
                    for name in op_pool(grnd_result.__class__.get_var_dict,
                                        (grnd_result,))}
        return Set(grnd_result, lift_map)

    def is_equal(self, op_pool: ISLOpMemoizer, pwaff2: "PwAff") -> bool:
        self, pwaff2 = normalize_binary_isl_obj(self, pwaff2)
        return op_pool(isl.PwAff.is_equal, (self.ground_obj,
                                            pwaff2.ground_obj))


class QPolynomial(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "QPolynomial":
        ground_obj, lift_map = normalize(isl.QPolynomial(s))
        return QPolynomial(ground_obj, lift_map)


class PwQPolynomial(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> "PwQPolynomial":
        ground_obj, lift_map = normalize(isl.PwQPolynomial(s))
        return PwQPolynomial(ground_obj, lift_map)


def align_two(op_pool: ISLOpMemoizer,
              obj1: NormalizedISLObj,
              obj2: NormalizedISLObj) -> Tuple[NormalizedISLObj,
                                               NormalizedISLObj]:
    obj1, obj2 = normalize_binary_isl_obj(obj1, obj2)
    grnd_obj1, grnd_obj2 = op_pool(isl.align_two, (obj1.ground_obj,
                                                   obj2.ground_obj))

    lift_map1 = {name: (obj1.lift_map.get(name) or obj2.lift_map.get(name))
                 for name in op_pool(grnd_obj1.__class__.get_var_dict, (grnd_obj1,))}
    lift_map2 = {name: (obj1.lift_map.get(name) or obj2.lift_map.get(name))
                 for name in op_pool(grnd_obj2.__class__.get_var_dict, (grnd_obj2,))}

    return obj1.copy(grnd_obj1, lift_map1), obj2.copy(grnd_obj2, lift_map2)


def align_spaces(op_pool: ISLOpMemoizer,
                 obj: NormalizedISLObj,
                 template: NormalizedISLObj,
                 obj_bigger_ok=False) -> NormalizedISLObj:
    obj, template = normalize_binary_isl_obj(obj, template)
    grnd_obj = op_pool(isl.align_spaces, (obj.ground_obj,
                                          template.ground_obj,
                                          obj_bigger_ok))

    lift_map = {name: (obj.lift_map.get(name) or template.lift_map.get(name))
                for name in op_pool(grnd_obj.__class__.get_var_dict, (grnd_obj,))}

    return obj.copy(grnd_obj, lift_map)


def project_out_except(op_pool: ISLOpMemoizer, obj: NormalizedISLObj,
                       names: FrozenSet[str], types: FrozenSet[isl.dim_type]
                       ) -> NormalizedISLObj:
    for tp in types:
        while True:
            space = obj.get_space(op_pool)
            var_dict = space.get_var_dict(op_pool, tp)

            all_indices = set(range(space.dim(op_pool, tp)))
            leftover_indices = set(var_dict[name][1]
                                   for name in names
                                   if name in var_dict)
            project_indices = all_indices-leftover_indices
            if not project_indices:
                break

            min_index = min(project_indices)
            count = 1
            while min_index+count in project_indices:
                count += 1

            obj = obj.project_out(op_pool, tp, min_index, count)

    return obj


def eliminate_except(op_pool: ISLOpMemoizer, obj: NormalizedISLObj,
                     names: FrozenSet[str], types: FrozenSet[isl.dim_type]
                     ) -> NormalizedISLObj:
    for tp in types:
        space = obj.get_space(op_pool)
        var_dict = space.get_var_dict(op_pool, tp)
        to_eliminate = (
                set(range(space.dim(op_pool, tp)))
                - set(var_dict[name][1]
                      for name in names
                      if name in var_dict))

        while to_eliminate:
            min_index = min(to_eliminate)
            count = 1
            while min_index+count in to_eliminate:
                count += 1

            obj = obj.eliminate(op_pool, tp, min_index, count)

            to_eliminate -= set(range(min_index, min_index+count))

    return obj
