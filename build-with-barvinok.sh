#! /bin/bash

set -e
set -x

BUILD_DIR=$(mktemp -d -t islpy-barvinok-build-XXXXXXX)
echo "BUILDING IN $BUILD_DIR"

PREFIX="$HOME/pack/barvinok"
NTL_VER="10.5.0"
BARVINOK_GIT_REV="barvinok-0.41"
NPROCS=30

if true; then
  rm -Rf "$PREFIX" "$BUILD_DIR"

  mkdir "$BUILD_DIR"
  cd "$BUILD_DIR"

  curl -O http://shoup.net/ntl/ntl-"$NTL_VER".tar.gz
  tar xfz ntl-"$NTL_VER".tar.gz
  cd "$BUILD_DIR/ntl-$NTL_VER/src"
  ./configure NTL_GMP_LIP=on PREFIX="$PREFIX" TUNE=x86 SHARED=on
  make -j$NPROCS
  make install

  cd "$BUILD_DIR"
  rm -Rf  barvinok
  git clone git://repo.or.cz/barvinok.git
  cd barvinok
  git checkout $BARVINOK_GIT_REV
  ./get_submodules.sh
  sh autogen.sh
  ./configure --prefix="$PREFIX" --with-ntl-prefix="$PREFIX" --enable-shared-barvinok --with-pet=bundled

  make -j$NPROCS
  make install
fi

cd "$BUILD_DIR"
rm -Rf  islpy
git clone --recursive https://github.com/inducer/islpy
cd islpy
./configure.py \
  --no-use-shipped-isl \
  --no-use-shipped-imath \
  --isl-inc-dir=$PREFIX/include \
  --isl-lib-dir=$PREFIX/lib \
  --use-barvinok
CC=g++ LDSHARED="g++ -shared" python setup.py install
