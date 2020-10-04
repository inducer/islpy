function build_simple2 {
    local name=$1
    local version=$2
    local url=$3
    local ext=$4
    shift 4
    if [ -e "${name}-stamp" ]; then
        return
    fi
    local name_version="${name}-${version}"
    local targz=${name_version}.$ext
    fetch_unpack $url/$targz
    (cd $name_version \
        && ((./configure --prefix=$BUILD_PREFIX $*) || (cat config.log && exit 1))  \
        && make \
        && make install)
    touch "${name}-stamp"
    echo "${name} is bundled with this wheel" >> doc/misc.rst
    echo "Source code can be found at: $url/$targz" >> doc/misc.rst
    echo "${name} license" >> doc/misc.rst
    echo "===================" >> doc/misc.rst
}

function pre_build {
    set -x
    export PATH=$PATH:$BUILD_PREFIX/bin
    if [ -n "$IS_OSX" ]; then
        export CC="clang"
        export CXX="clang++"
        export CFLAGS="-arch x86_64"
        export CXXFLAGS="-arch x86_64"
        export LDFLAGS="-arch x86_64"
        export MACOSX_DEPLOYMENT_TARGET="10.9"
    fi
    echo "Bundled dependencies in the wheel" >> doc/misc.rst
    build_simple2 gmp  6.1.2 https://gmplib.org/download/gmp tar.bz2 \
        --enable-shared --disable-static --with-pic --enable-fat
    pushd gmp-6.1.2
      cat README >> ../doc/misc.rst
      cat COPYING.LESSERv3 >> ../doc/misc.rst
      echo "" >> ../doc/misc.rst
    popd
    build_simple2 isl 0.22.1 http://isl.gforge.inria.fr tar.gz  \
        --enable-shared --disable-static --with-int=gmp --with-gmp-prefix=$BUILD_PREFIX
    pushd isl-0.22.1
      cat LICENSE >> ../doc/misc.rst
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

if [ -n "$IS_OSX" ]; then
    function repair_wheelhouse {
        echo "custom repair_wheelhouse for osx"
        local wheelhouse=$1
        check_pip
        $PIP_CMD install delocate
        delocate-listdeps $wheelhouse/*.whl # lists library dependencies
        # repair_wheelhouse can take more than 10 minutes without generating output
        # but jobs that do not generate output within 10 minutes are aborted by travis-ci.
        # Echoing something here solves the problem.
        echo in repair_wheelhouse, executing delocate-wheel
        delocate-wheel $wheelhouse/*.whl # copies library dependencies into wheel

        local wheels=$(python $MULTIBUILD_DIR/supported_wheels.py $wheelhouse/*.whl)
        for wheel in $wheels
        do
            se_file_name=$(basename $wheel)
            se_file_name="${se_file_name/macosx_10_9_intel./macosx_10_9_x86_64.}"
            se_file_name="${se_file_name/macosx_10_6_intel./macosx_10_9_x86_64.}"
            mv $wheel $wheelhouse/$se_file_name
        done
    }
fi
