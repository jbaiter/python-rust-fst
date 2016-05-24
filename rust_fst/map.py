from contextlib import contextmanager

from .common import (KeyStreamIterator, ValueStreamIterator,
                     MapItemStreamIterator, MapOpItemStreamIterator)
from .lib import ffi, lib, checked_call


class MapBuilder(object):
    def insert(self, val):
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError


class FileMapBuilder(MapBuilder):
    def __init__(self, fpath):
        self._ctx = lib.fst_context_new()
        self._writer_p = checked_call(
            lib.fst_bufwriter_new, self._ctx, fpath.encode('utf8'))
        self._builder_p = checked_call(
            lib.fst_filemapbuilder_new, self._ctx, self._writer_p)

    def insert(self, key, val):
        c_key = ffi.new("char[]", key.encode('utf8'))
        checked_call(lib.fst_filemapbuilder_insert,
                     self._ctx, self._builder_p, c_key, val)

    def finish(self):
        checked_call(lib.fst_filemapbuilder_finish,
                     self._ctx, self._builder_p)
        lib.fst_bufwriter_free(self._writer_p)
        lib.fst_context_free(self._ctx)


class MemMapBuilder(MapBuilder):
    def __init__(self):
        self._ctx = lib.fst_context_new()
        self._ptr = lib.fst_memmapbuilder_new()
        self._map_ptr = None

    def insert(self, key, val):
        c_key = ffi.new("char[]", key.encode('utf8'))
        checked_call(lib.fst_memmapbuilder_insert, self._ctx, self._ptr,
                     c_key, val)

    def finish(self):
        self._map_ptr = checked_call(lib.fst_memmapbuilder_finish,
                                     self._ctx, self._ptr)
        lib.fst_context_free(self._ctx)
        self._ctx = None
        self._ptr = None

    def get_map(self):
        if self._map_ptr is None:
            raise ValueError("The builder has to be finished first.")
        return FstMap(pointer=self._map_ptr)


class OpBuilder(object):
    def __init__(self, map_ptr):
        # NOTE: No need for `ffi.gc`, since the struct will be free'd
        #       once we call union/intersection/difference
        self._ptr = lib.fst_map_make_opbuilder(map_ptr)

    def push(self, map_ptr):
        lib.fst_map_opbuilder_push(self._ptr, map_ptr)

    def union(self):
        stream_ptr = lib.fst_map_opbuilder_union(self._ptr)
        return MapOpItemStreamIterator(
                stream_ptr, lib.fst_map_union_next, lib.fst_map_union_free)

    def intersection(self):
        stream_ptr = lib.fst_map_opbuilder_intersection(self._ptr)
        return MapOpItemStreamIterator(
                stream_ptr, lib.fst_map_intersection_next,
                lib.fst_map_intersection_free)

    def difference(self):
        stream_ptr = lib.fst_map_opbuilder_difference(self._ptr)
        return MapOpItemStreamIterator(
            stream_ptr, lib.fst_map_difference_next,
            lib.fst_map_difference_free)

    def symmetric_difference(self):
        stream_ptr = lib.fst_map_opbuilder_symmetricdifference(self._ptr)
        return MapOpItemStreamIterator(
            stream_ptr, lib.fst_map_symmetricdifference_next,
            lib.fst_map_symmetricdifference_free)


class FstMap(object):
    @staticmethod
    @contextmanager
    def build(fpath=None):
        """ Context manager to build a new FST map in a given file.

        Keys must be inserted in lexicographical order.

        See http://burntsushi.net/rustdoc/fst/struct.MapBuilder.html for more
        details.
        """
        if fpath:
            builder = FileMapBuilder(fpath)
        else:
            builder = MemMapBuilder()
        yield builder
        builder.finish()

    @classmethod
    def from_iter(cls, it, fpath=None):
        if isinstance(it, dict):
            it = sorted(it.items(), key=lambda x: x[0])
        with cls.build(fpath) as builder:
            for key, val in it:
                builder.insert(key, val)
        if fpath:
            return cls(path=fpath)
        else:
            return builder.get_map()

    def __init__(self, path=None, pointer=None):
        """ Load an FST map from a given file. """
        self._ctx = ffi.gc(lib.fst_context_new(), lib.fst_context_free)
        if path:
            s = checked_call(lib.fst_map_open, self._ctx,
                             ffi.new("char[]", path.encode('utf8')))
        else:
            s = pointer
        self._ptr = ffi.gc(s, lib.fst_map_free)

    def __contains__(self, val):
        return lib.fst_map_contains(
            self._ptr, ffi.new("char[]", val.encode('utf8')))

    def __getitem__(self, key):
        return checked_call(lib.fst_map_get, self._ctx, self._ptr,
                            ffi.new("char[]", key.encode('utf8')))

    def __iter__(self):
        return self.keys()

    def __len__(self):
        return int(lib.fst_map_len(self._ptr))

    def keys(self):
        stream_ptr = lib.fst_map_keys(self._ptr)
        return KeyStreamIterator(stream_ptr, lib.fst_mapkeys_next,
                                 lib.fst_mapkeys_free)

    def values(self):
        stream_ptr = lib.fst_map_values(self._ptr)
        return ValueStreamIterator(stream_ptr, lib.fst_mapvalues_next,
                                   lib.fst_mapvalues_free, ctx_ptr=self._ctx)

    def items(self):
        stream_ptr = lib.fst_map_stream(self._ptr)
        return MapItemStreamIterator(stream_ptr, lib.fst_mapstream_next,
                                     lib.fst_mapstream_free)

    def search(self, term, max_dist):
        """ Search the map keys with a Levenshtein automaton.

        :param term:        The search term
        :param max_dist:    The maximum edit distance for search results
        :returns:           Matching (key, value) items in the map
        :rtype:             :py:class:`MapItemStreamIterator`
        """
        lev_ptr = checked_call(
            lib.fst_levenshtein_new, self._ctx,
            ffi.new("char[]", term.encode('utf8')), max_dist)
        stream_ptr = lib.fst_map_levsearch(self._ptr, lev_ptr)
        return MapItemStreamIterator(stream_ptr, lib.fst_map_levstream_next,
                                     lib.fst_map_levstream_free, lev_ptr,
                                     lib.fst_levenshtein_free)

    def _make_opbuilder(self, *others):
        opbuilder = OpBuilder(self._ptr)
        for oth in others:
            opbuilder.push(oth._ptr)
        return opbuilder

    def union(self, *others):
        return self._make_opbuilder(*others).union()

    def intersection(self, *others):
        return self._make_opbuilder(*others).intersection()

    def difference(self, *others):
        return self._make_opbuilder(*others).difference()

    def symmetric_difference(self, *others):
        return self._make_opbuilder(*others).symmetric_difference()
