#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part1.inc"

  class constants { };
}

namespace islpy
{
  bool id_eq(isl::id const *self, isl::id const *other)
  {
    return self == other;
  }

  bool id_ne(isl::id const *self, isl::id const *other)
  {
    return self != other;
  }
}

void islpy_expose_part1(py::module_ &m)
{
  py::class_<isl::ctx>
    wrap_ctx(m, "Context");
  wrap_ctx.def("__init__",
               [](isl::ctx *self)
               {
                 isl_ctx *result = isl_ctx_alloc();

                 // Sounds scary, but just means "don't print a message".
                 // We implement our own error handling.
                 isl_options_set_on_error(result, ISL_ON_ERROR_CONTINUE);

                 if (result)
                 {
                   try
                   {
                     new(self) isl::ctx(result);
                   }
                   catch (...)
                   {
                     isl_ctx_free(result);
                     throw;
                   }
                 }
                 else
                   PYTHON_ERROR(RuntimeError, "failed to create context");
               });
  wrap_ctx.attr("_base_name") = "ctx";
  wrap_ctx.attr("_isl_name") = "isl_ctx";
  wrap_ctx.def("_is_valid", &isl::ctx::is_valid);
  wrap_ctx.def("_reset_instance", &isl::ctx::reset_instance);
  wrap_ctx.def("_wraps_same_instance_as", &isl::ctx::wraps_same_instance_as);

  // {{{ lists

  MAKE_WRAP(id_list, IdList);
  MAKE_WRAP(val_list, ValList);
  MAKE_WRAP(basic_set_list, BasicSetList);
  MAKE_WRAP(basic_map_list, BasicMapList);
  MAKE_WRAP(set_list, SetList);
  MAKE_WRAP(map_list, MapList);
  MAKE_WRAP(union_set_list, UnionSetList);
  MAKE_WRAP(constraint_list, ConstraintList);
  MAKE_WRAP(aff_list, AffList);
  MAKE_WRAP(pw_aff_list, PwAffList);
  MAKE_WRAP(pw_multi_aff_list, PwMultiAffList);
  MAKE_WRAP(ast_expr_list, AstExprList);
  MAKE_WRAP(ast_node_list, AstNodeList);
  MAKE_WRAP(qpolynomial_list, QPolynomialList);
  MAKE_WRAP(pw_qpolynomial_list, PwQPolynomialList);
  MAKE_WRAP(pw_qpolynomial_fold_list, PwQPolynomialFoldList);
  MAKE_WRAP(union_pw_aff_list, UnionPwAffList);
  MAKE_WRAP(union_pw_multi_aff_list, UnionPwMultiAffList);
  MAKE_WRAP(union_map_list, UnionMapList);

  // }}}

  // {{{ maps

  MAKE_WRAP(id_to_ast_expr, IdToAstExpr);

  // }}}

  MAKE_WRAP(printer, Printer);
  MAKE_WRAP(val, Val);
  wrap_val.def("__init__",
      [](isl::val *t, long i, isl::ctx *ctx_wrapper)
      {
        isl_ctx *ctx = nullptr;
        if (ctx_wrapper && ctx_wrapper->is_valid())
          ctx = ctx_wrapper->m_data;
        if (!ctx)
          ctx = isl::get_default_context();
        if (!ctx)
          throw isl::error("Val constructor: no context available");
        isl_val *result = isl_val_int_from_si(ctx, i);
        if (result)
          new (t) isl::val(result);
        else
          isl::handle_isl_error(ctx, "isl_val_from_si");
      }, py::arg("i"), py::arg("context").none(true)=py::none()
      );

  MAKE_WRAP(multi_val, MultiVal);
  MAKE_WRAP(vec, Vec);
  MAKE_WRAP(mat, Mat);
  MAKE_WRAP(fixed_box, FixedBox);

  MAKE_WRAP(aff, Aff);

  MAKE_WRAP(pw_aff, PwAff);
  wrap_pw_aff.def(py::init_implicit<isl::aff const &>());

  MAKE_WRAP(union_pw_aff, UnionPwAff);
  wrap_union_pw_aff.def(py::init_implicit<isl::aff const &>());
  wrap_union_pw_aff.def(py::init_implicit<isl::pw_aff const &>());

  MAKE_WRAP(multi_id, MultiId);

  MAKE_WRAP(multi_aff, MultiAff);

  MAKE_WRAP(pw_multi_aff, PwMultiAff);
  wrap_pw_multi_aff.def(py::init_implicit<isl::multi_aff const &>());

  MAKE_WRAP(union_pw_multi_aff, UnionPwMultiAff);
  wrap_union_pw_multi_aff.def(py::init_implicit<isl::pw_multi_aff const &>());

  MAKE_WRAP(multi_pw_aff, MultiPwAff);

  MAKE_WRAP(multi_union_pw_aff, MultiUnionPwAff);

  MAKE_WRAP(id, Id);
  wrap_id.def("__init__",
      [](isl::id *t, const char *name, py::object user, isl::ctx *ctx_wrapper)
      {
        isl_ctx *ctx = nullptr;
        if (ctx_wrapper && ctx_wrapper->is_valid())
          ctx = ctx_wrapper->m_data;
        if (!ctx)
          ctx = isl::get_default_context();
        if (!ctx)
          throw isl::error("Id constructor: no context available");
        Py_INCREF(user.ptr());
        isl_id *result = isl_id_alloc(ctx, name, user.ptr());
        isl_id_set_free_user(result, isl::my_decref);
        if (result)
          new (t) isl::id(result);
        else
          isl::handle_isl_error(ctx, "isl_id_alloc");
      }, py::arg("name"),
      py::arg("user").none(true)=py::none(),
      py::arg("context").none(true)=py::none()
      );
  wrap_id.def("__eq__", islpy::id_eq, py::arg("other"),
      "__eq__(self, other)\n\n"
      ":param self: :class:`Id`\n"
      ":param other: :class:`Id`\n"
      ":return: bool ");
  wrap_id.def("__ne__", islpy::id_ne, py::arg("other"),
      "__ne__(self, other)\n\n"
      ":param self: :class:`Id`\n"
      ":param other: :class:`Id`\n"
      ":return: bool ");

  MAKE_WRAP(constraint, Constraint);

  MAKE_WRAP(space, Space);
  MAKE_WRAP(local_space, LocalSpace);
  wrap_local_space.def(py::init_implicit<isl::space const &>());

#include "gen-expose-part1.inc"
}
