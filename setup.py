#!/usr/bin/env python

__copyright__ = """
Copyright (C) 2011-20 Andreas Kloeckner
"""

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from aksetup_helper import (
        check_pybind11, get_pybind_include,
        get_config, setup, check_git_submodules, Extension,
        PybindBuildExtCommand)


def get_config_schema():
    from aksetup_helper import (ConfigSchema,
            IncludeDir, LibraryDir, Libraries,
            Switch, StringListOption)

    default_cxxflags = [
            # Required for pybind11:
            # https://pybind11.readthedocs.io/en/stable/faq.html#someclass-declared-with-greater-visibility-than-the-type-of-its-field-someclass-member-wattributes
            "-fvisibility=hidden"
            ]

    return ConfigSchema([
        Switch("USE_SHIPPED_ISL", True, "Use included copy of isl"),
        Switch("USE_SHIPPED_IMATH", True, "Use included copy of imath in isl"),
        Switch("USE_GMP", True, "Use gmp in external isl"),
        Switch("USE_BARVINOK", False, "Include wrapper for Barvinok"),
        Switch("USE_IMATH_SIO", False, "When using imath, use small-integer "
            "optimization"),

        IncludeDir("GMP", []),
        LibraryDir("GMP", []),
        Libraries("GMP", ["gmp"]),

        IncludeDir("ISL", []),
        LibraryDir("ISL", []),
        Libraries("ISL", ["isl"]),

        IncludeDir("BARVINOK", []),
        LibraryDir("BARVINOK", []),
        Libraries("BARVINOK", ["barvinok", "polylibgmp"]),

        StringListOption("CXXFLAGS", default_cxxflags,
            help="Any extra C++ compiler options to include"),
        StringListOption("LDFLAGS", [],
            help="Any extra linker options to include"),
        ])


# {{{ awful monkeypatching to build only isl (and not the wrapper) with -O2

class Hooked_compile:  # noqa: N801
    def __init__(self, orig__compile, compiler):
        self.orig__compile = orig__compile
        self.compiler = compiler

    def __call__(self, obj, src, *args, **kwargs):
        compiler = self.compiler
        prev_compiler_so = compiler.compiler_so

        # The C++ wrapper takes an awfully long time to compile
        # with any optimization, on gcc 10 (2020-06-30, AK).
        if src.startswith("src/wrapper"):
            compiler.compiler_so = [opt for opt in compiler.compiler_so
                    if not (
                        opt.startswith("-O")
                        or opt.startswith("-g"))]
        if src.endswith(".c"):
            # Some C compilers (Apple clang IIRC?) really don't like having C++
            # flags passed to them.
            args = args[:2] + (
                    [opt for opt in args[2] if "gnu++" not in opt],) + args[3:]

        try:
            result = self.orig__compile(obj, src, *args, **kwargs)
        finally:
            compiler.compiler_so = prev_compiler_so
        return result


class IslPyBuildExtCommand(PybindBuildExtCommand):
    def __getattribute__(self, name):
        if name == "compiler":
            compiler = PybindBuildExtCommand.__getattribute__(self, name)
            if compiler is not None:
                orig__compile = compiler._compile
                if not isinstance(orig__compile, Hooked_compile):
                    compiler._compile = Hooked_compile(orig__compile, compiler)
            return compiler
        else:
            return PybindBuildExtCommand.__getattribute__(self, name)

# }}}


