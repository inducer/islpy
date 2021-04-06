from __future__ import annotations

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


from functools import cached_property
import islpy as isl
from dataclasses import dataclass, field
from typing import Union, Dict, Any, Optional, Tuple
from pytools import UniqueNameGenerator


BaseType = Union[isl.Aff, isl.BasicSet, isl.Set, isl.BasicMap, isl.Map]
BASE_CLASSES = (isl.Aff, isl.BasicSet, isl.Set, isl.BasicMap, isl.Map)


def normalize(obj: BaseType) -> BaseType:
    vng = UniqueNameGenerator(forced_prefix="_islpy")

    lift_map = {}
    new_obj = obj

    for old_name, (dt, pos) in obj.get_var_dict().items():
        if dt == isl.dim_type.param:
            new_name = vng("param")
        elif dt == isl.dim_type.set:
            new_name = vng("set")
        elif dt == isl.dim_type.in_:
            new_name = vng("in")
        elif dt == isl.dim_type.out:
            new_name = vng("out")
        else:
            raise NotImplementedError(dt)

        new_obj = new_obj.set_dim_name(dt, pos, new_name)
        lift_map[new_name] = old_name

    return new_obj, lift_map


@dataclass
class NormalizedISLObj:
    ground_obj: BaseType
    lift_map: Dict[str, str]

    def lift(self) -> BaseType:
        new_obj = self.ground_obj

        for old_name, (dt, pos) in new_obj.get_var_dict().items():
            new_obj = new_obj.set_dim_name(dt, pos, self.lift_map[old_name])

        return new_obj

    @cached_property
    def unlift_map(self) -> Dict[str, str]:
        return {v: k for k, v in self.lift_map.items()}

    def copy(self, ground_obj: Optional[BaseType] = None,
             lift_map: Optional[Dict[str, str]] = None) -> NormalizedISLObj:
        if ground_obj is None:
            ground_obj = self.ground_obj
        if lift_map is None:
            lift_map = self.lift_map.copy()

        return type(self)(ground_obj, lift_map)

    def post_init(self):
        def _no_user(id: isl.Id):
            try:
                isl.user
            except TypeError:
                return True
            else:
                return False

        assert all(_no_user(id_) for id_ in self.ground_obj.get_id_dict())

    def get_dim_name(self, op_pool: ISLOpMemoizer,
                     type: isl.dim_type, pos: int) -> str:
        base_name = op_pool(type(self.ground_obj).get_dim_name,
                           (self.ground_obj, pos))
        return self.lift_map[base_name]

    def set_dim_name(self, op_pool: ISLOpMemoizer,
                     type: isl.dim_type, pos: int,
                     s: str) -> NormalizedISLObj:
        base_name = op_pool(type(self.ground_obj).get_dim_name,
                            (self.ground_obj, pos))
        lift_map = self.lift_map.copy()
        lift_map[base_name] = s
        return self.copy(lift_map=lift_map)

    def get_dim_id(self, op_pool: ISLOpMemoizer,
                   type: isl.dim_type, pos: int) -> isl.Id:
        base_name = op_pool(type(self.ground_obj).get_dim_name,
                            (self.ground_obj, pos))
        return isl.Id(self.lift_map[base_name])

    def set_dim_id(self, op_pool: ISLOpMemoizer,
                   type: isl.dim_type, pos: int,
                   id: isl.Id) -> NormalizedISLObj:
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

    def get_var_dict(self, op_pool: ISLOpMemoizer):
        ground_dict = op_pool(type(self.ground_obj).get_var_dict, (self.ground_obj,))
        return {self.lift_map[k]: v for k, v in ground_dict.items()}


class NormalizedISLBasicSet(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLBasicSet:
        ground_obj, lift_map = normalize(isl.BasicSet(s))
        return NormalizedISLBasicSet(ground_obj, lift_map)

    def intersect(self, op_pool: ISLOpMemoizer,
                  other: NormalizedISLBasicSet) -> NormalizedISLBasicSet:
        if self.lift_map != other.lift_map:
            raise ValueError("spaces don't match")
        res_ground = op_pool(isl.BasicSet.intersect,
                             (self.ground_obj, other.ground_obj))
        return NormalizedISLBasicSet(res_ground, self.lift_map)


class NormalizedISLSet(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLSet:
        ground_obj, lift_map = normalize(isl.Set(s))
        return NormalizedISLSet(ground_obj, lift_map)

    def intersect(self, op_pool: ISLOpMemoizer,
                  other: NormalizedISLSet) -> NormalizedISLBasicSet:
        if self.lift_map != other.lift_map:
            raise ValueError("spaces don't match")
        res_ground = op_pool(isl.Set.intersect,
                             (self.ground_obj, other.ground_obj))
        return NormalizedISLBasicSet(res_ground, self.lift_map)


class NormalizedISLBasicMap(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLBasicMap:
        ground_obj, lift_map = normalize(isl.BasicMap(s))
        return NormalizedISLBasicMap(ground_obj, lift_map)


class NormalizedISLMap(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLMap:
        ground_obj, lift_map = normalize(isl.Map(s))
        return NormalizedISLMap(ground_obj, lift_map)


class NormalizedISLAff(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLAff:
        ground_obj, lift_map = normalize(isl.Aff(s))
        return NormalizedISLAff(ground_obj, lift_map)


class NormalizedISLPwAff(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLPwAff:
        ground_obj, lift_map = normalize(isl.PwAff(s))
        return NormalizedISLPwAff(ground_obj, lift_map)


class NormalizedISLQPolynomial(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLQPolynomial:
        ground_obj, lift_map = normalize(isl.QPolynomial(s))
        return NormalizedISLQPolynomial(ground_obj, lift_map)


class NormalizedISLPwQPolynomial(NormalizedISLObj):
    @staticmethod
    def read_from_str(ctx: isl.Context, s: str) -> NormalizedISLPwQPolynomial:
        ground_obj, lift_map = normalize(isl.PwQPolynomial(s))
        return NormalizedISLPwQPolynomial(ground_obj, lift_map)


@dataclass
class ISLOpMemoizer:
    cache: Dict[Any, Any] = field(default_factory=dict)

    def __call__(self, f, args: Tuple[Any, ...]):
        try:
            return self.cache[(f, args)]
        except KeyError:
            result = f(*args)
            self.cache[(f, args)] = result
            return result
