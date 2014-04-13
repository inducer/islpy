#! /bin/bash

set -e
set -x

cc -E -Iisl/include -Iisl-supplementary \
  -imacros isl/include/isl/list.h \
  -imacros isl/include/isl/multi.h \
  -o isl_declaration_macros_expanded.h \
  isl_declaration_macros.h

sed -i s/__islpy_/__isl_/g isl_declaration_macros_expanded.h 
