#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part2.inc"
}

void islpy_expose_part2(py::module_ &m)
{
  MAKE_WRAP(basic_set, BasicSet);

  MAKE_WRAP(basic_map, BasicMap);

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
