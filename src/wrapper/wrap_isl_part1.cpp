#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part1.inc"

  class constants { };
}

void islpy_expose_part1()
{
  import_gmpy();

  {
    typedef isl::ctx cls;
    py::class_<cls, boost::shared_ptr<cls>, boost::noncopyable>
      wrap_ctx("Context", py::no_init);
    wrap_ctx.def("__init__", py::make_constructor(isl::alloc_ctx));
    wrap_ctx.attr("_base_name") = "ctx";
    wrap_ctx.attr("_isl_name") = "isl_ctx";
  }

#define CONST(NAME) cls.attr(#NAME) = ISL_##NAME
  {
    py::class_<isl::constants> cls("constants", py::no_init);
    CONST(BOUND_BERNSTEIN);
    CONST(BOUND_RANGE);
    CONST(ON_ERROR_WARN);
    CONST(ON_ERROR_CONTINUE);
    CONST(ON_ERROR_ABORT);
    CONST(SCHEDULE_ALGORITHM_ISL);
    CONST(SCHEDULE_ALGORITHM_FEAUTRIER);
  }

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
  MAKE_WRAP(multi_pw_aff, MultiPwAff);
  MAKE_WRAP(pw_multi_aff, PwMultiAff);
  MAKE_WRAP(union_pw_multi_aff, UnionPwMultiAff);

  MAKE_WRAP(constraint, Constraint);
  MAKE_WRAP(space, Space);
  MAKE_WRAP(local_space, LocalSpace);

#include "gen-expose-part1.inc"
}
