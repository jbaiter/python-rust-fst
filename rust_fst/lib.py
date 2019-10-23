import os
import re
import sys
from ._native import ffi, lib


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


EXCEPTION_MAP = {
    'std::io::error::Error': OSError,
    'fst::error::Error': FstError,
    'fst::error::Error::Fst': TransducerError,
    'fst_regex::error::Error': RegexError,
    'fst_levenshtein::error::Error': LevenshteinError,
    'fst::error::Error::Io': IoError,
    'py::KeyError': KeyError
}


def checked_call(fn, ctx, *args):
    res = fn(ctx, *args)
    if not ctx.has_error:
        return res
    type_str = ffi.string(ctx.error_type).decode('utf8')
    if ctx.error_display != ffi.NULL:
        msg = ffi.string(ctx.error_display).decode('utf8').replace('\n', ' ')
    else:
        msg = None
    err_type = EXCEPTION_MAP.get(type_str)
    if err_type is FstError:
        if ctx.error_description != ffi.NULL:
            desc_str = ffi.string(ctx.error_description).decode('utf8')
        else:
            desc_str = None
        enum_val = re.match(r'(\w+)\(.*?\)', desc_str, re.DOTALL).group(1)
        err_type = EXCEPTION_MAP.get("{}::{}".format(type_str, enum_val))
        if err_type is None:
            msg = "{}: {}".format(enum_val, msg)
    if err_type is None:
        err_type = FstError
    raise err_type(msg)
