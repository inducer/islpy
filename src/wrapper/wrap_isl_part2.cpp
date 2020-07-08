#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part2.inc"
}

void islpy_expose_part2(py::module &m)
{
  MAKE_WRAP(basic_set, BasicSet);

  MAKE_WRAP(basic_map, BasicMap);

  MAKE_WRAP(set, Set);
  wrap_set.def(py::init<isl::basic_set &>());

  MAKE_WRAP(map, Map);
  wrap_map.def(py::init<isl::basic_map &>());

  MAKE_WRAP(union_set, UnionSet);
  wrap_union_set.def(py::init<isl::set &>());

  MAKE_WRAP(union_map, UnionMap);
  wrap_union_map.def(py::init<isl::map &>());

  MAKE_WRAP(point, Point);

  MAKE_WRAP(vertex, Vertex);

  MAKE_WRAP(cell, Cell);

  MAKE_WRAP(vertices, Vertices);
  MAKE_WRAP(stride_info, StrideInfo);

#include "gen-expose-part2.inc"
}
