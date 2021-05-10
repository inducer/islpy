#! /bin/bash

set -e
set -x

BUILD_DIR=$(mktemp -d -t islpy-barvinok-build-XXXXXXX)
echo "BUILDING IN $BUILD_DIR"

if test "$1" = ""; then
  echo "usage: $0 PREFIX_DIR"
fi
PREFIX="$1"
NTL_VER="10.5.0"
BARVINOK_GIT_REV="barvinok-0.41.5"
NPROCS=6

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
  if test "$GITHUB_HEAD_REF" != ""; then
    with_echo git clone --recursive https://github.com/inducer/islpy.git -b "$GITHUB_HEAD_REF"
  elif test "$CI_SERVER_NAME" = "GitLab" && test "$CI_COMMIT_REF_NAME" != ""; then
    with_echo git clone --recursive https://gitlab.tiker.net/inducer/islpy.git -b "$CI_COMMIT_REF_NAME"
  else
    with_echo git clone --recursive https://github.com/inducer/islpy.git
  fi

  curl -L -O --insecure http://shoup.net/ntl/ntl-"$NTL_VER".tar.gz
  tar xfz ntl-"$NTL_VER".tar.gz
  cd "$BUILD_DIR/ntl-$NTL_VER/src"
  ./configure NTL_GMP_LIP=on PREFIX="$PREFIX" TUNE=x86 SHARED=on
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
    --enable-shared-barvinok \
    --with-pet=no

  make -j$NPROCS
  make install
fi

cd "$BUILD_DIR"
cd islpy
./configure.py \
  --no-use-shipped-isl \
  --no-use-shipped-imath \
  --isl-inc-dir=$PREFIX/include \
  --isl-lib-dir=$PREFIX/lib \
  --use-barvinok
CC=g++ LDSHARED="g++ -shared" python setup.py install

# vim: sw=2
