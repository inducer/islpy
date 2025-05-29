#! /bin/bash

set -e
set -x

BUILD_DIR=$(mktemp -d -t islpy-barvinok-build-XXXXXXX)
echo "BUILDING IN $BUILD_DIR"

if test "$1" = ""; then
  echo "usage: $0 PREFIX_DIR [GMP_PREFIX_DIR]"
fi
PREFIX="$1"
GMP_PREFIX="${2:-$PREFIX}"
NTL_VER="10.5.0"
BARVINOK_GIT_REV="barvinok-0.41.8"
NPROCS=6
ISLPY_SOURCE="$(pwd)"

function with_echo()
{
  echo "$@"
  "$@"
}

if true; then
  rm -Rf "$BUILD_DIR"

  mkdir "$BUILD_DIR"
  cd "$BUILD_DIR"

  rm -Rf  islpy
  git clone "$ISLPY_SOURCE" --no-local

  curl -L -O --insecure http://shoup.net/ntl/ntl-"$NTL_VER".tar.gz
  tar xfz ntl-"$NTL_VER".tar.gz
  cd "$BUILD_DIR/ntl-$NTL_VER/src"
  ./configure NTL_GMP_LIP=on DEF_PREFIX="$PREFIX" GMP_PREFIX="$GMP_PREFIX" TUNE=x86 SHARED=on
  make -j$NPROCS
  make install

  cd "$BUILD_DIR"
  rm -Rf  barvinok
  git clone https://github.com/inducer/barvinok.git
  cd barvinok
  git checkout $BARVINOK_GIT_REV

  numtries=1
  while ! ./get_submodules.sh; do
    sleep 5
    numtries=$((numtries+1))
    if test "$numtries" == 5; then
      echo "*** getting barvinok submodules failed even after a few tries"
      exit 1
    fi
  done

  sh autogen.sh
  ./configure \
    --prefix="$PREFIX" \
    --with-ntl-prefix="$PREFIX" \
    --with-gmp-prefix="$GMP_PREFIX" \
    --enable-shared-barvinok \
    --with-pet=no

  BARVINOK_ADDITIONAL_MAKE_ARGS=""
  if [ "$(uname)" == "Darwin" ]; then
    BARVINOK_ADDITIONAL_MAKE_ARGS=CFLAGS="-Wno-error=implicit-function-declaration"
  fi
  make $BARVINOK_ADDITIONAL_MAKE_ARGS -j$NPROCS
  make install
fi

cd "$BUILD_DIR"
cd islpy
export LD_LIBRARY_PATH="$PREFIX/lib:$LD_LIBRARY_PATH"
python -m pip install . \
    --config-settings=cmake.define.USE_SHIPPED_ISL=OFF \
    --config-settings=cmake.define.USE_SHIPPED_IMATH=OFF \
    --config-settings=cmake.define.USE_BARVINOK=ON \
    --config-settings=cmake.define.ISL_INC_DIRS:LIST="$PREFIX/include " \
    --config-settings=cmake.define.ISL_LIB_DIRS:LIST="$PREFIX/lib"

# vim: sw=2
