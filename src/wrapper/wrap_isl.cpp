#include "wrap_isl.hpp"

void islpy_expose_part1(py::module_ &m);
void islpy_expose_part2(py::module_ &m);
void islpy_expose_part3(py::module_ &m);

namespace isl
{
  ctx_use_map_t ctx_use_map;

  [[noreturn]] void handle_isl_error(isl_ctx *ctx, std::string const &func_name)
  {
    std::string errmsg = "call to " + func_name + " failed: ";
    if (ctx)
    {
      const char *isl_msg = isl_ctx_last_error_msg(ctx);
      if (isl_msg)
        errmsg += isl_msg;
      else
        errmsg += "<no message>";

      const char *err_file = isl_ctx_last_error_file(ctx);
      if (err_file)
      {
        errmsg += " in ";
        errmsg += err_file;
        errmsg += ":";
        errmsg += std::to_string(isl_ctx_last_error_line(ctx));
      }
    }
    throw isl::error(errmsg);
  }

  isl_ctx *get_default_context()
  {
    py::module_ mod = py::module_::import_("islpy");
    py::object ctx_py = mod.attr("DEFAULT_CONTEXT");
    if (!ctx_py.is_none())
    {
      isl::ctx *ctx_wrapper = py::cast<isl::ctx *>(ctx_py);
      if (ctx_wrapper->is_valid())
        return ctx_wrapper->m_data;
    }
    return nullptr;
  }
}


