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
#include <isl/aff.h>
#include <isl/vertices.h>
#include <isl/band.h>
#include <isl/schedule.h>
#include <isl/flow.h>
#include <isl/options.h>
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
  extern ctx_use_map_t ctx_use_map;

  inline void deref_ctx(isl_ctx *ctx)
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

  WRAP_CLASS(multi_aff);
  WRAP_CLASS(multi_pw_aff);
  WRAP_CLASS(pw_multi_aff);
  WRAP_CLASS(union_pw_multi_aff);

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
  WRAP_CLASS(restriction);

  inline ctx *alloc_ctx()
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
}





#define MAKE_WRAP(name, py_name) \
  py::class_<isl::name, boost::noncopyable> wrap_##name(#py_name, py::no_init); \
  wrap_##name.def("is_valid", &isl::name::is_valid, "Return whether current object is still valid."); \
  wrap_##name.attr("_base_name") = #name; \
  wrap_##name.attr("_isl_name") = "isl_"#name;

