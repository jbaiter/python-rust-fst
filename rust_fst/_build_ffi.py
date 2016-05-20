from cffi import FFI

ffi = FFI()
ffi.set_source('rust_fst._ffi', None)
ffi.cdef("""
    void string_free(char*);

    typedef struct FileSetBuilder_S FileSetBuilder;
    typedef struct BufWriter_S BufWriter;
    typedef struct Set_S Set;
    typedef struct Stream_S Stream;
    typedef struct Levenshtein_S Levenshtein;
    typedef struct LevStream_S LevStream;

    BufWriter* bufwriter_new(char*);
    void bufwriter_free(BufWriter*);

    FileSetBuilder* fst_setbuilder_new(BufWriter*);
    void fst_setbuilder_insert(FileSetBuilder*, char*);
    void fst_setbuilder_finish(FileSetBuilder*);

    Set* fst_set_open(char*);
    bool fst_set_contains(Set*, char*);
    Stream* fst_set_stream(Set*);
    LevStream* fst_set_search(Set*, Levenshtein*);
    void fst_set_free(Set*);

    char* fst_stream_next(Stream*);
    void fst_stream_free(Stream*);

    char* lev_stream_next(LevStream*);
    void lev_stream_free(LevStream*);

    Levenshtein* levenshtein_new(char*, uint32_t);
    void levenshtein_free(Levenshtein*);
""")

if __name__ == '__main__':
    ffi.compile()
