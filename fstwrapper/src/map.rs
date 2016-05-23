extern crate libc;

use std::error::Error;
use std::fs::File;
use std::io;
use std::ptr;
use fst::{IntoStreamer, Streamer, Levenshtein, Map, MapBuilder};
use fst::map;

use util::{Context, str_to_cstr, cstr_to_str, to_raw_ptr};


#[allow(dead_code)]
pub struct MapItem {
    key: *const libc::c_char,
    value: libc::uint64_t,
}


pub type FileMapBuilder = MapBuilder<&'static mut io::BufWriter<File>>;
pub type MemMapBuilder = MapBuilder<Vec<u8>>;
pub type MapLevStream = map::Stream<'static, &'static Levenshtein>;


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
    ctx.has_error = false;
    match ref_from_ptr!(ptr).get(key) {
        Some(val) => val,
        None => {
            let msg = str_to_cstr(&format!("Key '{}' not in map.", key));
            ctx.has_error = true;
            ctx.error_type = str_to_cstr("KeyError");
            ctx.error_debug = msg;
            ctx.error_display = msg;
            ctx.error_description = msg;
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
    ctx.has_error = false;
    match mutref_from_ptr!(ptr).next() {
        Some(val) => val,
        None => {
            let msg = str_to_cstr("No more values.");
            ctx.has_error = true;
            ctx.error_type = str_to_cstr("StopIteration");
            ctx.error_debug = msg;
            ctx.error_display = msg;
            ctx.error_description = msg;
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
