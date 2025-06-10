# Useful setting for looking at build commands (passed to pip install):
# --config-settings=cmake.define.CMAKE_VERBOSE_MAKEFILE=ON
#
# To build with debug info: Run pip install with
# --config-settings=cmake.build-type=Debug
# Note that setting CMAKE_BUILD_TYPE to Debug here does not suffice:
# scikit build core will still silently strip the debug symbols:
# https://github.com/scikit-build/scikit-build-core/issues/875

cmake_minimum_required(VERSION 3.15...3.27)
project(islpy)
find_package(Python 3.10 COMPONENTS Interpreter Development.Module REQUIRED)

# Detect the installed nanobind package and import it into CMake
execute_process(
    COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
    OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")
find_package(nanobind CONFIG REQUIRED)

option(USE_SHIPPED_ISL "Use shipped ISL" ON)
option(USE_SHIPPED_IMATH "Use shipped IMATH" ON)
option(USE_IMATH_FOR_MP "Use IMATH for multiprecision arithmetic" ON)
option(USE_IMATH_SIO "Use IMATH small-integer optimization" ON)
option(USE_GMP_FOR_MP "Use GMP" OFF)
option(USE_BARVINOK "Use Barvinok (beware of GPL license)" OFF)
option(GENERATE_STUBS "Generate stubs as part of build" ON)

if(USE_SHIPPED_ISL)
    if(USE_BARVINOK)
        message(FATAL_ERROR "Using barvinok is not compatible with shipped ISL")
    endif()
    set(ISL_SOURCES
        isl/isl_schedule.c
        isl/isl_ast_build_expr.c
        isl/isl_sample.c
        isl/isl_coalesce.c
        isl/isl_fold.c
        isl/isl_schedule_read.c
        isl/isl_aff_map.c
        isl/isl_scheduler_clustering.c
        isl/isl_flow.c
        isl/isl_map_subtract.c
        isl/uset_to_umap.c
        isl/isl_hash.c
        isl/isl_aff.c
        isl/isl_transitive_closure.c
        isl/isl_map_simplify.c
        isl/print.c
        isl/basis_reduction_tab.c
        isl/isl_schedule_constraints.c
        isl/isl_sort.c
        isl/isl_ast.c
        isl/bset_to_bmap.c
        isl/bset_from_bmap.c
        isl/isl_schedule_band.c
        isl/isl_bernstein.c
        isl/uset_from_umap.c
        isl/isl_scheduler.c
        isl/isl_set_to_ast_graft_list.c
        isl/isl_convex_hull.c
        isl/isl_schedule_tree.c
        isl/isl_tarjan.c
        isl/isl_equalities.c
        isl/isl_constraint.c
        isl/isl_union_map.c
        isl/isl_bound.c
        isl/isl_stride.c
        isl/set_list_from_map_list_inl.c
        isl/isl_farkas.c
        isl/isl_tab_pip.c
        isl/set_to_map.c
        isl/set_from_map.c
        isl/isl_lp.c
        isl/isl_ffs.c
        isl/isl_id_to_ast_expr.c
        isl/isl_val.c
        isl/isl_set_list.c
        isl/isl_space.c
        isl/isl_tab.c
        isl/isl_map.c
        isl/isl_version.c
        isl/isl_stream.c
        isl/isl_local_space.c
        isl/isl_id_to_pw_aff.c
        isl/isl_ilp.c
        isl/isl_range.c
        isl/isl_point.c
        isl/isl_schedule_node.c
        isl/isl_polynomial.c
        isl/isl_options.c
        isl/isl_morph.c
        isl/isl_deprecated.c
        isl/isl_ctx.c
        isl/isl_seq.c
        isl/isl_box.c
        isl/isl_output.c
        isl/isl_factorization.c
        isl/isl_printer.c
        isl/dep.c
        isl/isl_id_to_id.c
        isl/isl_ast_build.c
        isl/isl_ast_codegen.c
        isl/isl_obj.c
        isl/isl_scheduler_scc.c
        isl/isl_vec.c
        isl/isl_map_list.c
        isl/isl_vertices.c
        isl/isl_arg.c
        isl/isl_mat.c
        isl/isl_id.c
        isl/isl_affine_hull.c
        isl/isl_scan.c
        isl/isl_map_to_basic_set.c
        isl/isl_blk.c
        isl/isl_dim_map.c
        isl/isl_local.c
        isl/isl_reordering.c
        isl/isl_ast_graft.c
        isl/isl_input.c
    )
    set(ISL_INC_DIRS
        ${CMAKE_SOURCE_DIR}/isl-supplementary
        ${CMAKE_SOURCE_DIR}/isl/include
        ${CMAKE_SOURCE_DIR}/isl
    )
    if(USE_GMP_FOR_MP)
        list(APPEND ISL_SOURCES
            isl/isl_val_gmp.c
        )
    elseif(USE_IMATH_FOR_MP)
        if(USE_SHIPPED_IMATH)
            list(APPEND ISL_SOURCES
                isl/isl_imath.c
                isl/imath/imath.c
                isl/imath/imrat.c
                isl/imath/gmp_compat.c
            )
            list(APPEND ISL_INC_DIRS ${CMAKE_SOURCE_DIR}/isl/imath)
        endif()
        if(USE_IMATH_SIO)
            list(APPEND ISL_SOURCES
                isl/isl_int_sioimath.c
                isl/isl_val_sioimath.c
            )
        else()
            list(APPEND ISL_SOURCES
                isl/isl_val_imath.c
            )
        endif()
    endif()
else()
    set(ISL_SOURCES)
    if(NOT ISL_LIB_NAMES)
        set(ISL_LIB_NAMES isl)
        if(USE_BARVINOK)
            list(PREPEND ISL_LIB_NAMES barvinok)
        endif()
    endif()
endif()

set(ISLPY_GENERATED_SOURCE
    ${CMAKE_BINARY_DIR}/generated/gen-expose-part1.inc
    ${CMAKE_BINARY_DIR}/generated/gen-expose-part2.inc
    ${CMAKE_BINARY_DIR}/generated/gen-expose-part3.inc
    ${CMAKE_BINARY_DIR}/generated/gen-wrap-part1.inc
    ${CMAKE_BINARY_DIR}/generated/gen-wrap-part2.inc
    ${CMAKE_BINARY_DIR}/generated/gen-wrap-part3.inc
)

if(USE_BARVINOK)
    set(ISLPY_GENERATION_FLAGS --barvinok)
else()
    set(ISLPY_GENERATION_FLAGS)
endif()

add_custom_command(
    OUTPUT ${ISLPY_GENERATED_SOURCE}
    COMMAND ${Python_EXECUTABLE} ${CMAKE_SOURCE_DIR}/gen_wrap.py
        -o ${CMAKE_BINARY_DIR}/generated
        -I ${ISL_INC_DIRS}
        ${ISLPY_GENERATION_FLAGS}
)

nanobind_add_module(
    _isl
    NB_STATIC # Build static libnanobind (the extension module itself remains a shared library)
    NOMINSIZE # Optimize for speed, not for size
    LTO       # Enable LTO
    src/wrapper/wrap_isl.cpp
    src/wrapper/wrap_isl_part1.cpp
    src/wrapper/wrap_isl_part2.cpp
    src/wrapper/wrap_isl_part3.cpp
    ${ISL_SOURCES}
    ${ISLPY_GENERATED_SOURCE}
)
target_include_directories(_isl PRIVATE ${CMAKE_BINARY_DIR}/generated)

# Work around https://github.com/inducer/islpy/issues/120.
# See https://stackoverflow.com/questions/43554227/extern-inline-func-results-in-undefined-reference-error
# for some context.
set_source_files_properties(${ISL_SOURCES} PROPERTIES COMPILE_DEFINITIONS __OPTIMIZE_SIZE__)

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

if(USE_SHIPPED_ISL)
    target_compile_definitions(_isl PRIVATE GIT_HEAD_ID="included-with-islpy")
else()
    target_link_directories(_isl PRIVATE ${ISL_LIB_DIRS})
    target_link_libraries(_isl PRIVATE ${ISL_LIB_NAMES})
endif()

install(TARGETS _isl LIBRARY DESTINATION islpy)

if(GENERATE_STUBS)
    set(ISLPY_STUB_FILE ${CMAKE_BINARY_DIR}/_isl.pyi)
    add_custom_command(
        OUTPUT ${ISLPY_STUB_FILE}
        COMMAND ${Python_EXECUTABLE} ${CMAKE_SOURCE_DIR}/stubgen/stubgen.py
            -o ${CMAKE_BINARY_DIR}
            --exec ${CMAKE_SOURCE_DIR}/islpy/_monkeypatch.py
            --python-path ${CMAKE_BINARY_DIR}
            -m _isl
        DEPENDS _isl
    )
    add_custom_target(
        _isl_stub
        ALL DEPENDS ${CMAKE_BINARY_DIR}/_isl.pyi
    )
    install(FILES ${ISLPY_STUB_FILE} DESTINATION islpy)
else()
    if(NOT EXISTS "${CMAKE_SOURCE_DIR}/islpy/_isl.pyi")
        message(FATAL_ERROR "Disabled stub generation requires pregenerated stubs")
    endif()
endif()

# vim: sw=2
