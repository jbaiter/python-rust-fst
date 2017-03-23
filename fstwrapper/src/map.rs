extern crate libc;

use std::error::Error;
use std::fs::File;
use std::io;
use std::ptr;
use fst::{IntoStreamer, Streamer, Levenshtein, Regex, Map, MapBuilder};
use fst::map;
use fst::raw;

use util::{Context, str_to_cstr, cstr_to_str, to_raw_ptr};


#[repr(C)]
#[derive(Debug)]
#[allow(dead_code)]
pub struct MapItem {
    key: *const libc::c_char,
    value: libc::uint64_t,
}

#[repr(C)]
#[derive(Debug)]
#[allow(dead_code)]
pub struct MapOpItem {
    key: *const libc::c_char,
    num_values: libc::size_t,
    values: *const raw::IndexedValue
}


pub type FileMapBuilder = MapBuilder<&'static mut io::BufWriter<File>>;
pub type MemMapBuilder = MapBuilder<Vec<u8>>;
pub type MapLevStream = map::Stream<'static, &'static Levenshtein>;
pub type MapRegexStream = map::Stream<'static, &'static Regex>;


#[no_mangle]
pub extern "C" fn fst_filemapbuilder_new(ctx: *mut Context,
                                         wtr_ptr: *mut io::BufWriter<File>)
                                         -> *mut FileMapBuilder {
    let wtr = mutref_from_ptr!(wtr_ptr);
    to_raw_ptr(with_context!(ctx, ptr::null_mut(),
                             MapBuilder::new(wtr)))
}

#[no_mangle]
pub extern "C" fn fst_filemapbuilder_insert(ctx: *mut Context,
                                            ptr: *mut FileMapBuilder,
                                            key: *mut libc::c_char,
                                            val: libc::uint64_t)
                                            -> bool {
    let builder = mutref_from_ptr!(ptr);
    with_context!(ctx, false, builder.insert(cstr_to_str(key), val));
    true
}

#[no_mangle]
pub extern "C" fn fst_filemapbuilder_finish(ctx: *mut Context, ptr: *mut FileMapBuilder) -> bool {
    let builder = val_from_ptr!(ptr);
    with_context!(ctx, false, builder.finish());
    true
}

#[no_mangle]
pub extern "C" fn fst_memmapbuilder_new() -> *mut MemMapBuilder {
    to_raw_ptr(MapBuilder::memory())
}

#[no_mangle]
pub extern "C" fn fst_memmapbuilder_insert(ctx: *mut Context,
                                           ptr: *mut MemMapBuilder,
                                           key: *mut libc::c_char,
                                           val: libc::uint64_t)
                                           -> bool {
    let builder = mutref_from_ptr!(ptr);
    with_context!(ctx, false, builder.insert(cstr_to_str(key), val));
    true
}

#[no_mangle]
pub extern "C" fn fst_memmapbuilder_finish(ctx: *mut Context, ptr: *mut MemMapBuilder) -> *mut Map {
    let builder = val_from_ptr!(ptr);
    let data = with_context!(ctx, ptr::null_mut(), builder.into_inner());
    let map = with_context!(ctx, ptr::null_mut(), Map::from_bytes(data));
    to_raw_ptr(map)
}

#[no_mangle]
pub extern "C" fn fst_map_open(ctx: *mut Context, path: *mut libc::c_char) -> *mut Map {
    let path = cstr_to_str(path);
    let map = with_context!(ctx, ptr::null_mut(), Map::from_path(path));
    to_raw_ptr(map)
}
make_free_fn!(fst_map_free, *mut Map);

#[no_mangle]
pub extern "C" fn fst_map_len(ptr: *mut Map) -> libc::size_t {
    ref_from_ptr!(ptr).len()
}

#[no_mangle]
pub extern "C" fn fst_map_contains(ptr: *mut Map, key: *mut libc::c_char) -> bool {
    ref_from_ptr!(ptr).contains_key(cstr_to_str(key))
}

#[no_mangle]
pub extern "C" fn fst_map_stream(ptr: *mut Map) -> *mut map::Stream<'static> {
    to_raw_ptr(ref_from_ptr!(ptr).stream())
}
make_free_fn!(fst_mapstream_free, *mut map::Stream);
map_make_next_fn!(fst_mapstream_next, *mut map::Stream);
make_free_fn!(fst_mapitem_free, *mut MapItem);

#[no_mangle]
pub extern "C" fn fst_map_get(ctx: *mut Context,
                              ptr: *mut Map,
                              key: *mut libc::c_char)
                              -> libc::uint64_t {
    let key = cstr_to_str(key);
    let ctx = mutref_from_ptr!(ctx);
    ctx.clear();
    match ref_from_ptr!(ptr).get(key) {
        Some(val) => val,
        None => {
            let msg = str_to_cstr(&format!("Key '{}' not in map.", key));
            ctx.has_error = true;
            ctx.error_type = str_to_cstr("py::KeyError");
            ctx.error_display = msg;
            return 0;
        }
    }
}

#[no_mangle]
pub extern "C" fn fst_map_keys(ptr: *mut Map) -> *mut map::Keys<'static> {
    to_raw_ptr(ref_from_ptr!(ptr).keys())
}
make_free_fn!(fst_mapkeys_free, *mut map::Keys);
set_make_next_fn!(fst_mapkeys_next, *mut map::Keys);

