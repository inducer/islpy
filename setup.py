#!/usr/bin/env python

__copyright__ = "Copyright (C) 2011-15 Andreas Kloeckner"

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

from codecs import open


def get_config_schema():
    from aksetup_helper import (ConfigSchema,
            IncludeDir, LibraryDir, Libraries,
            Switch, StringListOption)

    return ConfigSchema([
        Switch("USE_SHIPPED_ISL", True, "Use included copy of isl"),
        Switch("USE_SHIPPED_IMATH", True, "Use included copy of imath in isl"),
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

        StringListOption("CXXFLAGS", [],
            help="Any extra C++ compiler options to include"),
        StringListOption("LDFLAGS", [],
            help="Any extra linker options to include"),
        ])


CFFI_TEMPLATE = """
from cffi import FFI

EXTRA_DEFINES = {EXTRA_DEFINES}

INCLUDES = '''
{INCLUDES}
'''

ffi = FFI()
ffi.set_source(
    "islpy._isl_cffi",
    INCLUDES,
    define_macros=list(EXTRA_DEFINES.items()),
    sources={EXTRA_SOURCES},
    include_dirs={INCLUDE_DIRS},
    library_dirs={LIBRARY_DIRS},
    libraries={LIBRARIES},
    extra_compile_args={CFLAGS},
    extra_link_args={LDFLAGS})


with open("wrapped-functions.h", "rt") as header_f:
    header = header_f.read()

ffi.cdef(header)

if __name__ == "__main__":
    ffi.compile()
"""


def write_cffi_build_script(headers, **kwargs):
    format_args = dict((k, repr(v)) for k, v in kwargs.items())

    format_args["INCLUDES"] = "\n".join(
            "#include <%s>" % header
            for header in headers)

    with open("islpy_cffi_build.py", "wt") as outf:
        outf.write(CFFI_TEMPLATE.format(**format_args))


def main():
    from aksetup_helper import (hack_distutils,
            get_config, setup, check_git_submodules)

    check_git_submodules()

    hack_distutils(what_opt=None)
    conf = get_config(get_config_schema(), warn_about_no_config=False)

    EXTRA_SOURCES = []  # noqa
    EXTRA_DEFINES = {}  # noqa
    INCLUDE_DIRS = []  # noqa
    LIBRARY_DIRS = []  # noqa
    LIBRARIES = []  # noqa
    CXXFLAGS = conf["CXXFLAGS"]

    if conf["USE_SHIPPED_ISL"]:
        from glob import glob
        isl_blacklist = [
                "_templ.c", "mp_get",
                "isl_multi_templ.c",
                "isl_multi_apply_set.c",
                "isl_multi_gist.c",
                "isl_multi_coalesce.c",
                "isl_multi_intersect.c",
                "isl_multi_floor.c",
                "isl_multi_apply_union_set.c",
                "isl_multi_cmp.c",
                "isl_multi_hash.c",
                "isl_union_templ.c",
                "isl_union_multi.c",
                "isl_union_eval.c",
                "isl_union_neg.c",
                "isl_union_single.c",
                "isl_pw_hash.c",
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
                EXTRA_SOURCES.append(fn)

        conf["ISL_INC_DIR"] = ["isl-supplementary", "isl/include",  "isl"]

        if conf["USE_SHIPPED_IMATH"]:
            EXTRA_SOURCES.extend([
                "isl/imath/imath.c",
                "isl/imath/imrat.c",
                "isl/imath/gmp_compat.c",
                "isl/imath_wrap/imath.c",
                "isl/imath_wrap/imrat.c",
                "isl/imath_wrap/gmp_compat.c",
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

        EXTRA_DEFINES["ISLPY_ISL_VERSION"] = 15

    # }}}

    INCLUDE_DIRS.extend(conf["ISL_INC_DIR"])

    if not (conf["USE_SHIPPED_ISL"] and conf["USE_SHIPPED_IMATH"]):
        INCLUDE_DIRS.extend(conf["GMP_INC_DIR"])
        LIBRARY_DIRS.extend(conf["GMP_LIB_DIR"])
        LIBRARIES.extend(conf["GMP_LIBNAME"])

    init_filename = "islpy/version.py"
    with open(init_filename, "r") as version_f:
        version_py = version_f.read()
    exec(compile(version_py, init_filename, "exec"), conf)

    from gen_wrap import gen_wrapper
    headers = gen_wrapper(wrapper_dirs, include_barvinok=conf["USE_BARVINOK"],
            isl_version=EXTRA_DEFINES.get("ISLPY_ISL_VERSION"))

    write_cffi_build_script(
            headers,
            EXTRA_DEFINES=EXTRA_DEFINES,
            EXTRA_SOURCES=EXTRA_SOURCES,
            INCLUDE_DIRS=INCLUDE_DIRS,
            LIBRARY_DIRS=LIBRARY_DIRS,
            LIBRARIES=LIBRARIES,
            CFLAGS=CXXFLAGS,
            LDFLAGS=conf["LDFLAGS"]
            )

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
              'Programming Language :: Python :: 2.6',
              'Programming Language :: Python :: 2.7',
              'Programming Language :: Python :: 3',
              'Programming Language :: Python :: 3.3',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: Implementation :: CPython',
              'Programming Language :: Python :: Implementation :: PyPy',
              'Topic :: Multimedia :: Graphics :: 3D Modeling',
              'Topic :: Scientific/Engineering',
              'Topic :: Scientific/Engineering :: Mathematics',
              'Topic :: Scientific/Engineering :: Physics',
              'Topic :: Scientific/Engineering :: Visualization',
              'Topic :: Software Development :: Libraries',
              ],

          packages=["islpy"],

          setup_requires=["cffi>=1.1.0"],
          cffi_modules=["islpy_cffi_build.py:ffi"],
          install_requires=[
              "pytest>=2",
              "cffi>=1.1.0",
              # "Mako>=0.3.6",
              "six",
              ],
          )


if __name__ == '__main__':
    main()
