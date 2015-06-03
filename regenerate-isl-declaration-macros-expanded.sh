#! /bin/bash

set -e
set -x

INCLUDEPATH=isl/include
OUTFILE=isl_declaration_macros_expanded.h
DEFINES="-DISLPY_ISL_VERSION=15"

#INCLUDEPATH=$HOME/pool/include
#OUTFILE=isl_declaration_macros_expanded_v14.h
#DEFINES="-DISLPY_ISL_VERSION=14"

cc -E $DEFINES -I$INCLUDEPATH -Iisl-supplementary \
  -imacros $INCLUDEPATH/isl/list.h \
  -imacros $INCLUDEPATH/isl/multi.h \
  -o $OUTFILE \
  isl_declaration_macros.h

sed -i s/__islpy_/__isl_/g isl_declaration_macros_expanded.h
