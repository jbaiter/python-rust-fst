extern crate libc;
extern crate fst;


use std::error::Error;
use std::fs::File;
use std::io;
use std::ptr;
use fst::{IntoStreamer, Streamer, Levenshtein, Set, SetBuilder};
use fst::set;

use util::{Context, cstr_to_str, to_raw_ptr};


pub type FileSetBuilder = SetBuilder<&'static mut io::BufWriter<File>>;
pub type MemSetBuilder = SetBuilder<Vec<u8>>;
pub type SetLevStream = set::Stream<'static, &'static Levenshtein>;


#[no_mangle]
pub extern "C" fn fst_filesetbuilder_new(ctx: *mut Context,
                                         wtr_ptr: *mut io::BufWriter<File>)
                                         -> *mut FileSetBuilder {
    let wtr = mutref_from_ptr!(wtr_ptr);
    to_raw_ptr(with_context!(ctx, ptr::null_mut(), SetBuilder::new(wtr)))
}

#[no_mangle]
pub extern "C" fn fst_filesetbuilder_insert(ctx: *mut Context,
                                            ptr: *mut FileSetBuilder,
                                            s: *mut libc::c_char)
                                            -> bool {
    let build = mutref_from_ptr!(ptr);
    with_context!(ctx, false, build.insert(cstr_to_str(s)));
    true
}

#[no_mangle]
pub extern "C" fn fst_filesetbuilder_finish(ctx: *mut Context, ptr: *mut FileSetBuilder) -> bool {
    let build = val_from_ptr!(ptr);
    with_context!(ctx, false, build.finish());
    true
}

#[no_mangle]
pub extern "C" fn fst_memsetbuilder_new() -> *mut MemSetBuilder {
    to_raw_ptr(SetBuilder::memory())
}

#[no_mangle]
pub extern "C" fn fst_memsetbuilder_insert(ctx: *mut Context,
                                           ptr: *mut MemSetBuilder,
                                           s: *mut libc::c_char)
                                           -> bool {
    let build = mutref_from_ptr!(ptr);
    with_context!(ctx, false, build.insert(cstr_to_str(s)));
    true
}

#[no_mangle]
pub extern "C" fn fst_memsetbuilder_finish(ctx: *mut Context, ptr: *mut MemSetBuilder) -> *mut Set {
    let build = val_from_ptr!(ptr);
    let data = with_context!(ctx, ptr::null_mut(), build.into_inner());
    let set = with_context!(ctx, ptr::null_mut(), Set::from_bytes(data));
    to_raw_ptr(set)
}

#[no_mangle]
pub extern "C" fn fst_set_open(ctx: *mut Context, cpath: *mut libc::c_char) -> *mut Set {
    let path = cstr_to_str(cpath);
    let set = with_context!(ctx, ptr::null_mut(), Set::from_path(path));
    to_raw_ptr(set)
}
make_free_fn!(fst_set_free, *mut Set);


#[no_mangle]
pub extern "C" fn fst_set_contains(ptr: *mut Set, s: *mut libc::c_char) -> bool {
    let set = mutref_from_ptr!(ptr);
    set.contains(cstr_to_str(s))
}

#[no_mangle]
pub extern "C" fn fst_set_stream(ptr: *mut Set) -> *mut set::Stream<'static> {
    let set = mutref_from_ptr!(ptr);
    to_raw_ptr(set.stream())
}
make_free_fn!(fst_set_stream_free, *mut set::Stream);
set_make_next_fn!(fst_set_stream_next, *mut set::Stream);

#[no_mangle]
pub extern "C" fn fst_set_len(ptr: *mut Set) -> libc::size_t {
    let set = mutref_from_ptr!(ptr);
    set.len()
}

#[no_mangle]
pub extern "C" fn fst_set_isdisjoint(self_ptr: *mut Set, oth_ptr: *mut Set) -> bool {
    let slf = ref_from_ptr!(self_ptr);
    let oth = ref_from_ptr!(oth_ptr);
    slf.is_disjoint(oth)
}

#[no_mangle]
pub extern "C" fn fst_set_issubset(self_ptr: *mut Set, oth_ptr: *mut Set) -> bool {
    let slf = ref_from_ptr!(self_ptr);
    let oth = ref_from_ptr!(oth_ptr);
    slf.is_subset(oth)
}

#[no_mangle]
pub extern "C" fn fst_set_issuperset(self_ptr: *mut Set, oth_ptr: *mut Set) -> bool {
    let slf = ref_from_ptr!(self_ptr);
    let oth = ref_from_ptr!(oth_ptr);
    slf.is_superset(oth)
}

#[no_mangle]
pub extern "C" fn fst_set_levsearch(set_ptr: *mut Set,
                                    lev_ptr: *mut Levenshtein)
                                    -> *mut SetLevStream {
    let set = mutref_from_ptr!(set_ptr);
    let lev = ref_from_ptr!(lev_ptr);
    to_raw_ptr(set.search(lev).into_stream())
}
make_free_fn!(fst_set_levstream_free, *mut SetLevStream);
set_make_next_fn!(fst_set_levstream_next, *mut SetLevStream);

#[no_mangle]
pub extern "C" fn fst_set_make_opbuilder(ptr: *mut Set) -> *mut set::OpBuilder<'static> {
    let set = ref_from_ptr!(ptr);
    let ob = set.op();
    to_raw_ptr(ob)
}
make_free_fn!(fst_set_opbuilder_free, *mut set::OpBuilder<'static>);

#[no_mangle]
pub extern "C" fn fst_set_opbuilder_push(ptr: *mut set::OpBuilder, set_ptr: *mut Set) {
    let set = ref_from_ptr!(set_ptr);
    let ob = mutref_from_ptr!(ptr);
    ob.push(set);
}

#[no_mangle]
pub extern "C" fn fst_set_opbuilder_union(ptr: *mut set::OpBuilder<'static>)
                                          -> *mut set::Union<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.union())
}
make_free_fn!(fst_set_union_free, *mut set::Union<'static>);
set_make_next_fn!(fst_set_union_next, *mut set::Union<'static>);

#[no_mangle]
pub extern "C" fn fst_set_opbuilder_intersection(ptr: *mut set::OpBuilder<'static>)
                                                 -> *mut set::Intersection<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.intersection())
}
make_free_fn!(fst_set_intersection_free, *mut set::Intersection);
set_make_next_fn!(fst_set_intersection_next, *mut set::Intersection);

#[no_mangle]
pub extern "C" fn fst_set_opbuilder_difference(ptr: *mut set::OpBuilder<'static>)
                                               -> *mut set::Difference<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.difference())
}
make_free_fn!(fst_set_difference_free, *mut set::Difference);
set_make_next_fn!(fst_set_difference_next, *mut set::Difference);

#[no_mangle]
pub extern "C" fn fst_set_opbuilder_symmetricdifference
    (ptr: *mut set::OpBuilder<'static>)
     -> *mut set::SymmetricDifference<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.symmetric_difference())
}
make_free_fn!(fst_set_symmetricdifference_free, *mut set::SymmetricDifference);
set_make_next_fn!(fst_set_symmetricdifference_next, *mut set::SymmetricDifference);
