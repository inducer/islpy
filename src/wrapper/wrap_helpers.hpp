#ifndef PYCUDA_WRAP_HELPERS_HEADER_SEEN
#define PYCUDA_WRAP_HELPERS_HEADER_SEEN




#include <boost/version.hpp>
#include <boost/python.hpp>
#include <boost/python/stl_iterator.hpp>




namespace py = boost::python;




#if (BOOST_VERSION/100) < 1035
#warning *******************************************************************
#warning **** Your version of Boost C++ is likely too old for islpy.    ****
#warning *******************************************************************
#endif




#define PYTHON_ERROR(TYPE, REASON) \
{ \
  PyErr_SetString(PyExc_##TYPE, REASON); \
  throw boost::python::error_already_set(); \
}

#define ENUM_VALUE(PREFIX, NAME) \
  value(#NAME, PREFIX##NAME)

#define DEF_SIMPLE_METHOD(NAME) \
  def(#NAME, &cls::NAME)

#define DEF_SIMPLE_METHOD_WITH_ARGS(NAME, ARGS) \
  def(#NAME, &cls::NAME, boost::python::args ARGS)

#define DEF_SIMPLE_FUNCTION(NAME) \
  boost::python::def(#NAME, &NAME)

#define DEF_SIMPLE_FUNCTION_WITH_ARGS(NAME, ARGS) \
  boost::python::def(#NAME, &NAME, boost::python::args ARGS)

#define DEF_SIMPLE_RO_MEMBER(NAME) \
  def_readonly(#NAME, &cls::NAME)

#define DEF_SIMPLE_RW_MEMBER(NAME) \
  def_readwrite(#NAME, &cls::NAME)

#define PYTHON_FOREACH(NAME, ITERABLE) \
  BOOST_FOREACH(boost::python::object NAME, \
      std::make_pair( \
        boost::python::stl_input_iterator<boost::python::object>(ITERABLE), \
        boost::python::stl_input_iterator<boost::python::object>()))

#define COPY_PY_LIST(TYPE, NAME) \
  std::copy( \
      boost::python::stl_input_iterator<TYPE>(py_##NAME), \
      boost::python::stl_input_iterator<TYPE>(), \
      std::back_inserter(NAME));

namespace
{
  template <typename T>
  inline boost::python::handle<> handle_from_new_ptr(T *ptr)
  {
    return boost::python::handle<>(
        typename boost::python::manage_new_object::apply<T *>::type()(ptr));
  }
}

#endif
