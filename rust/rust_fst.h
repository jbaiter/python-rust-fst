/** ===============================
                Utility
    =============================== **/

typedef struct {
    bool  has_error;
    char* error_type;
    char* error_description;
    char* error_display;
    char* error_debug;
} Context;

typedef struct BufWriter BufWriter;
typedef struct Levenshtein Levenshtein;
typedef struct Regex Regex;

Levenshtein* fst_levenshtein_new(Context*, char*, uint32_t);
void fst_levenshtein_free(Levenshtein*);

Regex* fst_regex_new(Context*, char*);
void fst_regex_free(Regex*);

Context* fst_context_new();
void fst_context_free(Context*);

void fst_string_free(char*);

BufWriter* fst_bufwriter_new(Context*, char*);
void fst_bufwriter_free(BufWriter*);


/** ===============================
                    Set
    =============================== **/

typedef struct FileSetBuilder FileSetBuilder;
typedef struct MemSetBuilder MemSetBuilder;
typedef struct Set Set;
typedef struct SetStream SetStream;
typedef struct SetLevStream SetLevStream;
typedef struct SetRegexStream SetRegexStream;
typedef struct SetOpBuilder SetOpBuilder;
typedef struct SetUnion SetUnion;
typedef struct SetIntersection SetIntersection;
typedef struct SetDifference SetDifference;
typedef struct SetSymmetricDifference SetSymmetricDifference;
typedef struct SetStreamBuilder SetStreamBuilder;

FileSetBuilder* fst_filesetbuilder_new(Context*, BufWriter*);
void fst_filesetbuilder_insert(Context*, FileSetBuilder*, char*);
void fst_filesetbuilder_finish(Context*, FileSetBuilder*);

MemSetBuilder* fst_memsetbuilder_new();
bool fst_memsetbuilder_insert(Context*, MemSetBuilder*, char*);
Set* fst_memsetbuilder_finish(Context*, MemSetBuilder*);

Set* fst_set_open(Context*, char*);
bool fst_set_contains(Set*, char*);
size_t fst_set_len(Set*);
bool fst_set_isdisjoint(Set*, Set*);
bool fst_set_issubset(Set*, Set*);
bool fst_set_issuperset(Set*, Set*);
SetStream* fst_set_stream(Set*);
SetLevStream* fst_set_levsearch(Set*, Levenshtein*);
SetRegexStream* fst_set_regexsearch(Set*, Regex*);
SetOpBuilder* fst_set_make_opbuilder(Set*);
SetOpBuilder* fst_set_make_opbuilder_streambuilder(SetStreamBuilder*);
SetOpBuilder* fst_set_make_opbuilder_levstream(SetLevStream*);
SetOpBuilder* fst_set_make_opbuilder_regexstream(SetRegexStream*);
SetOpBuilder* fst_set_make_opbuilder_union(SetUnion*);
void fst_set_free(Set*);

char* fst_set_stream_next(SetStream*);
void fst_set_stream_free(SetStream*);

char* fst_set_levstream_next(SetLevStream*);
void fst_set_levstream_free(SetLevStream*);

char* fst_set_regexstream_next(SetRegexStream*);
void fst_set_regexstream_free(SetRegexStream*);

void fst_set_opbuilder_push(SetOpBuilder*, Set*);
void fst_set_opbuilder_push_levstream(SetOpBuilder*, SetLevStream*);
void fst_set_opbuilder_push_regexstream(SetOpBuilder*, SetRegexStream*);
void fst_set_opbuilder_push_streambuilder(SetOpBuilder*, SetStreamBuilder*);
void fst_set_opbuilder_push_union(SetOpBuilder*, SetUnion*);
void fst_set_opbuilder_free(SetOpBuilder*);
SetUnion* fst_set_opbuilder_union(SetOpBuilder*);
SetIntersection* fst_set_opbuilder_intersection(SetOpBuilder*);
SetDifference* fst_set_opbuilder_difference(SetOpBuilder*);
SetSymmetricDifference* fst_set_opbuilder_symmetricdifference(
    SetOpBuilder*);

char* fst_set_union_next(SetUnion*);
void fst_set_union_free(SetUnion*);

char* fst_set_intersection_next(SetIntersection*);
void fst_set_intersection_free(SetIntersection*);

char* fst_set_difference_next(SetDifference*);
void fst_set_difference_free(SetDifference*);

char* fst_set_symmetricdifference_next(SetSymmetricDifference*);
void fst_set_symmetricdifference_free(SetSymmetricDifference*);

