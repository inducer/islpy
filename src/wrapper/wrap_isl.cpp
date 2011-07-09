#include <boost/python.hpp>
#include <isl/ctx.h>
#include <isl/dim.h>
#include <isl/set.h>
#include <isl/map.h>
#include <isl/point.h>
#include <isl/printer.h>
#include <isl/local_space.h>
#include <isl/vec.h>
#include <isl/polynomial.h>
#include "gmpy.h"
#include "wrap_helpers.hpp"

namespace py = boost::python;

namespace isl
{
#define WRAP_CLASS(name) \
  struct name \
  { \
    public: \
      isl_##name        *m_data; \
      bool              m_valid; \
      \
      name(isl_##name *data) \
      : m_data(data), m_valid(true) \
      { } \
      ~name() \
      { if (m_valid) isl_##name##_free(m_data); } \
  };

  WRAP_CLASS(ctx);
  WRAP_CLASS(dim);
  WRAP_CLASS(basic_set);
  WRAP_CLASS(basic_map);
  WRAP_CLASS(set);
  WRAP_CLASS(map);
  WRAP_CLASS(printer);
  WRAP_CLASS(local_space);
  WRAP_CLASS(vec);
  WRAP_CLASS(point);
  WRAP_CLASS(qpolynomial);

  ctx *alloc_ctx()
  {
    isl_ctx *result = isl_ctx_alloc();
    if (result)
    {
      try
      { return new ctx(result); }
      catch (...)
      {
        isl_ctx_free(result);
        throw;
      }
    }
    else
      PYTHON_ERROR(RuntimeError, "failed to create context");
  }


  #include "gen-wrap.inc"

}




BOOST_PYTHON_MODULE(_isl)
{
  import_gmpy();

  /*
  {
    typedef isl_options cls;
    py::class_<cls>("Options")
      .DEF_SIMPLE_RW_MEMBER(lp_solver)
      .DEF_SIMPLE_RW_MEMBER(ilp_solver)
      .DEF_SIMPLE_RW_MEMBER(pip)
      .DEF_SIMPLE_RW_MEMBER(context)
      .DEF_SIMPLE_RW_MEMBER(gbr)
      .DEF_SIMPLE_RW_MEMBER(gbr_only_first)
      .DEF_SIMPLE_RW_MEMBER(closure)
      .DEF_SIMPLE_RW_MEMBER(bound)
      .DEF_SIMPLE_RW_MEMBER(bernstein_recurse)
      .DEF_SIMPLE_RW_MEMBER(bernstein_triangulate)
      .DEF_SIMPLE_RW_MEMBER(pip_symmetry)
      .DEF_SIMPLE_RW_MEMBER(convex)
      .DEF_SIMPLE_RW_MEMBER(schedule_parametric)
      .DEF_SIMPLE_RW_MEMBER(schedule_outer_zero_distance)
      .DEF_SIMPLE_RW_MEMBER(schedule_split_parallel)
      ;
  }
  */

  py::enum_<isl_error>("error")
    .ENUM_VALUE(isl_error_, none)
    .ENUM_VALUE(isl_error_, abort)
    .ENUM_VALUE(isl_error_, unknown)
    .ENUM_VALUE(isl_error_, internal)
    .ENUM_VALUE(isl_error_, invalid)
    .ENUM_VALUE(isl_error_, unsupported)
    ;

  py::enum_<isl_dim_type>("dim_type")
    .ENUM_VALUE(isl_dim_, cst)
    .ENUM_VALUE(isl_dim_, param)
    .ENUM_VALUE(isl_dim_, in)
    .ENUM_VALUE(isl_dim_, out)
    .ENUM_VALUE(isl_dim_, set)
    .ENUM_VALUE(isl_dim_, div)
    .ENUM_VALUE(isl_dim_, all)
    ;

  py::enum_<isl_dim_type>("fold")
    .ENUM_VALUE(isl_fold_, min)
    .ENUM_VALUE(isl_fold_, max)
    .ENUM_VALUE(isl_fold_, list)
    ;

  {
    typedef isl::ctx cls;
    py::class_<cls, boost::noncopyable>("Context", py::no_init)
      .def("__init__", py::make_constructor(isl::alloc_ctx))
      ;
  }

  py::class_<isl::dim, boost::noncopyable> wrap_dim("Dim", py::no_init);
  py::class_<isl::basic_set, boost::noncopyable> wrap_basic_set("BasicSet", py::no_init);
  py::class_<isl::basic_map, boost::noncopyable> wrap_basic_map("BasicMap", py::no_init);
  py::class_<isl::set, boost::noncopyable> wrap_set("Set", py::no_init);
  py::class_<isl::map, boost::noncopyable> wrap_map("Map", py::no_init);
  py::class_<isl::printer, boost::noncopyable> wrap_printer("Printer", py::no_init);
  py::class_<isl::local_space, boost::noncopyable> wrap_local_space("LocalSpace", py::no_init);
  py::class_<isl::vec, boost::noncopyable> wrap_vec("Vec", py::no_init);
  py::class_<isl::point, boost::noncopyable> wrap_point("Point", py::no_init);
  py::class_<isl::qpolynomial, boost::noncopyable> wrap_qpolynomial("QPolynomial", py::no_init);

  #include "gen-expose.inc"
}
