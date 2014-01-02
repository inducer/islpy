#include "wrap_isl.hpp"

void islpy_expose_part1();
void islpy_expose_part2();
void islpy_expose_part3();

namespace isl
{
  ctx_use_map_t ctx_use_map;
}



namespace
{
  py::handle<> ISLError;

  void translate_isl_error(const isl::error &err)
  {
    PyErr_SetObject(ISLError.get(), py::object(err.what()).ptr());
  }
}



BOOST_PYTHON_MODULE(_isl)
{
  ISLError = py::handle<>(PyErr_NewException("islpy.Error", PyExc_RuntimeError, NULL));
  py::scope().attr("Error") = ISLError;
  py::register_exception_translator<isl::error>(translate_isl_error);

  py::docstring_options doc_opt(true, false, false);

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

  py::enum_<isl_ast_op_type>("ast_op_type")
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

  py::enum_<isl_ast_expr_type>("ast_expr_type")
    .ENUM_VALUE(isl_ast_expr_, error)
    .ENUM_VALUE(isl_ast_expr_, op)
    .ENUM_VALUE(isl_ast_expr_, id)
    .ENUM_VALUE(isl_ast_expr_, int)
    ;

  py::enum_<isl_ast_node_type>("ast_node_type")
    .ENUM_VALUE(isl_ast_node_, error)
    .ENUM_VALUE(isl_ast_node_, for)
    .ENUM_VALUE(isl_ast_node_, if)
    .ENUM_VALUE(isl_ast_node_, block)
    .ENUM_VALUE(isl_ast_node_, user)
    ;

#define FORMAT_ATTR(name) cls_format.attr(#name) = ISL_FORMAT_##name
  py::class_<isl::format> cls_format("format", py::no_init);
  FORMAT_ATTR(ISL);
  FORMAT_ATTR(POLYLIB);
  FORMAT_ATTR(POLYLIB_CONSTRAINTS);
  FORMAT_ATTR(OMEGA);
  FORMAT_ATTR(C);
  FORMAT_ATTR(LATEX);
  FORMAT_ATTR(EXT_POLYLIB);

  islpy_expose_part1();
  islpy_expose_part2();
  islpy_expose_part3();

  py::implicitly_convertible<isl::basic_set, isl::set>();
  py::implicitly_convertible<isl::basic_map, isl::map>();
  py::implicitly_convertible<isl::set, isl::union_set>();
  py::implicitly_convertible<isl::map, isl::union_map>();
  py::implicitly_convertible<isl::space, isl::local_space>();
  py::implicitly_convertible<isl::aff, isl::pw_aff>();
}
