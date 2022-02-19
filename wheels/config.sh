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
        export ABI=64
    elif [[ "$PLAT" == "x86_64" ]]; then
        export ABI=64
    elif [[ "$PLAT" == "i686" ]]; then
        export ABI=32
    fi
    echo "Bundled dependencies in the wheel" >> doc/misc.rst
    build_simple2 gmp  6.1.2 https://gmplib.org/download/gmp tar.bz2 \
        --enable-shared --disable-static --with-pic --enable-fat
    pushd gmp-6.1.2
      cat README >> ../doc/misc.rst
      cat COPYING.LESSERv3 >> ../doc/misc.rst
      echo "" >> ../doc/misc.rst
    popd
    build_simple2 isl 0.24 https://libisl.sourceforge.io tar.gz \
        --enable-shared --disable-static --with-int=gmp --with-gmp-prefix=$BUILD_PREFIX
    pushd isl-0.24
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

