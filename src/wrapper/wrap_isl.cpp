#include <boost/python.hpp>
#include <isl/ctx.h>
#include <isl/dim.h>
#include <isl/set.h>
#include <isl/map.h>
#include <isl/union_set.h>
#include <isl/union_map.h>
#include <isl/point.h>
#include <isl/printer.h>
#include <isl/local_space.h>
#include <isl/vec.h>
#include <isl/mat.h>
#include <isl/polynomial.h>
#include <isl/aff.h>
#include <isl/vertices.h>
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
      boost::shared_ptr<ctx> m_ctx; \
      \
      name(isl_##name *data) \
      : m_data(data), m_valid(true) \
      { } \
      ~name() \
      { if (m_valid) isl_##name##_free(m_data); } \
  };

  struct ctx \
  {
    public:
      isl_ctx           *m_data;

      ctx(isl_ctx *data)
      : m_data(data)
      { }

      ~ctx()
      { isl_ctx_free(m_data); }
  };

  WRAP_CLASS(printer);
  WRAP_CLASS(mat);
  WRAP_CLASS(vec);

  WRAP_CLASS(aff);
  WRAP_CLASS(pw_aff);

  WRAP_CLASS(div);
  WRAP_CLASS(dim);
  WRAP_CLASS(local_space);

  WRAP_CLASS(basic_set);
  WRAP_CLASS(basic_map);
  WRAP_CLASS(set);
  WRAP_CLASS(map);
  WRAP_CLASS(union_set);
  WRAP_CLASS(union_map);

  WRAP_CLASS(point);
  WRAP_CLASS(vertex);
  WRAP_CLASS(cell);
  WRAP_CLASS(vertices);
  WRAP_CLASS(qpolynomial);

  WRAP_CLASS(basic_set_list);
  WRAP_CLASS(set_list);
  WRAP_CLASS(aff_list);
  WRAP_CLASS(band_list);

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

  py::enum_<isl_fold>("fold")
    .ENUM_VALUE(isl_fold_, min)
    .ENUM_VALUE(isl_fold_, max)
    .ENUM_VALUE(isl_fold_, list)
    ;

  {
    typedef isl::ctx cls;
    py::class_<cls, boost::shared_ptr<cls>, boost::noncopyable>("Context", py::no_init)
      .def("__init__", py::make_constructor(isl::alloc_ctx))
      ;
  }

#define MAKE_WRAP(name, py_name) \
  py::class_<isl::name, boost::noncopyable> wrap_##name(#py_name, py::no_init);

  MAKE_WRAP(printer, Printer);
  MAKE_WRAP(mat, Mat);
  MAKE_WRAP(vec, Vec);

  MAKE_WRAP(aff, Aff);
  MAKE_WRAP(pw_aff, PwAff);

  MAKE_WRAP(div, Div);
  MAKE_WRAP(dim, Dim);
  MAKE_WRAP(local_space, LocalSpace);

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
  MAKE_WRAP(qpolynomial, QPolynomial);

  MAKE_WRAP(basic_set_list, BasicSetList);
  MAKE_WRAP(set_list, SetList);
  MAKE_WRAP(aff_list, AffList);
  MAKE_WRAP(band_list, BandList);

  #include "gen-expose.inc"
}
