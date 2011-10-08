#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part2.inc"
}

void islpy_expose_part2()
{
  import_gmpy();

  MAKE_WRAP(basic_set, BasicSet);
  MAKE_WRAP(basic_map, BasicMap);
  MAKE_WRAP(set, Set);
  MAKE_WRAP(map, Map);
  MAKE_WRAP(union_set, UnionSet);
  MAKE_WRAP(union_map, UnionMap);

  MAKE_WRAP(point, Point);
  MAKE_WRAP(vertex, Vertex);
  MAKE_WRAP(cell, Cell);
  MAKE_WRAP(vertices, Vertices);

#include "gen-expose-part2.inc"
}