def main():
    check_pybind11()
    check_git_submodules()

    conf = get_config(get_config_schema(), warn_about_no_config=False)

    CXXFLAGS = conf["CXXFLAGS"]  # noqa: N806

    EXTRA_OBJECTS = []  # noqa: N806
    EXTRA_DEFINES = {}  # noqa: N806

    INCLUDE_DIRS = ["src/wrapper"]  # noqa: N806
    LIBRARY_DIRS = []  # noqa: N806
    LIBRARIES = []  # noqa: N806

    if conf["USE_SHIPPED_ISL"]:
        from glob import glob
        isl_blacklist = [
                "_templ.c",
                "_templ_yaml.c",
                "mp_get",
                "extract_key.c",
                "isl_multi_templ.c",
                "isl_multi_apply_set.c",
                "isl_multi_gist.c",
                "isl_multi_coalesce.c",
                "isl_multi_intersect.c",
                "isl_multi_floor.c",
                "isl_multi_apply_union_set.c",
                "isl_multi_cmp.c",
                "isl_multi_pw_aff_explicit_domain.c",
                "isl_multi_hash.c",
                "isl_multi_dims.c",
                "isl_multi_explicit_domain.c",
                "isl_multi_no_explicit_domain.c",
                "isl_multi_align_set.c",
                "isl_multi_align_union_set.c",
                "isl_multi_union_pw_aff_explicit_domain.c",
                "isl_union_templ.c",
                "isl_union_multi.c",
                "isl_union_eval.c",
                "isl_union_neg.c",
                "isl_union_single.c",
                "isl_pw_hash.c",
                "isl_pw_eval.c",
                "isl_pw_union_opt.c",
                "isl_pw_union_opt.c",
                ]

        for fn in glob("isl/*.c"):
            blacklisted = False
            for bl in isl_blacklist:
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

                if "sioimath" in fn and not conf["USE_IMATH_SIO"]:
                    continue
                if "isl_val_imath" in fn and conf["USE_IMATH_SIO"]:
                    continue

            if "isl_ast_int.c" in fn and conf["USE_SHIPPED_IMATH"]:
                continue

            inf = open(fn, "r", encoding="utf-8")
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
                #"isl/imath_wrap/imath.c",
                #"isl/imath_wrap/imrat.c",
                #"isl/imath_wrap/gmp_compat.c",
                ])
            EXTRA_DEFINES["USE_IMATH_FOR_MP"] = 1
            if conf["USE_IMATH_SIO"]:
                EXTRA_DEFINES["USE_SMALL_INT_OPT"] = 1

                import sys
                if sys.platform in ['linux', 'linux2', 'darwin']:
                    CXXFLAGS.insert(0, "-std=gnu99")

            conf["ISL_INC_DIR"].append("isl/imath")
        else:
            EXTRA_DEFINES["USE_GMP_FOR_MP"] = 1

    else:
        LIBRARY_DIRS.extend(conf["ISL_LIB_DIR"])
        LIBRARIES.extend(conf["ISL_LIBNAME"])

    wrapper_dirs = conf["ISL_INC_DIR"][:]

    # {{{ configure barvinok

    if conf["USE_BARVINOK"]:
        if conf["USE_SHIPPED_ISL"]:
            raise RuntimeError("barvinok wrapper is not compatible with using "
                    "shipped isl")
        if conf["USE_SHIPPED_IMATH"]:
            raise RuntimeError("barvinok wrapper is not compatible with using "
                    "shipped imath")

        INCLUDE_DIRS.extend(conf["BARVINOK_INC_DIR"])
        LIBRARY_DIRS.extend(conf["BARVINOK_LIB_DIR"])
        LIBRARIES.extend(conf["BARVINOK_LIBNAME"])

        wrapper_dirs.extend(conf["BARVINOK_INC_DIR"])

        EXTRA_DEFINES["ISLPY_INCLUDE_BARVINOK"] = 1

    # }}}

    INCLUDE_DIRS.extend(conf["ISL_INC_DIR"])

    if not (conf["USE_SHIPPED_ISL"] and conf["USE_SHIPPED_IMATH"]) and \
            conf["USE_GMP"]:
        INCLUDE_DIRS.extend(conf["GMP_INC_DIR"])
        LIBRARY_DIRS.extend(conf["GMP_LIB_DIR"])
        LIBRARIES.extend(conf["GMP_LIBNAME"])

    init_filename = "islpy/version.py"
    with open(init_filename, "r") as version_f:
        version_py = version_f.read()
    exec(compile(version_py, init_filename, "exec"), conf)

    from gen_wrap import gen_wrapper
    gen_wrapper(wrapper_dirs, include_barvinok=conf["USE_BARVINOK"])

    with open("README.rst", "rt") as readme_f:
        readme = readme_f.read()

    setup(name="islpy",
          version=conf["VERSION_TEXT"],
          description="Wrapper around isl, an integer set library",
          long_description=readme,
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
              'Programming Language :: Python :: 3',
              'Topic :: Multimedia :: Graphics :: 3D Modeling',
              'Topic :: Scientific/Engineering',
              'Topic :: Scientific/Engineering :: Mathematics',
              'Topic :: Scientific/Engineering :: Physics',
              'Topic :: Scientific/Engineering :: Visualization',
              'Topic :: Software Development :: Libraries',
              ],

          packages=["islpy"],

          python_requires="~=3.6",
            setup_requires=[
                "pybind11",
                ],
          install_requires=[
              "pytest>=2",
              # "Mako>=0.3.6",
              "six",
              ],
          ext_modules=[
              Extension(
                  "islpy._isl",
                  [
                      "src/wrapper/wrap_isl.cpp",
                      "src/wrapper/wrap_isl_part1.cpp",
                      "src/wrapper/wrap_isl_part2.cpp",
                      "src/wrapper/wrap_isl_part3.cpp",
                      ] + EXTRA_OBJECTS,
                  include_dirs=INCLUDE_DIRS + [
                      get_pybind_include(),
                      get_pybind_include(user=True)
                      ],
                  library_dirs=LIBRARY_DIRS,
                  libraries=LIBRARIES,
                  define_macros=list(EXTRA_DEFINES.items()),
                  extra_compile_args=CXXFLAGS,
                  extra_link_args=conf["LDFLAGS"],
                  ),
              ],
          cmdclass={'build_ext': IslPyBuildExtCommand},
          )


if __name__ == '__main__':
    main()