NB_MODULE(_isl, m)
{
  // py::options options;
  // options.disable_function_signatures();

  static py::exception<isl::error> ISLError(m, "Error");

  py::register_exception_translator(
      [](const std::exception_ptr &p, void * /* unused */)
      {
        try
        {
          std::rethrow_exception(p);
        }
        catch (const isl::error &e)
        {
          PyErr_SetString(ISLError.ptr(), e.what());
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

  py::enum_<isl_error>(m, "error")
    .ENUM_VALUE(isl_error_, none)
    .ENUM_VALUE(isl_error_, abort)
    .ENUM_VALUE(isl_error_, alloc)
    .ENUM_VALUE(isl_error_, unknown)
    .ENUM_VALUE(isl_error_, internal)
    .ENUM_VALUE(isl_error_, invalid)
    .ENUM_VALUE(isl_error_, quota)
    .ENUM_VALUE(isl_error_, unsupported)
    ;

  py::enum_<isl_stat>(m, "stat")
    .ENUM_VALUE(isl_stat_, error)
    .ENUM_VALUE(isl_stat_, ok)
    ;

  py::enum_<isl_dim_type>(m, "dim_type")
    .ENUM_VALUE(isl_dim_, cst)
    .ENUM_VALUE(isl_dim_, param)
    .value("in_", isl_dim_in)
    .ENUM_VALUE(isl_dim_, out)
    .ENUM_VALUE(isl_dim_, set)
    .ENUM_VALUE(isl_dim_, div)
    .ENUM_VALUE(isl_dim_, all)
    ;

  py::enum_<isl_schedule_node_type>(m, "schedule_node_type")
    .ENUM_VALUE(isl_schedule_node_, error)
    .ENUM_VALUE(isl_schedule_node_, band)
    .ENUM_VALUE(isl_schedule_node_, context)
    .ENUM_VALUE(isl_schedule_node_, domain)
    .ENUM_VALUE(isl_schedule_node_, expansion)
    .ENUM_VALUE(isl_schedule_node_, extension)
    .ENUM_VALUE(isl_schedule_node_, filter)
    .ENUM_VALUE(isl_schedule_node_, leaf)
    .ENUM_VALUE(isl_schedule_node_, guard)
    .ENUM_VALUE(isl_schedule_node_, mark)
    .ENUM_VALUE(isl_schedule_node_, sequence)
    .ENUM_VALUE(isl_schedule_node_, set)
    ;

  py::enum_<isl_ast_expr_op_type>(m, "ast_expr_op_type")
    .ENUM_VALUE(isl_ast_expr_op_, error)
    .value("and_", isl_ast_expr_op_and)
    .ENUM_VALUE(isl_ast_expr_op_, and_then)
    .value("or_", isl_ast_expr_op_or)
    .ENUM_VALUE(isl_ast_expr_op_, or_else)
    .ENUM_VALUE(isl_ast_expr_op_, max)
    .ENUM_VALUE(isl_ast_expr_op_, min)
    .ENUM_VALUE(isl_ast_expr_op_, minus)
    .ENUM_VALUE(isl_ast_expr_op_, add)
    .ENUM_VALUE(isl_ast_expr_op_, sub)
    .ENUM_VALUE(isl_ast_expr_op_, mul)
    .ENUM_VALUE(isl_ast_expr_op_, div)
    .ENUM_VALUE(isl_ast_expr_op_, fdiv_q)
    .ENUM_VALUE(isl_ast_expr_op_, pdiv_q)
    .ENUM_VALUE(isl_ast_expr_op_, pdiv_r)
    .ENUM_VALUE(isl_ast_expr_op_, zdiv_r)
    .ENUM_VALUE(isl_ast_expr_op_, cond)
    .ENUM_VALUE(isl_ast_expr_op_, select)
    .ENUM_VALUE(isl_ast_expr_op_, eq)
    .ENUM_VALUE(isl_ast_expr_op_, le)
    .ENUM_VALUE(isl_ast_expr_op_, lt)
    .ENUM_VALUE(isl_ast_expr_op_, ge)
    .ENUM_VALUE(isl_ast_expr_op_, gt)
    .ENUM_VALUE(isl_ast_expr_op_, call)
    .ENUM_VALUE(isl_ast_expr_op_, access)
    .ENUM_VALUE(isl_ast_expr_op_, member)
    .ENUM_VALUE(isl_ast_expr_op_, address_of)
    ;

  py::enum_<isl_fold>(m, "fold")
    .ENUM_VALUE(isl_fold_, min)
    .ENUM_VALUE(isl_fold_, max)
    .ENUM_VALUE(isl_fold_, list)
    ;

  py::enum_<isl_ast_expr_type>(m, "ast_expr_type")
    .ENUM_VALUE(isl_ast_expr_, error)
    .ENUM_VALUE(isl_ast_expr_, op)
    .ENUM_VALUE(isl_ast_expr_, id)
    .ENUM_VALUE(isl_ast_expr_, int)
    ;

  py::enum_<isl_ast_node_type>(m, "ast_node_type")
    .ENUM_VALUE(isl_ast_node_, error)
    .value("for_", isl_ast_node_for)
    .value("if_", isl_ast_node_if)
    .ENUM_VALUE(isl_ast_node_, block)
    .ENUM_VALUE(isl_ast_node_, user)
    ;

  py::enum_<isl_ast_loop_type>(m, "ast_loop_type")
    .ENUM_VALUE(isl_ast_loop_, error)
    .ENUM_VALUE(isl_ast_loop_, default)
    .ENUM_VALUE(isl_ast_loop_, atomic)
    .ENUM_VALUE(isl_ast_loop_, unroll)
    .ENUM_VALUE(isl_ast_loop_, separate)
    ;

#define ADD_MACRO_ATTR(cls_name, prefix, name) cls_name.attr(#name) = prefix##name

  py::class_<isl::format> cls_format(m, "format");
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, ISL);
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, POLYLIB);
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, POLYLIB_CONSTRAINTS);
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, OMEGA);
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, C);
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, LATEX);
  ADD_MACRO_ATTR(cls_format, ISL_FORMAT_, EXT_POLYLIB);

  py::class_<isl::yaml_style> cls_yaml_style(m, "yaml_style");
  ADD_MACRO_ATTR(cls_yaml_style, ISL_YAML_STYLE_, BLOCK);
  ADD_MACRO_ATTR(cls_yaml_style, ISL_YAML_STYLE_, FLOW);

  py::class_<isl::bound> cls_bound(m, "bound");
  ADD_MACRO_ATTR(cls_bound, ISL_BOUND_, BERNSTEIN);
  ADD_MACRO_ATTR(cls_bound, ISL_BOUND_, RANGE);

  py::class_<isl::on_error> cls_on_error(m, "on_error");
  ADD_MACRO_ATTR(cls_on_error, ISL_ON_ERROR_, WARN);
  ADD_MACRO_ATTR(cls_on_error, ISL_ON_ERROR_, CONTINUE);
  ADD_MACRO_ATTR(cls_on_error, ISL_ON_ERROR_, ABORT);

  py::class_<isl::schedule_algorithm> cls_schedule_algorithm(m, "schedule_algorithm");
  ADD_MACRO_ATTR(cls_schedule_algorithm, ISL_SCHEDULE_ALGORITHM_, ISL);
  ADD_MACRO_ATTR(cls_schedule_algorithm, ISL_SCHEDULE_ALGORITHM_, FEAUTRIER);

  islpy_expose_part1(m);
  islpy_expose_part2(m);
  islpy_expose_part3(m);

  py::implicitly_convertible<isl::basic_set, isl::union_set>();

  py::implicitly_convertible<isl::basic_map, isl::union_map>();

  py::implicitly_convertible<isl::multi_aff, isl::union_pw_multi_aff>();

  // As far as I can tell, the reported leaks stem from the fact that we copy
  // many wrapper-exposed symbols from the wrapper namespace (islpy._isl) to
  // islpy, which keeps these alive past shutdown of the wrapper module (though
  // they should get cleaned up eventually!). -AK, 2023-09-08
  py::set_leak_warnings(false);
}