#[no_mangle]
pub extern "C" fn fst_map_values(ptr: *mut Map) -> *mut map::Values<'static> {
    to_raw_ptr(ref_from_ptr!(ptr).values())
}
make_free_fn!(fst_mapvalues_free, *mut map::Values);

#[no_mangle]
pub extern "C" fn fst_mapvalues_next(ctx: *mut Context, ptr: *mut map::Values) -> libc::uint64_t {
    let ctx = mutref_from_ptr!(ctx);
    ctx.clear();
    match mutref_from_ptr!(ptr).next() {
        Some(val) => val,
        None => {
            let msg = str_to_cstr("No more values.");
            ctx.has_error = true;
            ctx.error_type = str_to_cstr("StopIteration");
            ctx.error_display = msg;
            return 0;
        }
    }
}

#[no_mangle]
pub extern "C" fn fst_map_levsearch(map_ptr: *mut Map,
                                    lev_ptr: *mut Levenshtein)
                                    -> *mut MapLevStream {
    let map = mutref_from_ptr!(map_ptr);
    let lev = ref_from_ptr!(lev_ptr);
    to_raw_ptr(map.search(lev).into_stream())
}
make_free_fn!(fst_map_levstream_free, *mut MapLevStream);
map_make_next_fn!(fst_map_levstream_next, *mut MapLevStream);


#[no_mangle]
pub extern "C" fn fst_map_regexsearch(map_ptr: *mut Map, regex_ptr: *mut Regex)
                                      -> *mut MapRegexStream {
    let map = mutref_from_ptr!(map_ptr);
    let regex = ref_from_ptr!(regex_ptr);
    to_raw_ptr(map.search(regex).into_stream())
}
make_free_fn!(fst_map_regexstream_free, *mut MapRegexStream);
map_make_next_fn!(fst_map_regexstream_next, *mut MapRegexStream);


#[no_mangle]
pub extern "C" fn fst_map_make_opbuilder(ptr: *mut Map) -> *mut map::OpBuilder<'static> {
    let map = ref_from_ptr!(ptr);
    let ob = map.op();
    to_raw_ptr(ob)
}
make_free_fn!(fst_map_opbuilder_free, *mut map::OpBuilder);
make_free_fn!(fst_map_opitem_free, *mut MapOpItem);

#[no_mangle]
pub extern "C" fn fst_map_opbuilder_push(ptr: *mut map::OpBuilder, map_ptr: *mut Map) {
    let map = ref_from_ptr!(map_ptr);
    let ob = mutref_from_ptr!(ptr);
    ob.push(map);
}

#[no_mangle]
pub extern "C" fn fst_map_opbuilder_union(ptr: *mut map::OpBuilder)
                                          -> *mut map::Union {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.union())
}
make_free_fn!(fst_map_union_free, *mut map::Union);
mapop_make_next_fn!(fst_map_union_next, *mut map::Union);

#[no_mangle]
pub extern "C" fn fst_map_opbuilder_intersection(ptr: *mut map::OpBuilder)
                                                 -> *mut map::Intersection {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.intersection())
}
make_free_fn!(fst_map_intersection_free, *mut map::Intersection);
mapop_make_next_fn!(fst_map_intersection_next, *mut map::Intersection);

#[no_mangle]
pub extern "C" fn fst_map_opbuilder_difference(ptr: *mut map::OpBuilder)
                                               -> *mut map::Difference {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.difference())
}
make_free_fn!(fst_map_difference_free, *mut map::Difference);
mapop_make_next_fn!(fst_map_difference_next, *mut map::Difference);

#[no_mangle]
pub extern "C" fn fst_map_opbuilder_symmetricdifference
    (ptr: *mut map::OpBuilder)
     -> *mut map::SymmetricDifference {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.symmetric_difference())
}
make_free_fn!(fst_map_symmetricdifference_free, *mut map::SymmetricDifference);
mapop_make_next_fn!(fst_map_symmetricdifference_next, *mut map::SymmetricDifference);


#[no_mangle]
pub extern "C" fn fst_map_streambuilder_new(ptr: *mut Map) -> *mut map::StreamBuilder<'static> {
    let map = ref_from_ptr!(ptr);
    to_raw_ptr(map.range())
}

#[no_mangle]
pub extern "C" fn fst_map_streambuilder_add_ge(ptr: *mut map::StreamBuilder<'static>,
                                               c_bound: *mut libc::c_char)
                                               -> *mut map::StreamBuilder<'static> {
    let sb = val_from_ptr!(ptr);
    to_raw_ptr(sb.ge(cstr_to_str(c_bound)))
}

#[no_mangle]
pub extern "C" fn fst_map_streambuilder_add_lt(ptr: *mut map::StreamBuilder<'static>,
                                               c_bound: *mut libc::c_char)
                                               -> *mut map::StreamBuilder<'static> {
    let sb = val_from_ptr!(ptr);
    to_raw_ptr(sb.lt(cstr_to_str(c_bound)))
}

#[no_mangle]
pub extern "C" fn fst_map_streambuilder_finish(ptr: *mut map::StreamBuilder<'static>)
                                               -> *mut map::Stream {
    let sb = val_from_ptr!(ptr);
    to_raw_ptr(sb.into_stream())
}
