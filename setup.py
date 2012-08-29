#!/usr/bin/env python

def get_config_schema():
    from aksetup_helper import ConfigSchema, \
            IncludeDir, LibraryDir, Libraries, BoostLibraries, \
            Switch, StringListOption, make_boost_base_options

    return ConfigSchema(make_boost_base_options() + [
        BoostLibraries("python"),

        Switch("USE_SHIPPED_BOOST", True, "Use included Boost library"),
        Switch("USE_SHIPPED_ISL", True, "Use included copy of isl"),
        Switch("ISL_USE_PYTHON_INTEGERS", False, "Allows isl not to depend on gmp"),

        IncludeDir("GMP", []),
        LibraryDir("GMP", []),
        Libraries("GMP", ["gmp"]),

        IncludeDir("ISL", []),
        LibraryDir("ISL", []),
        Libraries("ISL", ["isl"]),

        StringListOption("CXXFLAGS", [], 
            help="Any extra C++ compiler options to include"),
        StringListOption("LDFLAGS", [], 
            help="Any extra linker options to include"),
        ])




def main():
    from aksetup_helper import (hack_distutils, \
            get_config, setup, Extension,
            set_up_shipped_boost_if_requested,
            check_git_submodules)

    check_git_submodules()

    hack_distutils(what_opt=None)
    conf = get_config(get_config_schema())

    EXTRA_OBJECTS, EXTRA_DEFINES = set_up_shipped_boost_if_requested("islpy", conf)

    INCLUDE_DIRS = conf["BOOST_INC_DIR"] + ["src/wrapper"]
    LIBRARY_DIRS = conf["BOOST_LIB_DIR"]
    LIBRARIES = conf["BOOST_PYTHON_LIBNAME"]
    DEFINES = {}

    if not conf["USE_SHIPPED_ISL"] and conf["ISL_USE_PYTHON_INTEGERS"]:
        raise RuntimeError("Cannot use Python integers with system-wide isl")

    if conf["USE_SHIPPED_ISL"]:
        from glob import glob
        ISL_BLACKLIST = ["_templ.c", "mp_get"]
        ISL_PYINT_BLACKLIST = ["isl_gmp.c", "basis_reduction_tab.c",
                "isl_scan.c", "isl_sample.c", "isl_affine_hull.c"]

        for fn in glob("isl/*.c"):
            blacklisted = False
            for bl in ISL_BLACKLIST:
                if bl in fn:
                    blacklisted = True
                    break

            if "no_piplib" in fn:
                pass
            elif "piplib" in fn:
                blacklisted = True

            if conf["ISL_USE_PYTHON_INTEGERS"]:
                for bl in ISL_PYINT_BLACKLIST:
                    if bl in fn:
                        blacklisted = True
                        break

            inf = open(fn, "rt")
            try:
                contents = inf.read()
            finally:
                inf.close()

            if "int main(" not in contents and not blacklisted:
                EXTRA_OBJECTS.append(fn)

        conf["ISL_INC_DIR"] = ["isl-supplementary", "isl/include",  "isl"]
    else:
        LIBRARY_DIRS.extend(conf["ISL_LIB_DIR"])
        LIBRARIES.extend(conf["ISL_LIBNAME"])

    INCLUDE_DIRS.extend(conf["ISL_INC_DIR"])

    if conf["ISL_USE_PYTHON_INTEGERS"]:
        # must come first, so it can override isl/int.h
        INCLUDE_DIRS = ["isl-py-int"] + INCLUDE_DIRS

        DEFINES["ISL_USE_PYTHON_INTEGERS"] = 1
    else:
        INCLUDE_DIRS.extend(conf["GMP_INC_DIR"])
        LIBRARY_DIRS.extend(conf["GMP_LIB_DIR"])
        LIBRARIES.extend(conf["GMP_LIBNAME"])

    init_filename = "islpy/version.py"
    exec(compile(open(init_filename, "r").read(), init_filename, "exec"), conf)

    try:
        from distutils.command.build_py import build_py_2to3 as build_py
    except ImportError:
        # 2.x
        from distutils.command.build_py import build_py

    from gen_wrap import gen_wrapper
    gen_wrapper(conf["ISL_INC_DIR"])

    setup(name="islpy",
          version=conf["VERSION_TEXT"],
          description="Wrapper around isl, an integer set library",
          long_description="""
                islpy is a Python wrapper around Sven Verdoolaege's `isl
                <http://www.kotnet.org/~skimo/isl/>`_, a library for manipulating sets and
                relations of integer points bounded by linear constraints.

                Supported operations on sets include

                * intersection, union, set difference,
                * emptiness check,
                * convex hull,
                * (integer) affine hull,
                * integer projection,
                * computing the lexicographic minimum using parametric integer programming,
                * coalescing, and
                * parametric vertex enumeration.

                It also includes an ILP solver based on generalized basis reduction, transitive
                closures on maps (which may encode infinite graphs), dependence analysis and
                bounds on piecewise step-polynomials.

                Islpy comes with comprehensive `documentation <http://documen.tician.de/islpy>`_.

                The `GNU Multiprecision Library <http://gmplib.org/>`_ and its
                Python wrapper `gmpy <https://code.google.com/p/gmpy/>`_
                (Version 1.x) may optionally be used.  A version of isl is
                shipped with islpy, but optionally a system-wide one may also
                be used.
                """,
          author="Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "MIT for the wrapper/LGPL for isl",
          url="http://documen.tician.de/islpy",
          classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Intended Audience :: Other Audience',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: MIT License',
            'License :: Free for non-commercial use',
            'Natural Language :: English',
            'Programming Language :: C++',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3',
            'Topic :: Multimedia :: Graphics :: 3D Modeling',
            'Topic :: Scientific/Engineering',
            'Topic :: Scientific/Engineering :: Mathematics',
            'Topic :: Scientific/Engineering :: Physics',
            'Topic :: Scientific/Engineering :: Visualization',
            'Topic :: Software Development :: Libraries',
            ],

          packages = [ "islpy" ],

          install_requires=[
              "pytest>=2",
              ],
          ext_modules = [
            Extension(
              "islpy._isl", 
              [
                  "src/wrapper/wrap_isl.cpp",
                  "src/wrapper/wrap_isl_part1.cpp",
                  "src/wrapper/wrap_isl_part2.cpp",
                  "src/wrapper/wrap_isl_part3.cpp",
                  ] + EXTRA_OBJECTS,
              include_dirs=INCLUDE_DIRS,
              library_dirs=LIBRARY_DIRS,
              libraries=LIBRARIES,
              define_macros=(
                  list(EXTRA_DEFINES.items())
                  +list(DEFINES.items())),
              extra_compile_args=conf["CXXFLAGS"],
              extra_link_args=conf["LDFLAGS"],
              ),
            ],

          # 2to3 invocation
          cmdclass={'build_py': build_py},
          )




if __name__ == '__main__':
    main()
