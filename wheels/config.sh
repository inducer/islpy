function pre_build {
    set -x

    pushd isl
      echo "isl license" >> ../doc/misc.rst
      cat LICENSE >> ../doc/misc.rst
      echo "imath license" >> ../doc/misc.rst
      echo "=============" >> ../doc/misc.rst
      head -n 25 imath/imath.h  >> ../doc/misc.rst
    popd
}

function run_tests {
    # Runs tests on installed distribution from an empty directory
    python --version
    python -c "import islpy"
}

function pip_wheel_cmd {
    local abs_wheelhouse=$1
    rm -rf siteconf.py
    python configure.py --no-use-shipped-isl --isl-inc-dir=$BUILD_PREFIX/include --isl-lib-dir=$BUILD_PREFIX/lib
    pip wheel $(pip_opts) -w $abs_wheelhouse --no-deps .
}

