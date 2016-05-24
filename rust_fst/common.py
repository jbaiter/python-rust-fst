from collections import namedtuple

from .lib import ffi, lib


class StreamIterator(object):
    def __init__(self, stream_ptr, next_fn, free_fn, autom_ptr=None,
                 autom_free_fn=None, ctx_ptr=None):
        self._ptr = stream_ptr
        self._next_fn = next_fn
        self._free_fn = free_fn
        self._autom_ptr = autom_ptr
        self._autom_free_fn = autom_free_fn
        self._ctx = ctx_ptr

    def _free(self):
        self._free_fn(self._ptr)
        if self._autom_ptr:
            self._autom_free_fn(self._autom_ptr)

    def __iter__(self):
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        raise NotImplementedError


class KeyStreamIterator(StreamIterator):
    def __next__(self):
        c_str = self._next_fn(self._ptr)
        if c_str == ffi.NULL:
            self._free()
            raise StopIteration
        py_str = ffi.string(c_str).decode('utf8')
        lib.fst_string_free(c_str)
        return py_str


class ValueStreamIterator(StreamIterator):
    def __next__(self):
        val = self._next_fn(self._ctx, self._ptr)
        if val == 0 and self._ctx.has_error:
            self._free()
            raise StopIteration
        return val


class MapItemStreamIterator(StreamIterator):
    def __next__(self):
        itm = self._next_fn(self._ptr)
        if itm == ffi.NULL:
            self._free()
            raise StopIteration
        key = ffi.string(itm.key).decode('utf8')
        value = itm.value
        lib.fst_string_free(itm.key)
        lib.fst_mapitem_free(itm)
        return (key, value)
