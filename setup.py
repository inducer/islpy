#!/usr/bin/env python


def get_config_schema():
    from aksetup_helper import ConfigSchema, \
            IncludeDir, LibraryDir, Libraries, BoostLibraries, \
            Switch, StringListOption, make_boost_base_options

    return ConfigSchema(make_boost_base_options() + [
        BoostLibraries("python"),

        Switch("USE_SHIPPED_BOOST", True, "Use included Boost library"),
        Switch("USE_SHIPPED_ISL", True, "Use included copy of isl"),
        Switch("USE_SHIPPED_IMATH", True, "Use included copy of imath in isl"),

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
    from aksetup_helper import (hack_distutils,
            get_config, setup, Extension,
            set_up_shipped_boost_if_requested,
            check_git_submodules)

    check_git_submodules()

    hack_distutils(what_opt=None)
    conf = get_config(get_config_schema(), warn_about_no_config=False)

    EXTRA_OBJECTS, EXTRA_DEFINES = set_up_shipped_boost_if_requested("islpy", conf)

    INCLUDE_DIRS = conf["BOOST_INC_DIR"] + ["src/wrapper"]
    LIBRARY_DIRS = conf["BOOST_LIB_DIR"]
    LIBRARIES = conf["BOOST_PYTHON_LIBNAME"]

    if conf["USE_SHIPPED_ISL"]:
        from glob import glob
        ISL_BLACKLIST = ["_templ.c", "mp_get"]

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

            if "gmp" in fn:
                if conf["USE_SHIPPED_IMATH"]:
                    continue
            if "imath" in fn:
                if not conf["USE_SHIPPED_IMATH"]:
                    continue
            if "isl_ast_int.c" in fn and conf["USE_SHIPPED_IMATH"]:
                continue

            inf = open(fn, "rt")
            try:
                contents = inf.read()
            finally:
                inf.close()

            if "int main(" not in contents and not blacklisted:
                EXTRA_OBJECTS.append(fn)

        conf["ISL_INC_DIR"] = ["isl-supplementary", "isl/include",  "isl"]

        if conf["USE_SHIPPED_IMATH"]:
            EXTRA_OBJECTS.extend([
                "isl/imath/imath.c",
                "isl/imath/imrat.c",
                "isl/imath/gmp_compat.c",
                ])
            EXTRA_DEFINES["USE_IMATH_FOR_MP"] = 1

            conf["ISL_INC_DIR"].append("isl/imath")
        else:
            EXTRA_DEFINES["USE_GMP_FOR_MP"] = 1

    else:
        LIBRARY_DIRS.extend(conf["ISL_LIB_DIR"])
        LIBRARIES.extend(conf["ISL_LIBNAME"])

    INCLUDE_DIRS.extend(conf["ISL_INC_DIR"])

    if not (conf["USE_SHIPPED_ISL"] and conf["USE_SHIPPED_IMATH"]):
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
          long_description=open("README.rst", "rt").read(),
          author="Andreas Kloeckner",
          author_email="inform@tiker.net",
          license="MIT",
          url="http://documen.tician.de/islpy",
          classifiers=[
              'Development Status :: 4 - Beta',
              'Intended Audience :: Developers',
              'Intended Audience :: Other Audience',
              'Intended Audience :: Science/Research',
              'License :: OSI Approved :: MIT License',
              'Natural Language :: English',
              'Programming Language :: C++',
              'Programming Language :: Python',
              'Programming Language :: Python :: 2.5',
              'Programming Language :: Python :: 2.6',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3',
              'Programming Language :: Python :: 3.2',
              'Programming Language :: Python :: 3.3',
              'Topic :: Multimedia :: Graphics :: 3D Modeling',
              'Topic :: Scientific/Engineering',
              'Topic :: Scientific/Engineering :: Mathematics',
              'Topic :: Scientific/Engineering :: Physics',
              'Topic :: Scientific/Engineering :: Visualization',
              'Topic :: Software Development :: Libraries',
              ],

          packages=["islpy"],

          install_requires=[
              "pytest>=2",
              # "Mako>=0.3.6",
              ],
          ext_modules=[
              Extension(
                  "islpy._isl",
                  EXTRA_OBJECTS + [
                      "src/wrapper/wrap_isl.cpp",
                      "src/wrapper/wrap_isl_part1.cpp",
                      "src/wrapper/wrap_isl_part2.cpp",
                      "src/wrapper/wrap_isl_part3.cpp",
                      ],
                  include_dirs=INCLUDE_DIRS,
                  library_dirs=LIBRARY_DIRS,
                  libraries=LIBRARIES,
                  define_macros=list(EXTRA_DEFINES.items()),
                  extra_compile_args=conf["CXXFLAGS"],
                  extra_link_args=conf["LDFLAGS"],
                  ),
              ],

          # 2to3 invocation
          cmdclass={'build_py': build_py},
          )


if __name__ == '__main__':
    main()
