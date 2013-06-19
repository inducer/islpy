#ifndef ISL_INT_PY_H
#define ISL_INT_PY_H

#include <Python.h>

typedef PyObject **isl_int;

#define ISL_INT_PY_DECL_SPECIFIER static __attribute__ ((unused))

// {{{ helpers

#define ISL_INT_PY_HANDLE_PY_ERROR(ROUTINE) \
  { \
    fputs("*** error occurred in " #ROUTINE ", aborting.", stderr); \
    PyErr_PrintEx(1); \
    abort(); \
  }

#define ISL_INT_PY_THREE_OP_FUNC(ISL_NAME, PY_NAME) \
  ISL_INT_PY_DECL_SPECIFIER void isl_int_##ISL_NAME (isl_int r, isl_int i, isl_int j) \
  { \
    Py_DECREF(*r); \
    *r = PY_NAME(*i, *j); \
    if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME); \
  }

#define ISL_INT_PY_THREE_OP_UI_FUNC(ISL_NAME, PY_NAME) \
  ISL_INT_PY_DECL_SPECIFIER void isl_int_##ISL_NAME (isl_int r, isl_int i, unsigned long int j) \
  { \
    PyObject *j2 = PyLong_FromUnsignedLong(j); \
    if (!j2) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME); \
    \
    Py_DECREF(r); \
    *r = PY_NAME(*i, j2); \
    if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME); \
    Py_DECREF(j2); \
  }

// }}}

// {{{ init/get/set

ISL_INT_PY_DECL_SPECIFIER void isl_int_init(isl_int i)
{
  isl_int result = (isl_int) malloc(sizeof(PyObject *));
  if (!result)
  {
    perror("allocating isl_int");
    abort();
  }

  *result = PyLong_FromLong(0);
  if (!*i) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_init);
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_clear(isl_int i)
{
  Py_DECREF(*i);
  free(i);
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_set(isl_int r, isl_int i)
{
  Py_DECREF(*r);
  *r = *i;
  Py_INCREF(*r);
}

// isl_int_set_gmp(r, i)        mpz_set(r, i)

ISL_INT_PY_DECL_SPECIFIER void isl_int_set_si(isl_int r, signed long int i)
{
  Py_DECREF(*r);
  *r = PyLong_FromLong(i);
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_set_ui(isl_int r, unsigned long i)
{
  Py_DECREF(*r);
  *r = PyLong_FromUnsignedLong(i);
  if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_set_ui);
}

/* isl_int_get_gmp(i,g): no way */

ISL_INT_PY_DECL_SPECIFIER signed long int isl_int_get_si(isl_int r)
{
  return PyLong_AsLong(*r);
}

ISL_INT_PY_DECL_SPECIFIER unsigned long int isl_int_get_ui(isl_int r)
{
  return PyLong_AsUnsignedLong(*r);
}

ISL_INT_PY_DECL_SPECIFIER double isl_int_get_d(isl_int r)
{
  return PyLong_AsDouble(*r);
}

ISL_INT_PY_DECL_SPECIFIER char *isl_int_get_str(isl_int r)
{
  PyObject *str = PyObject_Str(*r);
  if (!str) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_get_str);
  char *result = PyString_AsString(str);
  if (!result) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_get_str);
  result = strdup(result);
  if (!result)
  {
    fputs("error duplicating string in isl_int_get_str", stderr);
    abort();
  }
  Py_DECREF(str);
  return result;
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_free_str(char *s)
{
  free(s);
}

// }}}

ISL_INT_PY_DECL_SPECIFIER void isl_int_abs(isl_int r, isl_int i)
{
  Py_DECREF(*r);
  *r = PyNumber_Absolute(*i);
  if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_abs);
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_neg(isl_int r, isl_int i)
{
  Py_DECREF(*r);
  *r = PyNumber_Negative(*i);
  if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_neg);
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_swap(isl_int i, isl_int j)
{
  PyObject *tmp = *i;
  *i = *j;
  *j = tmp;
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_swap_or_set(isl_int i, isl_int j)
{
  isl_int_swap(i, j);
}

// {{{ arithmetic

ISL_INT_PY_THREE_OP_UI_FUNC(add_ui, PyNumber_Add);
ISL_INT_PY_THREE_OP_UI_FUNC(sub_ui, PyNumber_Subtract);

ISL_INT_PY_THREE_OP_FUNC(add, PyNumber_Add);
ISL_INT_PY_THREE_OP_FUNC(sub, PyNumber_Subtract);
ISL_INT_PY_THREE_OP_FUNC(mul, PyNumber_Multiply);

ISL_INT_PY_THREE_OP_UI_FUNC(mul_2exp, PyNumber_Lshift);
ISL_INT_PY_THREE_OP_UI_FUNC(mul_ui, PyNumber_Multiply);

ISL_INT_PY_DECL_SPECIFIER void isl_int_pow_ui(isl_int r, isl_int i, unsigned long int j)
{
  PyObject *j2 = PyLong_FromUnsignedLong(j);
  if (!j2) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME);

  Py_DECREF(r);
  *r = PyNumber_Power(*i, j2, Py_None);
  if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME);
  Py_DECREF(j2);
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_addmul(isl_int r, isl_int i, isl_int j)
{
  PyObject *ij = PyNumber_Multiply(*i, *j);
  if (!ij) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_addmul);

  PyObject *newr = PyNumber_Add(*r, ij);
  Py_DECREF(ij);
  if (!newr) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_addmul);

  Py_DECREF(r);
  *r = newr;
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_submul(isl_int r, isl_int i, isl_int j)
{
  PyObject *ij = PyNumber_Multiply(*i, *j);
  if (!ij) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_addmul);

  PyObject *newr = PyNumber_Subtract(*r, ij);
  Py_DECREF(ij);
  if (!newr) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_addmul);

  Py_DECREF(r);
  *r = newr;
}

