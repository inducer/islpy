#include "wrap_isl.hpp"

void islpy_expose_part1(py::module &m);
void islpy_expose_part2(py::module &m);
void islpy_expose_part3(py::module &m);

namespace isl
{
  ctx_use_map_t ctx_use_map;
}


PYBIND11_MODULE(_isl, m)
{
  static py::exception<isl::error> ISLError(m, "Error", NULL);
  py::register_exception_translator(
        [](std::exception_ptr p)
        {
          try
          {
            if (p) std::rethrow_exception(p);
          }
          catch (isl::error &err)
          {
            py::object err_obj = py::cast(err);
            PyErr_SetObject(ISLError.ptr(), err_obj.ptr());
          }
        });

  // py::docstring_options doc_opt(true, false, false);

  /*
  {
    typedef isl_options cls;
    py::class_<cls>(m, "Options")
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

#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  py::enum_<isl_error>(m, "error")
    .ENUM_VALUE(isl_error_, none)
    .ENUM_VALUE(isl_error_, abort)
    .ENUM_VALUE(isl_error_, unknown)
    .ENUM_VALUE(isl_error_, internal)
    .ENUM_VALUE(isl_error_, invalid)
    .ENUM_VALUE(isl_error_, unsupported)
    ;

  py::enum_<isl_stat>(m, "stat")
    .ENUM_VALUE(isl_stat_, error)
    .ENUM_VALUE(isl_stat_, ok)
    ;
#endif

  py::enum_<isl_dim_type>(m, "dim_type")
    .ENUM_VALUE(isl_dim_, cst)
    .ENUM_VALUE(isl_dim_, param)
    .value("in_", isl_dim_in)
    .ENUM_VALUE(isl_dim_, out)
    .ENUM_VALUE(isl_dim_, set)
    .ENUM_VALUE(isl_dim_, div)
    .ENUM_VALUE(isl_dim_, all)
    ;

  py::enum_<isl_fold>(m, "fold")
    .ENUM_VALUE(isl_fold_, min)
    .ENUM_VALUE(isl_fold_, max)
    .ENUM_VALUE(isl_fold_, list)
    ;

  py::enum_<isl_ast_op_type>(m, "ast_op_type")
    .ENUM_VALUE(isl_ast_op_, error)
    .ENUM_VALUE(isl_ast_op_, and)
    .ENUM_VALUE(isl_ast_op_, and_then)
    .ENUM_VALUE(isl_ast_op_, or)
    .ENUM_VALUE(isl_ast_op_, or_else)
    .ENUM_VALUE(isl_ast_op_, max)
    .ENUM_VALUE(isl_ast_op_, min)
    .ENUM_VALUE(isl_ast_op_, minus)
    .ENUM_VALUE(isl_ast_op_, add)
    .ENUM_VALUE(isl_ast_op_, sub)
    .ENUM_VALUE(isl_ast_op_, mul)
    .ENUM_VALUE(isl_ast_op_, div)
    .ENUM_VALUE(isl_ast_op_, fdiv_q)
    .ENUM_VALUE(isl_ast_op_, pdiv_q)
    .ENUM_VALUE(isl_ast_op_, pdiv_r)
    .ENUM_VALUE(isl_ast_op_, cond)
    .ENUM_VALUE(isl_ast_op_, select)
    .ENUM_VALUE(isl_ast_op_, eq)
    .ENUM_VALUE(isl_ast_op_, le)
    .ENUM_VALUE(isl_ast_op_, lt)
    .ENUM_VALUE(isl_ast_op_, ge)
    .ENUM_VALUE(isl_ast_op_, gt)
    .ENUM_VALUE(isl_ast_op_, call)
    .ENUM_VALUE(isl_ast_op_, access)
    .ENUM_VALUE(isl_ast_op_, member)
    ;

  py::enum_<isl_ast_expr_type>(m, "ast_expr_type")
    .ENUM_VALUE(isl_ast_expr_, error)
    .ENUM_VALUE(isl_ast_expr_, op)
    .ENUM_VALUE(isl_ast_expr_, id)
    .ENUM_VALUE(isl_ast_expr_, int)
    ;

  py::enum_<isl_ast_node_type>(m, "ast_node_type")
    .ENUM_VALUE(isl_ast_node_, error)
    .ENUM_VALUE(isl_ast_node_, for)
    .ENUM_VALUE(isl_ast_node_, if)
    .ENUM_VALUE(isl_ast_node_, block)
    .ENUM_VALUE(isl_ast_node_, user)
    ;

#define FORMAT_ATTR(name) cls_format.attr(#name) = ISL_FORMAT_##name
  py::class_<isl::format> cls_format(m, "format");
  FORMAT_ATTR(ISL);
  FORMAT_ATTR(POLYLIB);
  FORMAT_ATTR(POLYLIB_CONSTRAINTS);
  FORMAT_ATTR(OMEGA);
  FORMAT_ATTR(C);
  FORMAT_ATTR(LATEX);
  FORMAT_ATTR(EXT_POLYLIB);

  islpy_expose_part1(m);
  islpy_expose_part2(m);
  islpy_expose_part3(m);

  py::implicitly_convertible<isl::basic_set, isl::set>();
  py::implicitly_convertible<isl::basic_map, isl::map>();
  py::implicitly_convertible<isl::set, isl::union_set>();
  py::implicitly_convertible<isl::map, isl::union_map>();
  py::implicitly_convertible<isl::space, isl::local_space>();
  py::implicitly_convertible<isl::aff, isl::pw_aff>();
}
