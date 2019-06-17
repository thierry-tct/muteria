#! /bin/bash

set -e

topdir=$(dirname $(readlink -f $0))
prog=main

fail=0
$topdir/$prog 1 2 | grep 'The result is: 3' > /dev/null || fail=1

exit $fail