SetStreamBuilder* fst_set_streambuilder_new(Set*);
SetStreamBuilder* fst_set_streambuilder_add_ge(SetStreamBuilder*, char*);
SetStreamBuilder* fst_set_streambuilder_add_gt(SetStreamBuilder*, char*);
SetStreamBuilder* fst_set_streambuilder_add_le(SetStreamBuilder*, char*);
SetStreamBuilder* fst_set_streambuilder_add_lt(SetStreamBuilder*, char*);
SetStream* fst_set_streambuilder_finish(SetStreamBuilder*);


/** ===============================
                    Map
    =============================== **/

typedef struct {
    char*       key;
    uint64_t    value;
} MapItem;

typedef struct {
    size_t      index;
    uint64_t    value;
} IndexedValue;

typedef struct {
    char*           key;
    size_t          num_values;
    IndexedValue*   values;
} MapOpItem;


typedef struct FileMapBuilder FileMapBuilder;
typedef struct MemMapBuilder MemMapBuilder;
typedef struct Map Map;
typedef struct MapStream MapStream;
typedef struct MapLevStream MapLevStream;
typedef struct MapRegexStream MapRegexStream;
typedef struct MapKeyStream MapKeyStream;
typedef struct MapValueStream MapValueStream;
typedef struct MapOpBuilder MapOpBuilder;
typedef struct MapUnion MapUnion;
typedef struct MapIntersection MapIntersection;
typedef struct MapDifference MapDifference;
typedef struct MapSymmetricDifference MapSymmetricDifference;
typedef struct MapStreamBuilder MapStreamBuilder;

FileMapBuilder* fst_filemapbuilder_new(Context*, BufWriter*);
bool fst_filemapbuilder_insert(Context*, FileMapBuilder*, char*, uint64_t);
bool fst_filemapbuilder_finish(Context*, FileMapBuilder*);

MemMapBuilder* fst_memmapbuilder_new();
bool fst_memmapbuilder_insert(Context*, MemMapBuilder*, char*, uint64_t);
Map* fst_memmapbuilder_finish(Context*, MemMapBuilder*);

Map* fst_map_open(Context*, char*);
void fst_map_free(Map*);
uint64_t fst_map_get(Context*, Map*, char*);
size_t fst_map_len(Map*);
bool fst_map_contains(Map*, char*);
MapStream* fst_map_stream(Map*);
MapKeyStream* fst_map_keys(Map*);
MapValueStream* fst_map_values(Map*);
MapLevStream* fst_map_levsearch(Map*, Levenshtein*);
MapRegexStream* fst_map_regexsearch(Map*, Regex*);
MapOpBuilder* fst_map_make_opbuilder(Map*);

MapItem* fst_mapstream_next(MapStream*);
void fst_mapstream_free(MapStream*);
void fst_mapitem_free(MapItem*);

char* fst_mapkeys_next(MapKeyStream*);
void fst_mapkeys_free(MapKeyStream*);

uint64_t fst_mapvalues_next(Context*, MapValueStream*);
void fst_mapvalues_free(MapValueStream*);

MapItem* fst_map_levstream_next(MapLevStream*);
void fst_map_levstream_free(MapLevStream*);

MapItem* fst_map_regexstream_next(MapRegexStream*);
void fst_map_regexstream_free(MapRegexStream*);

void fst_map_opbuilder_push(MapOpBuilder*, Map*);
void fst_map_opbuilder_free(MapOpBuilder*);
MapUnion* fst_map_opbuilder_union(MapOpBuilder*);
MapIntersection* fst_map_opbuilder_intersection(MapOpBuilder*);
MapDifference* fst_map_opbuilder_difference(MapOpBuilder*);
MapSymmetricDifference* fst_map_opbuilder_symmetricdifference(
    MapOpBuilder*);
void fst_map_opitem_free(MapOpItem*);

MapOpItem* fst_map_union_next(MapUnion*);
void fst_map_union_free(MapUnion*);

MapOpItem* fst_map_intersection_next(MapIntersection*);
void fst_map_intersection_free(MapIntersection*);

MapOpItem* fst_map_difference_next(MapDifference*);
void fst_map_difference_free(MapDifference*);

MapOpItem* fst_map_symmetricdifference_next(MapSymmetricDifference*);
void fst_map_symmetricdifference_free(MapSymmetricDifference*);

MapStreamBuilder* fst_map_streambuilder_new(Map*);
MapStreamBuilder* fst_map_streambuilder_add_ge(MapStreamBuilder*, char*);
MapStreamBuilder* fst_map_streambuilder_add_lt(MapStreamBuilder*, char*);
MapStream* fst_map_streambuilder_finish(MapStreamBuilder*);