// }}}

ISL_INT_PY_DECL_SPECIFIER void isl_int_gcd(isl_int r, isl_int u, isl_int v)
{
  // from https://en.wikipedia.org/wiki/Binary_GCD_algorithm

  // simple cases (termination)
  int res = PyObject_RichCompareBool(*i, *j, Py_EQ); \
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_gcd);
  if (res == 1)
  {
    Py_DECREF(*r);
    *r = *u;
    Py_INCREF(*r);
    return;
  }

  res = PyObject_Not(*u);
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_gcd);
  if (res == 1)
  {
    Py_DECREF(*r);
    *r = *v;
    Py_INCREF(*r);
    return;
  }

  res = PyObject_Not(*v);
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_gcd);
  if (res == 1)
  {
    Py_DECREF(*r);
    *r = *u;
    Py_INCREF(*r);
    return;
  }

  // FIXME
  // look for factors of 2
  if (~u & 1) // u is even
  {
      if (v & 1) // v is odd
          return gcd(u >> 1, v);
      else // both u and v are even
          return gcd(u >> 1, v >> 1) << 1;
  }

  if (~v & 1) // u is odd, v is even
      return gcd(u, v >> 1);

  // reduce larger argument
  if (u > v)
      return gcd((u - v) >> 1, v);

  return gcd((v - u) >> 1, u);
}


ISL_INT_PY_DECL_SPECIFIER void isl_int_lcm(isl_int r, isl_int i, isl_int j)
{
  // FIXME
  // return i*j/gcd
  fputs("isl_int_lcm unimplemented", stderr);
  abort();
}

/* not exploiting performance increase for exactness, but ok */
ISL_INT_PY_THREE_OP_FUNC(divexact, PyNumber_FloorDivide);
ISL_INT_PY_THREE_OP_UI_FUNC(divexact_ui, PyNumber_FloorDivide);

ISL_INT_PY_DECL_SPECIFIER void isl_int_tdiv_q(isl_int r, isl_int i, isl_int j)
{
  // FIXME
  fputs("isl_int_tdiv_q unimplemented", stderr);
  abort();
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_cdiv_q(isl_int r, isl_int i, isl_int j)
{
  // FIXME
  fputs("isl_int_cdiv_q unimplemented", stderr);
  abort();
}

ISL_INT_PY_THREE_OP_FUNC(fdiv_q, PyNumber_FloorDivide);

ISL_INT_PY_DECL_SPECIFIER void isl_int_fdiv_r(isl_int r, isl_int i, isl_int j)
{
  // FIXME: Different behavior for negative j
  fputs("isl_int_fdiv_r unimplemented", stderr);
  abort();
}

ISL_INT_PY_THREE_OP_UI_FUNC(fdiv_q_ui, PyNumber_FloorDivide);

ISL_INT_PY_DECL_SPECIFIER int isl_int_read(isl_int r, char *s)
{
  *r = PyLong_FromString(s, NULL, 10);
  if (!*r)
  {
    PyErr_Clear();
    return -1;
  }
  else
    return 0;
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_print(FILE *out, isl_int i, int width)
{
  PyObject *py_str = PyObject_Str(*i);
  if (!py_str)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_print);
  char *s = PyString_AsString(PyObject *string)
  if (!s)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_print);
  fprintf(out, "%*s", width, s);
  Py_DECREF(py_str);
}


#define isl_int_sgn(i) isl_int_cmp_si(i, 0)


ISL_INT_PY_DECL_SPECIFIER int isl_int_cmp(isl_int i, isl_int j)
{
  int res = PyObject_RichCompareBool(*i, *j, Py_GT); \
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmp);
  if (res == 1)
    return 1;
  int res = PyObject_RichCompareBool(*i, *j, Py_EQ); \
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmp);
  if (res == 1)
    return 0;
  return -1;
}

