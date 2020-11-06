#!/bin/sh

irname=$2
varname=$1
args=""

/fast/fs/llvm3/build/bin/llc $irname -o out1.o -filetype=obj $args -experimental-debug-variable-locations
if test $? != 0; then
  exit 23
fi

/fast/fs/llvm3/build/bin/llc $irname -o out2.o -filetype=obj $args
if test $? != 0; then
  exit 23
fi

/fast/fs/llvm3/build/bin/llvm-dwarfdump --statistics out1.o > varsfile1
/fast/fs/llvm3/build/bin/llvm-dwarfdump --statistics out2.o > varsfile2

num1=`grep $varname varsfile1 | wc -l`
num2=`grep $varname varsfile2 | wc -l`

rm out1.o
rm out2.o
rm varsfile1
rm varsfile2

if test $num1 != $num2; then
  exit 0
fi

exit 1
