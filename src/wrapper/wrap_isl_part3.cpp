#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part3.inc"
}

void islpy_expose_part3()
{
  MAKE_WRAP(qpolynomial_fold, QPolynomialFold);
  MAKE_WRAP(pw_qpolynomial_fold, PwQPolynomialFold);
  MAKE_WRAP(union_pw_qpolynomial_fold, UnionPwQPolynomialFold);
  MAKE_WRAP(union_pw_qpolynomial, UnionPwQPolynomial);

  MAKE_WRAP(qpolynomial, QPolynomial);
  MAKE_WRAP(pw_qpolynomial, PwQPolynomial);

  MAKE_WRAP(term, Term);

  MAKE_WRAP(band, Band);
  MAKE_WRAP(schedule, Schedule);
  MAKE_WRAP(schedule_constraints, ScheduleConstraints);
#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  MAKE_WRAP(schedule_node, ScheduleNode);
#endif

  MAKE_WRAP(access_info, AccessInfo);
  MAKE_WRAP(flow, Flow);
  MAKE_WRAP(restriction, Restriction);
#if !defined(ISLPY_ISL_VERSION) || (ISLPY_ISL_VERSION >= 15)
  MAKE_WRAP(union_access_info, UnionAccessInfo);
  MAKE_WRAP(union_flow, UnionFlow);
#endif

  MAKE_WRAP(ast_expr, AstExpr);
  MAKE_WRAP(ast_node, AstNode);
  MAKE_WRAP(ast_build, AstBuild);
  MAKE_WRAP(ast_print_options, AstPrintOptions);

#include "gen-expose-part3.inc"
}

