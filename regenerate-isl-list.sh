#! /bin/bash

cc -E -Iisl/include -Iisl-generated isl/include/isl/list.h -o isl_list.h
echo "now chop away the non-list related stuff in isl_list.h, starting vim [Enter]"
read INPUT
vim isl_list.h
