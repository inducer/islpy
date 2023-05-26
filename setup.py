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

import sys
from typing import List, Sequence

# Needed for aksetup to be found
sys.path.extend(["."])


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
        Switch("USE_IMATH_SIO", True, "When using imath, use small-integer "
            "optimization"),

        IncludeDir("GMP", []),
        LibraryDir("GMP", []),
        Libraries("GMP", ["gmp"]),

        IncludeDir("ISL", ["/usr/include"]),
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


def _get_isl_sources(use_shipped_imath: bool, use_imath_sio: bool) -> Sequence[str]:
    extra_objects: List[str] = []

    from glob import glob
    isl_blocklist = [
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
            "isl_type_check_match_range_multi_val.c",
            ]

    for fn in glob("isl/*.c"):
        blocklisted = False
        for bl in isl_blocklist:
            if bl in fn:
                blocklisted = True
                break

        if "no_piplib" in fn:
            pass
        elif "piplib" in fn:
            blocklisted = True

        if "gmp" in fn:
            if use_shipped_imath:
                continue
        if "imath" in fn:
            if not use_shipped_imath:
                continue

            if "sioimath" in fn and not use_imath_sio:
                continue
            if "isl_val_imath" in fn and use_imath_sio:
                continue

        if "isl_ast_int.c" in fn and use_shipped_imath:
            continue

        inf = open(fn, encoding="utf-8")
        try:
            contents = inf.read()
        finally:
            inf.close()

        if "int main(" not in contents and not blocklisted:
            extra_objects.append(fn)

    if use_shipped_imath:
        extra_objects.extend([
            "isl/imath/imath.c",
            "isl/imath/imrat.c",
            "isl/imath/gmp_compat.c",
            #"isl/imath_wrap/imath.c",
            #"isl/imath_wrap/imrat.c",
            #"isl/imath_wrap/gmp_compat.c",
            ])

    return extra_objects


def main():
    from skbuild import setup
    import nanobind  # noqa: F401
    from setuptools import find_packages

    # {{{ import aksetup_helper bits

    prev_path = sys.path[:]
    # FIXME skbuild seems to remove this. Why?
    sys.path.append(".")

    from aksetup_helper import get_config, check_git_submodules
    from gen_wrap import gen_wrapper

    sys.path = prev_path

    # }}}

    check_git_submodules()

    conf = get_config(get_config_schema(), warn_about_no_config=False)

    cmake_args = []

    INCLUDE_DIRS = ["src/wrapper"]  # noqa: N806
    LIBRARY_DIRS = []  # noqa: N806
    LIBRARIES = []  # noqa: N806

    LIBRARY_DIRS.extend(conf["ISL_LIB_DIR"])
    LIBRARIES.extend(conf["ISL_LIBNAME"])

    INCLUDE_DIRS.extend(conf["ISL_INC_DIR"])

    if not (conf["USE_SHIPPED_ISL"] and conf["USE_SHIPPED_IMATH"]) and \
            conf["USE_GMP"]:
        INCLUDE_DIRS.extend(conf["GMP_INC_DIR"])
        LIBRARY_DIRS.extend(conf["GMP_LIB_DIR"])
        LIBRARIES.extend(conf["GMP_LIBNAME"])

    init_filename = "islpy/version.py"
    with open(init_filename) as version_f:
        version_py = version_f.read()
    exec(compile(version_py, init_filename, "exec"), conf)

    with open("README.rst") as readme_f:
        readme = readme_f.read()

    if conf["USE_SHIPPED_ISL"]:
        cmake_args.append("-DUSE_SHIPPED_ISL:bool=1")
        isl_inc_dirs = ["isl-supplementary", "isl/include",  "isl"]

        if conf["USE_SHIPPED_IMATH"]:
            cmake_args.append("-DUSE_IMATH_FOR_MP:bool=1")
            if conf["USE_IMATH_SIO"]:
                cmake_args.append("-DUSE_IMATH_SIO:bool=1")

            isl_inc_dirs.append("isl/imath")
        else:
            cmake_args.append("-DUSE_GMP_FOR_MP:bool=1")

        extra_objects = _get_isl_sources(
                use_shipped_imath=conf["USE_SHIPPED_IMATH"],
                use_imath_sio=conf["USE_IMATH_SIO"])

        cmake_args.append(f"-DISL_INC_DIRS:LIST={';'.join(isl_inc_dirs)}")

        cmake_args.append(f"-DISL_SOURCES:list={';'.join(extra_objects)}")
    else:
        if conf["ISL_INC_DIR"]:
            cmake_args.append(f"-DISL_INC_DIRS:LIST="
                    f"{';'.join(conf['ISL_INC_DIR'])}")

        if conf["ISL_LIB_DIR"]:
            cmake_args.append(f"-DISL_LIB_DIRS:LIST="
                    f"{';'.join(conf['ISL_LIB_DIR'])}")

        cmake_args.append(f"-DISL_LIB_NAMES={';'.join(conf['ISL_LIBNAME'])}")

        cmake_args.append('-DISL_SOURCES:list=')

        isl_inc_dirs = conf["ISL_INC_DIR"]

    if conf["USE_BARVINOK"]:
        if conf["USE_SHIPPED_ISL"]:
            raise RuntimeError("barvinok wrapper is not compatible with using "
                    "shipped isl")
        if conf["USE_SHIPPED_IMATH"]:
            raise RuntimeError("barvinok wrapper is not compatible with using "
                    "shipped imath")

        cmake_args.append("-DUSE_BARVINOK:bool=1")
        cmake_args.append(
                f"-DBARVINOK_INC_DIRS:LIST={';'.join(conf['BARVINOK_INC_DIR'])}")
        cmake_args.append(
                f"-DBARVINOK_LIB_DIRS:LIST={';'.join(conf['BARVINOK_LIB_DIR'])}")
        cmake_args.append(
                f"-DBARVINOK_LIB_NAMES:LIST={';'.join(conf['BARVINOK_LIBNAME'])}")

        isl_inc_dirs.extend(conf["BARVINOK_INC_DIR"])

    if conf["CXXFLAGS"]:
        cmake_args.append(f"-DCMAKE_CXX_FLAGS:STRING="
                f"{' '.join(conf['CXXFLAGS'])}")

    gen_wrapper(isl_inc_dirs, include_barvinok=conf["USE_BARVINOK"])

    setup(name="islpy",
          version=conf["VERSION_TEXT"],
          description="Wrapper around isl, an integer set library",
          long_description=readme,
          author="Andreas Kloeckner",
          author_email="inform@tiker.net",
          license="MIT",
          url="http://documen.tician.de/islpy",
          classifiers=[
              "Development Status :: 4 - Beta",
              "Intended Audience :: Developers",
              "Intended Audience :: Other Audience",
              "Intended Audience :: Science/Research",
              "License :: OSI Approved :: MIT License",
              "Natural Language :: English",
              "Programming Language :: C++",
              "Programming Language :: Python",
              "Programming Language :: Python :: 3",
              "Topic :: Multimedia :: Graphics :: 3D Modeling",
              "Topic :: Scientific/Engineering",
              "Topic :: Scientific/Engineering :: Mathematics",
              "Topic :: Scientific/Engineering :: Physics",
              "Topic :: Scientific/Engineering :: Visualization",
              "Topic :: Software Development :: Libraries",
              ],

          packages=find_packages(),

          python_requires="~=3.8",
          extras_require={
              "test": ["pytest>=2"],
              },
          cmake_args=cmake_args,
          cmake_install_dir="islpy",
          )


if __name__ == "__main__":
    main()