ISL_INT_PY_DECL_SPECIFIER int isl_int_cmp_si(isl_int i, long int si)
{
  PyObject *j = PyLong_FromLong(si);
  if (!j)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmp_si);

  int res = PyObject_RichCompareBool(*i, j, Py_GT); \
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmp_si);
  if (res == 1)
  {
    Py_DECREF(j);
    return 1;
  }
  int res = PyObject_RichCompareBool(*i, j, Py_EQ); \
  if (res == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmp_si);
  Py_DECREF(j);
  if (res == 1)
    return 0;
  return -1;
}

// {{{ "rich" comparisons

#define ISL_INT_PY_DEFINE_COMPARISON(LOWER, UPPER) \
  inline bool isl_int_#LOWER(isl_int i, isl_int j) \
  { \
    int res = PyObject_RichCompareBool(*i, *j, Py_#UPPER); \
    if (res == -1) \
      ISL_INT_PY_HANDLE_PY_ERROR(isl_int_#LOWER); \
    return res == 1; \
  }

ISL_INT_PY_DEFINE_COMPARISON(eq, EQ)
ISL_INT_PY_DEFINE_COMPARISON(ne, NE)
ISL_INT_PY_DEFINE_COMPARISON(lt, LT)
ISL_INT_PY_DEFINE_COMPARISON(le, LE)
ISL_INT_PY_DEFINE_COMPARISON(gt, GT)
ISL_INT_PY_DEFINE_COMPARISON(ge, GE)

#define ISL_INT_PY_DEFINE_ABS_COMPARISON(LOWER, UPPER) \
  inline bool isl_int_abs_#LOWER(isl_int i, isl_int j) \
  { \
    PyObject *ai = PyNumber_Absolute(*i); \
    if (!ai) \
      ISL_INT_PY_HANDLE_PY_ERROR(isl_int_abs_#LOWER); \
    PyObject *aj = PyNumber_Absolute(*j); \
    if (!aj) \
      ISL_INT_PY_HANDLE_PY_ERROR(isl_int_abs_#LOWER); \
    int res = PyObject_RichCompareBool(ai, aj, Py_#UPPER); \
    if (res == -1) \
      ISL_INT_PY_HANDLE_PY_ERROR(isl_int_abs_#LOWER); \
    Py_DECREF(ai); \
    Py_DECREF(aj); \
    return res == 1; \
  }

ISL_INT_PY_DEFINE_ABS_COMPARISON(eq, EQ)
ISL_INT_PY_DEFINE_ABS_COMPARISON(ne, NE)
ISL_INT_PY_DEFINE_ABS_COMPARISON(lt, LT)
ISL_INT_PY_DEFINE_ABS_COMPARISON(le, LE)
ISL_INT_PY_DEFINE_ABS_COMPARISON(gt, GT)
ISL_INT_PY_DEFINE_ABS_COMPARISON(ge, GE)

// }}}

#define isl_int_is_zero(i)      (isl_int_sgn(i) == 0)
#define isl_int_is_one(i)       (isl_int_cmp_si(i,1) == 0)
#define isl_int_is_negone(i)    (isl_int_cmp_si(i,-1) == 0)
#define isl_int_is_pos(i)       (isl_int_sgn(i) > 0)
#define isl_int_is_neg(i)       (isl_int_sgn(i) < 0)
#define isl_int_is_nonpos(i)    (isl_int_sgn(i) <= 0)
#define isl_int_is_nonneg(i)    (isl_int_sgn(i) >= 0)

ISL_INT_PY_DECL_SPECIFIER int isl_int_is_divisible_by(isl_int i, isl_int j)
{
  if (PyObject_IsTrue(*j))
  {
    /* j != 0 */
    PyObject *remdr = PyNumber_Remainder(*i, *j);
    if (!remdr)
      ISL_INT_PY_HANDLE_PY_ERROR(isl_int_is_divisible_by);
    int remdr_zero = PyObject_Not(remdr);
    if (remdr_zero == -1)
      ISL_INT_PY_HANDLE_PY_ERROR(isl_int_is_divisible_by);

    Py_DECREF(remdr);
    return remdr_zero == 1;
  }
  else
  {
    /* j == 0 -- only true if i == 0 as well */
    return PyObject_Not(*i);
  }
}

ISL_INT_PY_DECL_SPECIFIER uint32_t isl_int_hash(isl_int v, uint32_t hash)
{
  long py_hash = PyObject_Hash(*v);
  if (py_hash == -1)
    ISL_INT_PY_HANDLE_PY_ERROR(isl_int_hash);

  // Likely truncates, oh well.
   return (uint32_t) py_hash ^ hash;
}

#endif

// vim: foldmethod=marker
