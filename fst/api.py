import sys
import weakref

from contextlib import contextmanager

from cffi import FFI

ffi = FFI()
ffi.cdef("""
    char* get_string();
    void free_string(char*);
    char* reverse(char*);
    void cleanup(char*);

    typedef struct FileSetBuilder_S FileSetBuilder;
    typedef struct BufWriter_S BufWriter;
    typedef struct Set_S Set;
    typedef struct Stream_S Stream;
    typedef struct Levenshtein_S Levenshtein;
    typedef struct LevStream_S LevStream;

    BufWriter* bufwriter_new(char*);
    FileSetBuilder* fst_setbuilder_new(BufWriter*);
    void fst_setbuilder_insert(FileSetBuilder*, char*);
    void fst_setbuilder_finish(FileSetBuilder*);

    Set* fst_set_open(char*);
    bool fst_set_contains(Set*, char*);

    Stream* fst_set_stream(Set*);
    LevStream* fst_set_search(Set*, Levenshtein*);
    char* fst_stream_next(Stream*);
    char* lev_stream_next(LevStream*);

    Levenshtein* levenshtein_new(char*, uint32_t);
""")
C = ffi.dlopen("target/debug/libplayground.so")
weak_keys = weakref.WeakKeyDictionary()


class CString:
    def __init__(self, c_ptr):
        self._ptr = c_ptr

    def __str__(self):
        return ffi.string(self._ptr).decode('utf8')

    def __repr__(self):
        return "'{}'".format(str(self))


class SetBuilder:
    def __init__(self, builder_p):
        self._ptr = builder_p

    def insert(self, val):
        c_str = ffi.new("char[]", val.encode('utf8'))
        C.fst_setbuilder_insert(self._ptr, c_str)


class FstSet:
    def __init__(self, path):
        self._ptr = C.fst_set_open(ffi.new("char[]", path.encode('utf8')))

    def __contains__(self, val):
        return C.fst_set_contains(self._ptr,
                                  ffi.new("char[]", val.encode('utf8')))

    def __iter__(self):
        stream_ptr = C.fst_set_stream(self._ptr)
        while True:
            c_str = C.fst_stream_next(stream_ptr)
            if c_str == ffi.NULL:
                break
            yield CString(c_str)

    def search(self, term, max_dist):
        lev_ptr = C.levenshtein_new(ffi.new("char[]", term.encode('utf8')),
                                    max_dist)
        stream_ptr = C.fst_set_search(self._ptr, lev_ptr)
        while True:
            c_str = C.lev_stream_next(stream_ptr)
            if c_str == ffi.NULL:
                break
            yield CString(c_str)


@contextmanager
def create_fst_set(fpath):
    writer_p = C.bufwriter_new(fpath.encode('utf8'))
    builder_p = C.fst_setbuilder_new(writer_p)
    yield SetBuilder(builder_p)
    C.fst_setbuilder_finish(builder_p)
