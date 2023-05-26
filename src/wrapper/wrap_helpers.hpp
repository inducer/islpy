#ifndef PYCUDA_WRAP_HELPERS_HEADER_SEEN
#define PYCUDA_WRAP_HELPERS_HEADER_SEEN

#include <nanobind/nanobind.h>

namespace py = nanobind;


#define PYTHON_ERROR(TYPE, REASON) \
{ \
  PyErr_SetString(PyExc_##TYPE, REASON); \
  throw py::python_error(); \
}

#define ENUM_VALUE(PREFIX, NAME) \
  value(#NAME, PREFIX##NAME)

#define DEF_SIMPLE_METHOD(NAME) \
  def(#NAME, &cls::NAME)

#define DEF_SIMPLE_METHOD_WITH_ARGS(NAME, ARGS) \
  def(#NAME, &cls::NAME, py::args ARGS)

#define DEF_SIMPLE_FUNCTION(NAME) \
  py::def(#NAME, &NAME)

#define DEF_SIMPLE_FUNCTION_WITH_ARGS(NAME, ARGS) \
  py::def(#NAME, &NAME, py::args ARGS)

#define DEF_SIMPLE_RO_MEMBER(NAME) \
  def_readonly(#NAME, &cls::NAME)

#define DEF_SIMPLE_RW_MEMBER(NAME) \
  def_readwrite(#NAME, &cls::NAME)

namespace
{
  template <typename T>
  inline py::object handle_from_new_ptr(T *ptr)
  {
    return py::cast(ptr, py::rv_policy::take_ownership);
  }
}

#endif
