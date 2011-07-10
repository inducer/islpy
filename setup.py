#!/usr/bin/env python

def get_config_schema():
    from aksetup_helper import ConfigSchema, Option, \
            IncludeDir, LibraryDir, Libraries, BoostLibraries, \
            Switch, StringListOption, make_boost_base_options

    return ConfigSchema(make_boost_base_options() + [
        BoostLibraries("python"),

        IncludeDir("ISL", []),
        LibraryDir("ISL", []),
        Libraries("ISL", ["isl"]),

        StringListOption("CXXFLAGS", [], 
            help="Any extra C++ compiler options to include"),
        StringListOption("LDFLAGS", [], 
            help="Any extra linker options to include"),
        ])




def main():
    from aksetup_helper import hack_distutils, \
            get_config, setup, Extension

    hack_distutils()
    conf = get_config(get_config_schema())

    INCLUDE_DIRS = conf["BOOST_INC_DIR"] + ["src/wrapper"]
    LIBRARY_DIRS = conf["BOOST_LIB_DIR"]
    LIBRARIES = conf["BOOST_PYTHON_LIBNAME"]

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
          version=conf["version_text"],
          description="Wrapper around isl, an integer set library",
          author="Andreas Kloeckner",
          author_email="inform@tiker.net",
          license = "MIT for the wrapper/LGPL for isl",
          url="http://pypi.python.org/pypi/islpy",
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
              # "Mako>=0.3.6",
              ],
          ext_modules = [
            Extension(
              "islpy._isl", 
              ["src/wrapper/wrap_isl.cpp"],
              include_dirs=INCLUDE_DIRS + conf["ISL_INC_DIR"],
              library_dirs=LIBRARY_DIRS + conf["ISL_LIB_DIR"],
              libraries=LIBRARIES + conf["ISL_LIBNAME"],
              #define_macros=[('BOOST_PYTHON_NO_PY_SIGNATURES', '1')],
              extra_compile_args=conf["CXXFLAGS"],
              extra_link_args=conf["LDFLAGS"],
              ),
            ],

          # 2to3 invocation
          cmdclass={'build_py': build_py},
          )




if __name__ == '__main__':
    main()
