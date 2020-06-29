#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part2.inc"
}

void islpy_expose_part2(py::module &m)
{
  MAKE_WRAP(basic_set, BasicSet);
  WRAP_ENABLE_PICKLING(basic_set);

  MAKE_WRAP(basic_map, BasicMap);
  WRAP_ENABLE_PICKLING(basic_map);

  MAKE_WRAP(set, Set);
  wrap_set.def(py::init<isl::basic_set &>());
  WRAP_ENABLE_PICKLING(set);

  MAKE_WRAP(map, Map);
  wrap_map.def(py::init<isl::basic_map &>());
  WRAP_ENABLE_PICKLING(map);

  MAKE_WRAP(union_set, UnionSet);
  wrap_union_set.def(py::init<isl::set &>());
  WRAP_ENABLE_PICKLING(union_set);

  MAKE_WRAP(union_map, UnionMap);
  wrap_union_map.def(py::init<isl::map &>());
  WRAP_ENABLE_PICKLING(union_map);

  MAKE_WRAP(point, Point);
  WRAP_ENABLE_PICKLING(point);

  MAKE_WRAP(vertex, Vertex);
  WRAP_ENABLE_PICKLING(vertex);

  MAKE_WRAP(cell, Cell);
  WRAP_ENABLE_PICKLING(cell);

  MAKE_WRAP(vertices, Vertices);
  MAKE_WRAP(stride_info, StrideInfo);

#include "gen-expose-part2.inc"
}
