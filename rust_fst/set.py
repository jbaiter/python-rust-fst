from contextlib import contextmanager

from .lib import ffi, lib, checked_call


class SetBuilder:
    def __init__(self, ctx, ptr):
        self._ctx = ctx
        self._ptr = ptr

    def insert(self, val):
        c_str = ffi.new("char[]", val.encode('utf8'))
        checked_call(lib.fst_setbuilder_insert, self._ctx, self._ptr, c_str)


class FstSet:
    """ An immutable set backed by a finite state transducer stored on disk.

    The interface tries to follow the `frozenset` type as much as possible.
    """
    @staticmethod
    @contextmanager
    def build(fpath):
        """ Context manager to build a new FST set in a given file.

        Keys must be inserted in lexicographical order.

        See http://burntsushi.net/rustdoc/fst/struct.SetBuilder.html for more
        details.
        """
        ctx = lib.context_new();
        writer_p = checked_call(lib.bufwriter_new, ctx, fpath.encode('utf8'))
        builder_p = checked_call(lib.fst_setbuilder_new, ctx, writer_p)
        yield SetBuilder(ctx, builder_p)
        checked_call(lib.fst_setbuilder_finish, ctx, builder_p)
        lib.bufwriter_free(writer_p)
        lib.context_free(ctx)

    def __init__(self, path):
        """ Load an FST set from a given file. """
        self._ctx = ffi.gc(lib.context_new(), lib.context_free)
        s = checked_call(lib.fst_set_open, ctx,
                         ffi.new("char[]", path.encode('utf8')))
        self._ptr = ffi.gc(s, lib.fst_set_free)

    def __contains__(self, val):
        return lib.fst_set_contains(
            self._ptr, ffi.new("char[]", val.encode('utf8')))

    def __iter__(self):
        stream_ptr = lib.fst_set_stream(self._ptr)
        while True:
            c_str = lib.fst_stream_next(stream_ptr)
            if c_str == ffi.NULL:
                break
            yield ffi.string(c_str).decode('utf8')
            lib.string_free(c_str)
        lib.fst_stream_free(stream_ptr)

    def __len__(self):
        return lib.fst_set_len(self._ptr)

    def union(self, *others):
        # TODO
        raise NotImplementedError

    def intersection(self, *others):
        # TODO
        raise NotImplementedError

    def difference(self, *others):
        # TODO
        raise NotImplementedError

    def symmetric_difference(self, *others):
        # TODO
        raise NotImplementedError

    def issubset(self, other):
        return bool(lib.fst_set_issubset(self._ptr, other._ptr))

    def issuperset(self, other):
        return bool(lib.fst_set_issuperset(self._ptr, other._ptr))

    def isdisjoint(self, other):
        return bool(lib.fst_set_isdisjoint(self._ptr, other._ptr))

    def search(self, term, max_dist):
        """ Search the set with a Levenshtein automaton.

        :param term:        The search term
        :param max_dist:    The maximum edit distance for search results
        :returns:           Matching values in the set
        :rtype:             generator that yields str
        """
        lev_ptr = checked_call(
            self._ctx,
            lib.levenshtein_new(ffi.new("char[]", term.encode('utf8')),
                                max_dist))
        stream_ptr = lib.fst_set_search(self._ptr, lev_ptr)
        while True:
            c_str = lib.lev_stream_next(stream_ptr)
            if c_str == ffi.NULL:
                break
            yield ffi.string(c_str).decode('utf8')
            lib.string_free(c_str)
        lib.lev_stream_free(stream_ptr)
        lib.levenshtein_free(lev_ptr)
