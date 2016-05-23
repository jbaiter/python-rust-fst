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
    libname = "fstwrapper"
    if sys.platform == 'win32':
        prefix = ''
        suffix = 'dll'
    elif sys.platform == 'darwin':
        prefix = 'lib'
        suffix = 'dylib'
    else:
        prefix = 'lib'
        suffix = 'so'
    cur_dir = os.path.dirname(__file__)
    return os.path.join(cur_dir, "{}{}.{}".format(prefix, libname, suffix))


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


def make_stream_iter(stream_ptr, next_fn, free_fn):
    while True:
        c_str = next_fn(stream_ptr)
        if c_str == ffi.NULL:
            break
        yield ffi.string(c_str).decode('utf8')
        lib.fst_string_free(c_str)
    free_fn(stream_ptr)
