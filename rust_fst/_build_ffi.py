from cffi import FFI

ffi = FFI()
ffi.set_source('rust_fst._ffi', None)
ffi.cdef("""
    typedef struct {
        bool  has_error;
        char* error_type;
        char* error_description;
        char* error_display;
        char* error_debug;
    } Context;

    typedef struct FileSetBuilder_S FileSetBuilder;
    typedef struct BufWriter_S BufWriter;
    typedef struct Set_S Set;
    typedef struct Stream_S Stream;
    typedef struct Levenshtein_S Levenshtein;
    typedef struct LevStream_S LevStream;

    Context* context_new();
    void context_free(Context*);

    void string_free(char*);

    BufWriter* bufwriter_new(Context*, char*);
    void bufwriter_free(BufWriter*);

    FileSetBuilder* fst_setbuilder_new(Context*, BufWriter*);
    void fst_setbuilder_insert(Context*, FileSetBuilder*, char*);
    void fst_setbuilder_finish(Context*, FileSetBuilder*);

    Set* fst_set_open(Context*, char*);
    bool fst_set_contains(Set*, char*);
    size_t fst_set_len(Set*);
    bool fst_set_isdisjoint(Set*, Set*);
    bool fst_set_issubset(Set*, Set*);
    bool fst_set_issuperset(Set*, Set*);
    Stream* fst_set_stream(Set*);
    LevStream* fst_set_levsearch(Set*, Levenshtein*);
    void fst_set_free(Set*);

    char* fst_setstream_next(Stream*);
    void fst_setstream_free(Stream*);

    char* fst_levstream_next(LevStream*);
    void fst_levstream_free(LevStream*);

    Levenshtein* fst_levenshtein_new(Context*, char*, uint32_t);
    void fst_levenshtein_free(Levenshtein*);
""")

if __name__ == '__main__':
    ffi.compile()
