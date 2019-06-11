
from __future__ import print_function

import os
import sys
import argparse

import lib.lib as l

def main():
    assert len(sys.argv) == 3, "expect 2 arguments: values a and b"
    a = int(sys.argv[1])
    b = int(sys.argv[2])
    lobj = l.Lib()
    res = lobj.compute(a, b)
    print("The result is:", res)

if __name__ == '__main__':
    main()