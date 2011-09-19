#ifndef ISL_INT_PY_H
#define ISL_INT_PY_H

#include <Python.h>

typedef PyObject **isl_int;

#define ISL_INT_PY_HANDLE_PY_ERROR(ROUTINE) \
  { \
    fputs(stderr, "*** error occurred in " #ROUTINE ", aborting."); \
    PyErr_PrintEx(1); \
    abort(); \
  }

#define ISL_INT_PY_THREE_OP_FUNC(ISL_NAME, PY_NAME) \
  inline void isl_int_##ISL_NAME (isl_int r, isl_int i, isl_int j) \
  { \
    Py_DECREF(*r); \
    *r = PY_NAME(*i, *j); \
    if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME); \
  }

#define ISL_INT_PY_THREE_OP_UI_FUNC(ISL_NAME, PY_NAME) \
  inline void isl_int_##ISL_NAME (isl_int r, isl_int i, unsinged long int j) \
  { \
    isl_int j2 = PyLong_FromUnsignedLong(j); \
    if (!j2) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME); \
    \
    Py_DECREF(r); \
    *r = PY_NAME(*i, j2); \
    if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_##ISL_NAME); \
    PyDECREF(j2); \
  }

inline void isl_int_init(isl_int i)
{
  isl_int result = malloc(sizeof(PyObject *));
  if (!result)
  {
    perror("allocating isl_int");
    abort();
  }

  *result = PyLong_FromLong(0);
  if (!*i) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_init);
}

inline void isl_int_clear(i)
{
  Py_DECREF(*i);
  free(i);
}

inline void isl_int_set(isl_int r, isl_int i)
{
  Py_DECREF(*r);
  *r = *i;
  Py_INCREF(*r);
}

// isl_int_set_gmp(r, i)	mpz_set(r, i)

inline void isl_int_set_si(isl_int r, signed long int i)
{
  Py_DECREF(*r);
  *r = PyLong_FromLong(*i);
}

inline void isl_int_set_ui(isl_int *r, isl_int *i)
{
  Py_DECREF(*r);
  *r = PyLong_FromUnsignedLong(*i);
  if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_set_ui);
}

// isl_int_get_gmp(i,g)

inline void signed long int isl_int_get_si(isl_int r)
{
  return PyLong_AsLong(*r);
}

inline void unsigned long int isl_int_get_ui(isl_int r)
{
  return PyLong_AsUnsignedLong(*r);
}

inline isl_int_get_d(isl_int r)
{
  return PyLong_AsDouble(*r)
}

inline char *isl_int_get_str(isl_int r)
{
  PyObject *str = PyObject_Str(*r);
  if (!str) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_get_str);
  char *result = PyString_AsString(str);
  if (!result) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_get_str);
  Py_DECREF(str);
  return result; 
#error FIXME: Wrong--would be freed using gmp.
}

inline void isl_int_abs(isl_int r, isl_int i)
{
  Py_DECREF(*r);
  *r = PyNumber_Absolute(*i);
  if (!*r) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_abs);
}

inline void isl_int_neg(isl_int r, isl_int i)
{
  Py_DECREF(*r);
  *r = PyNumber_Negative(*i);
  if (!str) ISL_INT_PY_HANDLE_PY_ERROR(isl_int_abs);
}

inline void isl_int_swap(isl_int i, isl_int j)
{
  PyObject *tmp = *i;
  *i = *j;
  *j = tmp;
}

inline void isl_int_swap_or_set(isl_int i, isl_int j)
{
  isl_int_swap(i, j);
}

ISL_INT_PY_THREE_OP_UI_FUNC(add_ui, PyNumber_Add);
ISL_INT_PY_THREE_OP_UI_FUNC(sub_ui, PyNumber_Subtract);

ISL_INT_PY_THREE_OP_FUNC(add, PyNumber_Add);
ISL_INT_PY_THREE_OP_FUNC(sub, PyNumber_Subtract);
ISL_INT_PY_THREE_OP_FUNC(mul, PyNumber_Multiply);

ISL_INT_PY_THREE_OP_UI_FUNC(mul_2exp, PyNumber_LShift);
ISL_INT_PY_THREE_OP_UI_FUNC(mul_ui, PyNumber_Multiply);
ISL_INT_PY_THREE_OP_UI_FUNC(pow_ui, PyNumber_Power);

isl_int_addmul(isl_int r, isl_int i, isl_int j)
isl_int_submul(isl_int r, isl_int i, isl_int j)

isl_int_gcd(isl_int r, isl_int i, isl_int j)
isl_int_lcm(isl_int r, isl_int i, isl_int j)

// FIXME: not exploiting performance increase for exactness
ISL_INT_PY_THREE_OP_FUNC(divexact, PyNumber_FloorDiv);
ISL_INT_PY_THREE_OP_UI_FUNC(divexact_ui, PyNumber_FloorDiv);

isl_int_tdiv_q(isl_int r, isl_int i, isl_int j)
isl_int_cdiv_q(isl_int r, isl_int i, isl_int j)

ISL_INT_PY_THREE_OP_FUNC(fdiv_q, PyNumber_FloorDiv);

// FIXME: Different behavior for negative j
isl_int_fdiv_r(isl_int r, isl_int i, isl_int j)

ISL_INT_PY_THREE_OP_UI_FUNC(fdiv_q_ui, PyNumber_FloorDiv);

isl_int_read(r,s)	mpz_set_str(r,s,10)

#define isl_int_print(out, i,width)					\
	do {								\
		char *s;						\
		isl_int_print_gmp_free_t gmp_free;			\
		s = mpz_get_str(0, 10, i);				\
		fprintf(out, "%*s", width, s);				\
		mp_get_memory_functions(NULL, NULL, &gmp_free);		\
		(*gmp_free)(s, strlen(s)+1);				\
	} while (0)

isl_int_sgn(isl_int i)
isl_int_cmp(isl_int i, isl_int j)
isl_int_cmp_si(isl_int i,si)
isl_int_eq(isl_int i, isl_int j)
isl_int_ne(isl_int i, isl_int j)
isl_int_lt(isl_int i, isl_int j)
isl_int_le(isl_int i, isl_int j)
isl_int_gt(isl_int i, isl_int j)
isl_int_ge(isl_int i, isl_int j)
isl_int_abs_eq(isl_int i, isl_int j)
isl_int_abs_ne(isl_int i, isl_int j)
isl_int_abs_lt(isl_int i, isl_int j)
isl_int_abs_gt(isl_int i, isl_int j)
isl_int_abs_ge(isl_int i, isl_int j)


isl_int_is_zero(isl_int i)
isl_int_is_one(isl_int i)
isl_int_is_negone(isl_int i)
isl_int_is_pos(isl_int i)
isl_int_is_neg(isl_int i)
isl_int_is_nonpos(isl_int i)
isl_int_is_nonneg(isl_int i)
isl_int_is_divisible_by(isl_int i, isl_int j)

inline uint32_t isl_int_hash(isl_int v, uint32_t hash)
{
  xxx
}

#endif
