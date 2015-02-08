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

void islpy_expose_part1()
{
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

  // {{{ lists

  MAKE_WRAP(id_list, IdList);

  MAKE_WRAP(val_list, ValList);
  MAKE_WRAP(aff_list, AffList);
  MAKE_WRAP(pw_aff_list, PwAffList);

  MAKE_WRAP(basic_set_list, BasicSetList);
#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  MAKE_WRAP(basic_map_list, BasicMapList);
#endif
  MAKE_WRAP(set_list, SetList);
#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  MAKE_WRAP(map_list, MapList);
  MAKE_WRAP(union_set_list, UnionSetList);
#endif

  MAKE_WRAP(ast_expr_list, AstExprList);
  MAKE_WRAP(ast_node_list, AstNodeList);
  MAKE_WRAP(band_list, BandList);

  // }}}

  // {{{ maps

  MAKE_WRAP(id_to_ast_expr, IdToAstExpr);

  // }}}

  MAKE_WRAP(printer, Printer);
  MAKE_WRAP(val, Val);

  MAKE_WRAP(multi_val, MultiVal);
  MAKE_WRAP(vec, Vec);
  MAKE_WRAP(mat, Mat);

  MAKE_WRAP(aff, Aff);
  wrap_aff.enable_pickling();
  MAKE_WRAP(pw_aff, PwAff);
  wrap_pw_aff.enable_pickling();
#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  MAKE_WRAP(union_pw_aff, UnionPwAff);
  wrap_union_pw_aff.enable_pickling();
#endif
  MAKE_WRAP(multi_aff, MultiAff);
  wrap_multi_aff.enable_pickling();
  MAKE_WRAP(multi_pw_aff, MultiPwAff);
  wrap_multi_pw_aff.enable_pickling();
  MAKE_WRAP(pw_multi_aff, PwMultiAff);
  wrap_pw_multi_aff.enable_pickling();
  MAKE_WRAP(union_pw_multi_aff, UnionPwMultiAff);
  wrap_union_pw_multi_aff.enable_pickling();
#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  MAKE_WRAP(multi_union_pw_aff, MultiUnionPwAff);
  wrap_multi_union_pw_aff.enable_pickling();
#endif

  MAKE_WRAP(id, Id);
  wrap_id.def("__eq__", islpy::id_eq, py::args("self", "other"),
      "__eq__(self, other)\n\n"
      ":param self: :class:`Id`\n"
      ":param other: :class:`Id`\n"
      ":return: bool ");
  wrap_id.def("__ne__", islpy::id_ne, py::args("self", "other"),
      "__ne__(self, other)\n\n"
      ":param self: :class:`Id`\n"
      ":param other: :class:`Id`\n"
      ":return: bool ");

  MAKE_WRAP(constraint, Constraint);
  wrap_constraint.enable_pickling();
  MAKE_WRAP(space, Space);
  MAKE_WRAP(local_space, LocalSpace);

#include "gen-expose-part1.inc"
}
