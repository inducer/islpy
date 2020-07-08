#ifndef PYCUDA_WRAP_HELPERS_HEADER_SEEN
#define PYCUDA_WRAP_HELPERS_HEADER_SEEN



#include <pybind11/pybind11.h>
#include <pybind11/operators.h>


namespace py = pybind11;


#define PYTHON_ERROR(TYPE, REASON) \
{ \
  PyErr_SetString(PyExc_##TYPE, REASON); \
  throw pybind11::error_already_set(); \
}

#define ENUM_VALUE(PREFIX, NAME) \
  value(#NAME, PREFIX##NAME)

#define DEF_SIMPLE_METHOD(NAME) \
  def(#NAME, &cls::NAME)

#define DEF_SIMPLE_METHOD_WITH_ARGS(NAME, ARGS) \
  def(#NAME, &cls::NAME, pybind11::args ARGS)

#define DEF_SIMPLE_FUNCTION(NAME) \
  pybind11::def(#NAME, &NAME)

#define DEF_SIMPLE_FUNCTION_WITH_ARGS(NAME, ARGS) \
  pybind11::def(#NAME, &NAME, pybind11::args ARGS)

#define DEF_SIMPLE_RO_MEMBER(NAME) \
  def_readonly(#NAME, &cls::NAME)

#define DEF_SIMPLE_RW_MEMBER(NAME) \
  def_readwrite(#NAME, &cls::NAME)

namespace
{
  template <typename T>
  inline pybind11::object handle_from_new_ptr(T *ptr)
  {
    return py::cast(ptr, py::return_value_policy::take_ownership);
  }
}

#endif
