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
        return Map(_pointer=self._map_ptr)


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


class Map(object):
    """ An immutable map of unicode keys to unsigned integer values backed
        by a finite state transducer.

    The map can either be constructed in memory or on disk. For large datasets
    it is recommended to store it on disk, since memory usage will be constant
    due to the file being memory-mapped.

    To build a map, use the :py:meth:`from_iter` classmethod and pass it an
    iterator and (optionally) a path where the map should be stored. If the
    latter is missing, the map will be built in memory.

    In addition to querying the map for single keys, the following operations
    are supported:

    * Range queries with slicing syntax (i.e. `myset['c':'f']` will return an
      iterator over all items in the map whose keys start with 'c', 'd' or 'e')
    * Performing fuzzy searches on the map keys bounded by Levenshtein edit
      distance
    * Performing a search on the map keys with a regular expression
    * Performing set operations on multiple maps, e.g. to find different
      values for common keys

    A few caveats must be kept in mind:

    * Once constructed, a Map can never be modified.
    * Sets must be built with iterators of lexicographically sorted
      (str/unicode, int) tuples, where the integer value must be positive.
    """

    @staticmethod
    @contextmanager
    def build(fpath=None):
        """ Context manager to build a new map.

        Call :py:meth:`insert` on the returned builder object to insert
        new items into the mapp. Keep in mind that insertion must happen in
        lexicographical order, otherwise an exception will be thrown.

        :param path:    Path to build mapp in, or `None` if set should be built
                        in memory
        :returns:       :py:class:`MapBuilder`
        """
        if fpath:
            builder = FileMapBuilder(fpath)
        else:
            builder = MemMapBuilder()
        yield builder
        builder.finish()

    @classmethod
    def from_iter(cls, it, fpath=None):
        """ Build a new map from an iterator.

        Keep in mind that the iterator must return lexicographically sorted
        (key, value) pairs, where the keys are unicode strings and the values
        unsigned integers.

        :param it:      Iterator to build map with
        :type it:       iterator over (str/unicode, int) pairs, where int >= 0
        :param path:    Path to build map in, or `None` if set should be built
                        in memory
        :returns:       The finished map
        :rtype:         :py:class:`Map`
        """
        if isinstance(it, dict):
            it = sorted(it.items(), key=lambda x: x[0])
        with cls.build(fpath) as builder:
            for key, val in it:
                builder.insert(key, val)
        if fpath:
            return cls(path=fpath)
        else:
            return builder.get_map()

    def __init__(self, path=None, _pointer=None):
        """ Load a map from a given file.

        :param path:    Path to map on disk
        """
        self._ctx = ffi.gc(lib.fst_context_new(), lib.fst_context_free)
        if path:
            s = checked_call(lib.fst_map_open, self._ctx,
                             ffi.new("char[]", path.encode('utf8')))
        else:
            s = _pointer
        self._ptr = ffi.gc(s, lib.fst_map_free)

    def __contains__(self, val):
        return lib.fst_map_contains(
            self._ptr, ffi.new("char[]", val.encode('utf8')))

    def __getitem__(self, key):
        """ Get the value for a key or a range of (key, value) pairs.

        If the key is a slice object (e.g. `mymap['a':'f']`) an iterator
        over all matching items in the map will be returned.

        .. important::
            Slicing follows the semantics for numerical indices, i.e. the
            `stop` value is **exclusive**. For example, `mymap['a':'c']` will
            return items whose key begins with 'a' or 'b', but **not** 'c'.

        :param key:     The key to retrieve the value for or a range of
                        unicode strings
        :returns:       The value or an iterator over matching items
        """
        if isinstance(key, slice):
            s = key
            if s.start and s.stop and s.start > s.stop:
                raise ValueError(
                    "Start key must be lexicographically smaller than stop.")
            sb_ptr = lib.fst_map_streambuilder_new(self._ptr)
            if s.start:
                c_start = ffi.new("char[]", s.start.encode('utf8'))
                sb_ptr = lib.fst_map_streambuilder_add_ge(sb_ptr, c_start)
            if s.stop:
                c_stop = ffi.new("char[]", s.stop.encode('utf8'))
                sb_ptr = lib.fst_map_streambuilder_add_lt(sb_ptr, c_stop)
            stream_ptr = lib.fst_map_streambuilder_finish(sb_ptr)
            return MapItemStreamIterator(stream_ptr, lib.fst_mapstream_next,
                                         lib.fst_mapstream_free)
        else:
            return checked_call(lib.fst_map_get, self._ctx, self._ptr,
                                ffi.new("char[]", key.encode('utf8')))

    def __iter__(self):
        return self.keys()

    def __len__(self):
        return int(lib.fst_map_len(self._ptr))

    def keys(self):
        """ Get an iterator over all keys in the map. """
        stream_ptr = lib.fst_map_keys(self._ptr)
        return KeyStreamIterator(stream_ptr, lib.fst_mapkeys_next,
                                 lib.fst_mapkeys_free)

    def values(self):
        """ Get an iterator over all values in the map. """
        stream_ptr = lib.fst_map_values(self._ptr)
        return ValueStreamIterator(stream_ptr, lib.fst_mapvalues_next,
                                   lib.fst_mapvalues_free, ctx_ptr=self._ctx)

    def items(self):
        """ Get an iterator over all (key, value) pairs in the map. """
        stream_ptr = lib.fst_map_stream(self._ptr)
        return MapItemStreamIterator(stream_ptr, lib.fst_mapstream_next,
                                     lib.fst_mapstream_free)

    def search_re(self, pattern):
        """ Search the map with a regular expression.

        Note that the regular expression syntax is not Python's, but the one
        supported by the `regex` Rust crate, which is almost identical
        to the engine of the RE2 engine.

        For a documentation of the syntax, see:
        http://doc.rust-lang.org/regex/regex/index.html#syntax

        Due to limitations of the underlying FST, only a subset of this syntax
        is supported. Most notably absent are:
            - Lazy quantifiers (r'*?', r'+?')
            - Word boundaries (r'\b')
            - Other zero-width assertions (r'^', r'$')
        For background on these limitations, consult the documentation of
        the Rust crate: http://burntsushi.net/rustdoc/fst/struct.Regex.html

        :param pattern:     A regular expression
        :returns:           An iterator over all items with matching keys in
                            the set
        :rtype:             :py:class:`MapItemStreamIterator`
        """
        re_ptr = checked_call(
            lib.fst_regex_new, self._ctx,
            ffi.new("char[]", pattern.encode('utf8')))
        stream_ptr = lib.fst_map_regexsearch(self._ptr, re_ptr)
        return MapItemStreamIterator(stream_ptr, lib.fst_map_regexstream_next,
                                     lib.fst_map_regexstream_free, re_ptr,
                                     lib.fst_regex_free)

    def search(self, term, max_dist):
        """ Search the map with a Levenshtein automaton.

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
        """ Get an iterator over the items in the union of this map and others.

        The iterator will return pairs of `(key, [IndexedValue])`, where
        the latter is a list of different values for the key in the different
        maps, represented as a tuple of the map index and the value in the
        map.

        :param others:  List of :py:class:`Set` objects
        :returns:       Iterator over all items in all maps in lexicographical
                        order
        """
        return self._make_opbuilder(*others).union()

    def intersection(self, *others):
        """ Get an iterator over the items in the intersection of this map and
            others.

        The iterator will return pairs of `(key, [IndexedValue])`, where
        the latter is a list of different values for the key in the different
        maps, represented as a tuple of the map index and the value in the
        map.

        :param others:  List of :py:class:`Map` objects
        :returns:       Iterator over all items whose key exists in all of the
                        passed maps in lexicographical order
        """
        return self._make_opbuilder(*others).intersection()

    def difference(self, *others):
        """ Get an iterator over the items in the difference of this map and
            others.

        The iterator will return pairs of `(key, [IndexedValue])`, where
        the latter is a list of different values for the key in the different
        maps, represented as a tuple of the map index and the value in the
        map.

        :param others:  List of :py:class:`Map` objects
        :returns:       Iterator over all items whose key exists in this map,
                        but in none of the other maps, in lexicographical order
        """
        return self._make_opbuilder(*others).difference()

    def symmetric_difference(self, *others):
        """ Get an iterator over the items in the symmetric difference of this
            map and others.

        The iterator will return pairs of `(key, [IndexedValue])`, where
        the latter is a list of different values for the key in the different
        maps, represented as a tuple of the map index and the value in the
        map.

        :param others:  List of :py:class:`Mapp` objects
        :returns:       Iterator over all items whose key exists in only one of
                        the maps in lexicographical order
        """
        return self._make_opbuilder(*others).symmetric_difference()
