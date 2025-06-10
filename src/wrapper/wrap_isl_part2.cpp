#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part2.inc"
}

void islpy_expose_part2(py::module_ &m)
{
  MAKE_WRAP(basic_set, BasicSet);
  wrap_basic_set.def("__hash__", [](isl::basic_set const &self) {
                       isl::set set_self(self);
                       return isl_set_get_hash(set_self.m_data);
                     });
  // used in align_dims
  wrap_basic_set.def("is_params", [](isl::basic_set const &self) {
                       isl::set set_self(self);
                       return bool(isl_set_is_params(set_self.m_data));
                     });

  MAKE_WRAP(basic_map, BasicMap);
  wrap_basic_map.def("__hash__", [](isl::basic_map const &self) {
                       isl::map map_self(self);
                       return isl_map_get_hash(map_self.m_data);
                     });

  MAKE_WRAP(set, Set);
  MAKE_INIT_CONVERTIBLE(basic_set, set);

  MAKE_WRAP(map, Map);
  MAKE_INIT_CONVERTIBLE(basic_map, map);
  MAKE_TO_METHOD(basic_map, map);

  MAKE_WRAP(union_set, UnionSet);
  MAKE_INIT_CONVERTIBLE(set, union_set);

  MAKE_WRAP(union_map, UnionMap);
  MAKE_INIT_CONVERTIBLE(map, union_map);

  MAKE_WRAP(point, Point);

  MAKE_WRAP(vertex, Vertex);

  MAKE_WRAP(cell, Cell);

  MAKE_WRAP(vertices, Vertices);
  MAKE_WRAP(stride_info, StrideInfo);

#include "gen-expose-part2.inc"
}
