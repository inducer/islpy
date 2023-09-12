cmake_minimum_required(VERSION 3.18...3.22)
project(islpy)
find_package(Python 3.8 COMPONENTS Interpreter Development.Module REQUIRED)

# Force Release build by default
if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING Choose the type of build. FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

# Detect the installed nanobind package and import it into CMake
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")
find_package(nanobind CONFIG REQUIRED)

IF(DEFINED ENV{CIBUILDWHEEL})
  set(NOMINSIZE "")
else()
  set(NOMINSIZE "NOMINSIZE")
endif()

nanobind_add_module(
  _isl
  NB_STATIC # Build static libnanobind (the extension module itself remains a shared library)
  ${NOMINSIZE} # Optimize for speed, not for size
  LTO       # Enable LTO
  src/wrapper/wrap_isl.cpp
  src/wrapper/wrap_isl_part1.cpp
  src/wrapper/wrap_isl_part2.cpp
  src/wrapper/wrap_isl_part3.cpp
  ${ISL_SOURCES}
)

if(USE_IMATH_FOR_MP)
  target_compile_definitions(_isl PRIVATE USE_IMATH_FOR_MP=1)
endif()

if(USE_IMATH_SIO)
  target_compile_definitions(_isl PRIVATE USE_SMALL_INT_OPT=1)
endif()

if(USE_GMP_FOR_MP)
  target_compile_definitions(_isl PRIVATE USE_GMP_FOR_MP=1)
endif()

if(USE_BARVINOK)
  target_compile_definitions(_isl PRIVATE ISLPY_INCLUDE_BARVINOK=1)
  target_include_directories(_isl PRIVATE ${BARVINOK_INC_DIRS})
  target_link_directories(_isl PRIVATE ${BARVINOK_LIB_DIRS})
  target_link_libraries(_isl PRIVATE ${BARVINOK_LIB_NAMES})
endif()

target_include_directories(_isl PRIVATE ${ISL_INC_DIRS})

if(NOT USE_SHIPPED_ISL)
  target_link_directories(_isl PRIVATE ${ISL_LIB_DIRS})
  target_link_libraries(_isl PRIVATE ${ISL_LIB_NAMES})
endif()

install(TARGETS _isl LIBRARY DESTINATION .)

# vim: sw=2
