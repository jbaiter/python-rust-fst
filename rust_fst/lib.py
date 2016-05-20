import os
import sys
from ._ffi import ffi


def find_library():
    libname = "libfstwrapper"
    if sys.platform == 'win32':
        suffix = 'dll'
    elif sys.platform == 'darwin':
        suffix = 'dylib'
    else:
        suffix = 'so'
    cur_dir = os.path.dirname(__file__)
    build_types = ["release", "debug"]
    return os.path.join(cur_dir, "{}.{}".format(libname, suffix))


lib = ffi.dlopen(find_library())
