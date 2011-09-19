#include <boost/python.hpp>
#include <isl/ctx.h>
#include <isl/space.h>
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
#include <isl/band.h>
#include <isl/schedule.h>
#include <isl/flow.h>
#include <boost/unordered_map.hpp>
#include "gmpy.h"
#include "wrap_helpers.hpp"

// TODO: flow.h
// TODO: better error reporting

namespace py = boost::python;

namespace isl
{
  struct managed_int
  {
    isl_int m_data;

    managed_int()
    {
      isl_int_init(m_data);
    }
    ~managed_int()
    {
      isl_int_clear(m_data);
    }
  };

  struct ctx;

  typedef boost::unordered_map<isl_ctx *, unsigned> ctx_use_map_t;
  ctx_use_map_t ctx_use_map;

  void deref_ctx(isl_ctx *ctx)
  {
    ctx_use_map[ctx] -= 1;
    if (ctx_use_map[ctx] == 0)
      isl_ctx_free(ctx);
  }

#define WRAP_CLASS(name) \
  struct name { WRAP_CLASS_CONTENT(name) }

#define MAKE_CAST_CTOR(name, from_type, cast_func) \
      name(from_type &data) \
      : m_valid(false) \
      { \
        m_ctx = isl_##from_type##_get_ctx(data.m_data); \
        \
        isl_##from_type *copy = isl_##from_type##_copy(data.m_data); \
        if (!copy) \
          throw std::runtime_error("isl_" #from_type "_copy failed"); \
        m_data = cast_func(copy); \
        if (!m_data) \
          throw std::runtime_error(#cast_func " failed"); \
        \
        m_valid = true; \
        ctx_use_map[m_ctx] += 1; \
      }

#define WRAP_CLASS_CONTENT(name) \
    private: \
      bool              m_valid; \
      isl_ctx           *m_ctx; \
    public: \
      isl_##name        *m_data; \
      \
      name(isl_##name *data) \
      : m_valid(true), m_data(data) \
      { \
        m_ctx = isl_##name##_get_ctx(data); \
        ctx_use_map[m_ctx] += 1; \
      } \
      \
      void invalidate() \
      { \
        deref_ctx(m_ctx); \
        m_valid = false; \
      } \
      \
      bool is_valid() const \
      { \
        return m_valid; \
      } \
      \
      ~name() \
      { \
        if (m_valid) \
        { \
          isl_##name##_free(m_data); \
          deref_ctx(m_ctx); \
        } \
      }

  struct ctx \
  {
    public:
      isl_ctx           *m_data;

      ctx(isl_ctx *data)
      : m_data(data)
      {
        ctx_use_map_t::iterator it(ctx_use_map.find(m_data));
        if (it == ctx_use_map.end())
          ctx_use_map[data] = 1;
        else
          ctx_use_map[m_data] += 1;
      }

      bool is_valid() const
      {
        return true;
      }
      ~ctx()
      {
        deref_ctx(m_data);
      }
  };

  WRAP_CLASS(printer);
  WRAP_CLASS(mat);
  WRAP_CLASS(vec);
  WRAP_CLASS(id);

  WRAP_CLASS(aff);

  struct pw_aff
  {
    WRAP_CLASS_CONTENT(pw_aff);
    MAKE_CAST_CTOR(pw_aff, aff, isl_pw_aff_from_aff);
  };

  WRAP_CLASS(constraint);
  WRAP_CLASS(space);

  struct local_space
  {
    WRAP_CLASS_CONTENT(local_space);
    MAKE_CAST_CTOR(local_space, space, isl_local_space_from_space);
  };

  WRAP_CLASS(basic_set);
  WRAP_CLASS(basic_map);

  struct set
  {
    WRAP_CLASS_CONTENT(set);
    MAKE_CAST_CTOR(set, basic_set, isl_set_from_basic_set);
  };

  struct map
  {
    WRAP_CLASS_CONTENT(map);
    MAKE_CAST_CTOR(map, basic_map, isl_map_from_basic_map);
  };

  struct union_set
  {
    WRAP_CLASS_CONTENT(union_set);
    MAKE_CAST_CTOR(union_set, set, isl_union_set_from_set);
  };
  struct union_map
  {
    WRAP_CLASS_CONTENT(union_map);
    MAKE_CAST_CTOR(union_map, map, isl_union_map_from_map);
  };

  WRAP_CLASS(point);
  WRAP_CLASS(vertex);
  WRAP_CLASS(cell);
  WRAP_CLASS(vertices);

  WRAP_CLASS(qpolynomial);
  WRAP_CLASS(pw_qpolynomial);
  WRAP_CLASS(qpolynomial_fold);
  WRAP_CLASS(pw_qpolynomial_fold);
  WRAP_CLASS(union_pw_qpolynomial);
  WRAP_CLASS(union_pw_qpolynomial_fold);
  WRAP_CLASS(term);

  WRAP_CLASS(basic_set_list);
  WRAP_CLASS(set_list);
  WRAP_CLASS(aff_list);
  WRAP_CLASS(pw_aff_list);
  WRAP_CLASS(band_list);

  WRAP_CLASS(band);
  WRAP_CLASS(schedule);

  WRAP_CLASS(access_info);
  WRAP_CLASS(flow);

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

  class format { };

  #include "gen-wrap.inc"
}




BOOST_PYTHON_MODULE(_isl)
{
  py::docstring_options doc_opt(true, false, false);

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
    .value("in_", isl_dim_in)
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
    py::class_<cls, boost::shared_ptr<cls>, boost::noncopyable> 
      wrap_ctx("Context", py::no_init);
    wrap_ctx.def("__init__", py::make_constructor(isl::alloc_ctx));
    wrap_ctx.attr("_base_name") = "ctx";
    wrap_ctx.attr("_isl_name") = "isl_ctx";
  }

#define MAKE_WRAP(name, py_name) \
  py::class_<isl::name, boost::noncopyable> wrap_##name(#py_name, py::no_init); \
  wrap_##name.def("is_valid", &isl::name::is_valid, "Return whether current object is still valid."); \
  wrap_##name.attr("_base_name") = #name; \
  wrap_##name.attr("_isl_name") = "isl_"#name;

  MAKE_WRAP(printer, Printer);
  MAKE_WRAP(mat, Mat);
  MAKE_WRAP(vec, Vec);
  MAKE_WRAP(id, Id);

  MAKE_WRAP(aff, Aff);
  MAKE_WRAP(pw_aff, PwAff);

  MAKE_WRAP(constraint, Constraint);
  MAKE_WRAP(space, Space);
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
  MAKE_WRAP(pw_qpolynomial, PwQPolynomial);
  MAKE_WRAP(qpolynomial_fold, QPolynomialFold);
  MAKE_WRAP(pw_qpolynomial_fold, PwQPolynomialFold);
  MAKE_WRAP(union_pw_qpolynomial, UnionPwQPolynomial);
  MAKE_WRAP(union_pw_qpolynomial_fold, UnionPwQPolynomialFold);
  MAKE_WRAP(term, Term);

  MAKE_WRAP(band, Band);
  MAKE_WRAP(schedule, Schedule);

  MAKE_WRAP(basic_set_list, BasicSetList);
  MAKE_WRAP(set_list, SetList);
  MAKE_WRAP(aff_list, AffList);
  MAKE_WRAP(pw_aff_list, PwAffList);
  MAKE_WRAP(band_list, BandList);

  MAKE_WRAP(access_info, AccessInfo);
  MAKE_WRAP(flow, Flow);

#define FORMAT_ATTR(name) cls_format.attr(#name) = ISL_FORMAT_##name
  py::class_<isl::format> cls_format("format", py::no_init);
  FORMAT_ATTR(ISL);
  FORMAT_ATTR(POLYLIB);
  FORMAT_ATTR(POLYLIB_CONSTRAINTS);
  FORMAT_ATTR(OMEGA);
  FORMAT_ATTR(C);
  FORMAT_ATTR(LATEX);
  FORMAT_ATTR(EXT_POLYLIB);

  py::implicitly_convertible<isl::basic_set, isl::set>();
  py::implicitly_convertible<isl::basic_map, isl::map>();
  py::implicitly_convertible<isl::set, isl::union_set>();
  py::implicitly_convertible<isl::map, isl::union_map>();
  py::implicitly_convertible<isl::space, isl::local_space>();
  py::implicitly_convertible<isl::aff, isl::pw_aff>();

  #include "gen-expose.inc"
}
