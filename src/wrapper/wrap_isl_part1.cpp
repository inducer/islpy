#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part1.inc"
}

void islpy_expose_part1()
{
  import_gmpy();

  MAKE_WRAP(basic_set_list, BasicSetList);
  MAKE_WRAP(set_list, SetList);
  MAKE_WRAP(aff_list, AffList);
  MAKE_WRAP(pw_aff_list, PwAffList);
  MAKE_WRAP(band_list, BandList);

  MAKE_WRAP(printer, Printer);
  MAKE_WRAP(mat, Mat);
  MAKE_WRAP(vec, Vec);
  MAKE_WRAP(id, Id);

  MAKE_WRAP(aff, Aff);
  MAKE_WRAP(pw_aff, PwAff);
  MAKE_WRAP(multi_aff, MultiAff);
  MAKE_WRAP(pw_multi_aff, PwMultiAff);

  MAKE_WRAP(constraint, Constraint);
  MAKE_WRAP(space, Space);
  MAKE_WRAP(local_space, LocalSpace);

#include "gen-expose-part1.inc"
}
