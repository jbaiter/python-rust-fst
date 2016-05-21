import os
import re
import sys
from ._ffi import ffi

class FstError(Exception):
    pass

class TransducerError(FstError):
    pass

class RegexError(FstError):
    pass

class LevenshteinError(FstError):
    pass

class IoError(FstError):
    pass


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

EXCEPTION_MAP = {
    'std::io::Error': OSError,
    'fst::Error': FstError,
    'fst::Error::Fst': TransducerError,
    'fst::Error::Regex': RegexError,
    'fst::Error::Levenshtein': LevenshteinError,
    'fst::Error::Io': IoError,
}


def checked_call(fn, ctx, *args):
    res = fn(ctx, *args)
    if not ctx.has_error:
        return res
    msg = ffi.string(ctx.error_display).decode('utf8').replace('\n', ' ')
    type_str = ffi.string(ctx.error_type).decode('utf8')
    err_type = EXCEPTION_MAP.get(type_str)
    if err_type is FstError:
        desc_str = ffi.string(ctx.error_description).decode('utf8')
        enum_val = re.match(r'(\w+)\(.*?\)', desc_str, re.DOTALL).group(1)
        err_type = EXCEPTION_MAP.get("{}::{}".format(type_str, enum_val))
        if err_type is None:
            msg = "{}: {}".format(enum_val, msg)
    if err_type is None:
        err_type = FstError
    raise err_type(msg)
