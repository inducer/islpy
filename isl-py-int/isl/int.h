#ifndef ISL_INT_PY_H
#define ISL_INT_PY_H

#include <Python.h>

#define ISL_INT_PY_DECL_SPECIFIER static __attribute__ ((unused))

typedef PyObject **isl_int;

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

ISL_INT_PY_DECL_SPECIFIER void isl_int_gcd(isl_int r, isl_int i, isl_int j)
{
  // FIXME
  fputs("isl_int_gcd unimplemented", stderr);
  abort();
}

ISL_INT_PY_DECL_SPECIFIER void isl_int_lcm(isl_int r, isl_int i, isl_int j)
{
  // FIXME
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
  fputs("isl_int_print unimplemented", stderr); /* and that's fine. */
  abort();
}

ISL_INT_PY_DECL_SPECIFIER int isl_int_sgn(isl_int i)
{
  PyObject *zero = PyLong_FromLong(0);
  if (!zero) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_sgn);

  int result = PyObject_Compare(*i, zero);

  Py_DECREF(zero);
  return result;
}

ISL_INT_PY_DECL_SPECIFIER int isl_int_cmp(isl_int i, isl_int j)
{
  return PyObject_Compare(*i, *j);
}

ISL_INT_PY_DECL_SPECIFIER int isl_int_cmp_si(isl_int i, signed long si)
{
  PyObject *si2 = PyLong_FromLong(si);
  if (!si2) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmp_si);

  int result = PyObject_Compare(*i, si2);
  Py_DECREF(si2);
  return result;
}

#define isl_int_eq(i,j) (isl_int_cmp(i,j) == 0)
#define isl_int_ne(i,j) (isl_int_cmp(i,j) != 0)
#define isl_int_lt(i,j) (isl_int_cmp(i,j) < 0)
#define isl_int_le(i,j) (isl_int_cmp(i,j) <= 0)
#define isl_int_gt(i,j) (isl_int_cmp(i,j) > 0)
#define isl_int_ge(i,j) (isl_int_cmp(i,j) >= 0)

ISL_INT_PY_DECL_SPECIFIER int isl_int_cmpabs(isl_int i, isl_int j)
{
  PyObject *iabs = PyNumber_Absolute(*i);
  if (!iabs) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmpabs);

  PyObject *jabs = PyNumber_Absolute(*j);
  if (!jabs) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_cmpabs);

  int result = PyObject_Compare(iabs, jabs);

  Py_DECREF(iabs);
  Py_DECREF(jabs);
  return result;
}

#define isl_int_abs_eq(i,j)     (isl_int_cmpabs(i,j) == 0)
#define isl_int_abs_ne(i,j)     (isl_int_cmpabs(i,j) != 0)
#define isl_int_abs_lt(i,j)     (isl_int_cmpabs(i,j) < 0)
#define isl_int_abs_gt(i,j)     (isl_int_cmpabs(i,j) > 0)
#define isl_int_abs_ge(i,j)     (isl_int_cmpabs(i,j) >= 0)

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
    PyObject *rem = PyNumber_Remainder(*i, *j);
    if (!rem) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_is_divisible_by);

    int result = PyObject_Not(rem);
    Py_DECREF(rem);
    return result;
  }
  else
  {
    /* j == 0 -- only true if i == 0 as well */
    return PyObject_Not(*i);
  }
}

ISL_INT_PY_DECL_SPECIFIER uint32_t isl_int_hash(isl_int v, uint32_t hash)
{
  return (uint32_t) PyObject_Hash(*v) ^ hash;
}

#endif
