#include "wrap_isl.hpp"

namespace isl
{
#include "gen-wrap-part3.inc"
}

void islpy_expose_part3(py::module_ &m)
{
  MAKE_WRAP(qpolynomial, QPolynomial);
  MAKE_WRAP(pw_qpolynomial, PwQPolynomial);
  MAKE_WRAP(qpolynomial_fold, QPolynomialFold);
  MAKE_WRAP(pw_qpolynomial_fold, PwQPolynomialFold);
  MAKE_WRAP(union_pw_qpolynomial_fold, UnionPwQPolynomialFold);
  MAKE_WRAP(union_pw_qpolynomial, UnionPwQPolynomial);

  MAKE_WRAP(term, Term);

  MAKE_WRAP(schedule, Schedule);
  MAKE_WRAP(schedule_constraints, ScheduleConstraints);
  MAKE_WRAP(schedule_node, ScheduleNode);

  MAKE_WRAP(access_info, AccessInfo);
  MAKE_WRAP(flow, Flow);
  MAKE_WRAP(restriction, Restriction);
  MAKE_WRAP(union_access_info, UnionAccessInfo);
  MAKE_WRAP(union_flow, UnionFlow);

  MAKE_WRAP(ast_expr, AstExpr);
  MAKE_WRAP(ast_node, AstNode);
  MAKE_WRAP(ast_build, AstBuild);
  MAKE_WRAP(ast_print_options, AstPrintOptions);

#include "gen-expose-part3.inc"
}
