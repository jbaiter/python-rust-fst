#![crate_type = "dylib"]
#![feature(core_intrinsics)]

extern crate libc;
extern crate fst;

use std::error::Error;
use std::ffi::{CStr,CString};
use std::fs::File;
use std::intrinsics;
use std::io;
use std::ptr;
use fst::{IntoStreamer, Streamer, Levenshtein, Set, SetBuilder};
use fst::set::{Stream,OpBuilder,Union,Intersection,Difference,
               SymmetricDifference};


pub type FileSetBuilder = SetBuilder<&'static mut io::BufWriter<File>>;
pub type MemSetBuilder = SetBuilder<Vec<u8>>;


/// Exposes information about errors over the ABI
pub struct Context {
    has_error: bool,
    error_type: *const libc::c_char,
    error_debug: *const libc::c_char,
    error_display: *const libc::c_char,
    error_description: *const libc::c_char,
}


/// Get an immutable reference from a raw pointer
macro_rules! ref_from_ptr {
    ($p:ident) => (unsafe {
        assert!(!$p.is_null());
        &*$p
    })
}

/// Get a mutable reference from a raw pointer
macro_rules! mutref_from_ptr {
    ($p:ident) => (unsafe {
        assert!(!$p.is_null());
        &mut *$p
    })
}

/// Get the object referenced by the raw pointer
macro_rules! val_from_ptr {
    ($p:ident) => (unsafe {
        assert!(!$p.is_null());
        Box::from_raw($p)
    })
}

/// Declare a function that frees a struct's memory
macro_rules! make_free_fn {
    ($name:ident, $t:ty) => (
        #[no_mangle]
        pub extern fn $name(ptr: $t) {
            assert!(!ptr.is_null());
            val_from_ptr!(ptr);
        }
    )
}

/// Declare a function that returns the next item from a stream
macro_rules! make_next_fn {
    ($name:ident, $t:ty) => (
        #[no_mangle]
        pub extern fn $name(ptr: $t) -> *const libc::c_char {
            let stream = mutref_from_ptr!(ptr);
            match stream.next() {
                Some(val) => CString::new(val).unwrap().into_raw(),
                None      => ptr::null()
            }
        }
    )
}

/// Run an expression and in case of an error, store information about the
/// error in the passed Context struct and return a default value.
macro_rules! with_context {
    ($ctx_ptr:ident, $default_rval:expr, $e:expr) => {{
        let ctx = mutref_from_ptr!($ctx_ptr);
        ctx.has_error = false;
        match $e {
            Ok(val) => val,
            Err(err) => {
                ctx.has_error = true;
                ctx.error_type = str_to_cstr(get_typename(&err));
                ctx.error_debug = str_to_cstr(&format!("{:?}", err));
                ctx.error_display = str_to_cstr(&format!("{}", err));
                ctx.error_description = str_to_cstr(err.description());
                return $default_rval;
            }
        }
    }}
}


fn cstr_to_str<'a>(s: *mut libc::c_char) -> &'a str {
    let cstr = unsafe { CStr::from_ptr(s) };
    cstr.to_str().unwrap()
}

fn str_to_cstr(string: &str) -> *mut libc::c_char {
    CString::new(string).unwrap().into_raw()
}

fn to_raw_ptr<T>(v: T) -> *mut T {
    Box::into_raw(Box::new(v))
}


/* FIXME: This requires the nightly channel, isn't there a better way to
 *        get this information? */
fn get_typename<T>(_: &T) -> &'static str {
    unsafe { intrinsics::type_name::<T>() }
}


#[no_mangle]
pub extern fn context_new() -> *mut Context {
    to_raw_ptr(Context { has_error: false,
                         error_type: ptr::null(),
                         error_description: ptr::null(),
                         error_display: ptr::null(),
                         error_debug: ptr::null() })
}
make_free_fn!(fst_context_free, *mut Context);

#[no_mangle]
pub extern fn fst_string_free(s: *mut libc::c_char) {
    unsafe { CString::from_raw(s) };
}

#[no_mangle]
pub extern fn fst_bufwriter_new(ctx: *mut Context,
                                s: *mut libc::c_char)
                                -> *mut io::BufWriter<File> {
    let path = cstr_to_str(s);
    let file = with_context!(ctx, ptr::null_mut(), File::create(path));
    to_raw_ptr(io::BufWriter::new(file))
}
make_free_fn!(fst_bufwriter_free, *mut io::BufWriter<File>);


#[no_mangle]
pub extern fn fst_filesetbuilder_new(ctx: *mut Context,
                                     wtr_ptr: *mut io::BufWriter<File>)
                                     -> *mut FileSetBuilder {
    let wtr = mutref_from_ptr!(wtr_ptr);
    to_raw_ptr(with_context!(ctx, ptr::null_mut(),
                             SetBuilder::new(wtr)))
}

#[no_mangle]
pub extern fn fst_filesetbuilder_insert(ctx: *mut Context,
                                        ptr: *mut FileSetBuilder,
                                        s: *mut libc::c_char)
                                        -> bool {
    let build = mutref_from_ptr!(ptr);
    with_context!(ctx, false, build.insert(cstr_to_str(s)));
    true
}

#[no_mangle]
pub extern fn fst_filesetbuilder_finish(ctx: *mut Context,
                                        ptr: *mut FileSetBuilder)
                                        -> bool {
    let build = val_from_ptr!(ptr);
    with_context!(ctx, false, build.finish());
    true
}

#[no_mangle]
pub extern fn fst_memsetbuilder_new() -> *mut MemSetBuilder {
    to_raw_ptr(SetBuilder::memory())
}

#[no_mangle]
pub extern fn fst_memsetbuilder_insert (ctx: *mut Context,
                                        ptr: *mut MemSetBuilder,
                                        s: *mut libc::c_char)
                                        -> bool {
    let build = mutref_from_ptr!(ptr);
    with_context!(ctx, false, build.insert(cstr_to_str(s)));
    true
}

#[no_mangle]
pub extern fn fst_memsetbuilder_finish(ctx: *mut Context,
                                       ptr: *mut MemSetBuilder)
                                       -> *mut Set {
    let build = val_from_ptr!(ptr);
    let data = with_context!(ctx, ptr::null_mut(), build.into_inner());
    let set = with_context!(ctx, ptr::null_mut(), Set::from_bytes(data));
    to_raw_ptr(set)
}

#[no_mangle]
pub extern fn fst_set_open(ctx: *mut Context,
                           cpath: *mut libc::c_char)
                           -> *mut Set {
    let path = cstr_to_str(cpath);
    let set = with_context!(ctx, ptr::null_mut(), Set::from_path(path));
    to_raw_ptr(set)
}
make_free_fn!(fst_set_free, *mut Set);


#[no_mangle]
pub extern fn fst_set_contains(ptr: *mut Set, s: *mut libc::c_char) -> bool {
    let set = mutref_from_ptr!(ptr);
    set.contains(cstr_to_str(s))
}

#[no_mangle]
pub extern fn fst_set_stream(ptr: *mut Set) -> *mut Stream<'static> {
    let set = mutref_from_ptr!(ptr);
    to_raw_ptr(set.stream())
}
make_free_fn!(fst_setstream_free, *mut Stream);
make_next_fn!(fst_setstream_next, *mut Stream);

#[no_mangle]
pub extern fn fst_set_len(ptr: *mut Set) -> libc::size_t {
    let set = mutref_from_ptr!(ptr);
    set.len()
}

#[no_mangle]
pub extern fn fst_set_isdisjoint(self_ptr: *mut Set, oth_ptr: *mut Set) -> bool {
    let slf = ref_from_ptr!(self_ptr);
    let oth = ref_from_ptr!(oth_ptr);
    slf.is_disjoint(oth)
}

#[no_mangle]
pub extern fn fst_set_issubset(self_ptr: *mut Set, oth_ptr: *mut Set) -> bool {
    let slf = ref_from_ptr!(self_ptr);
    let oth = ref_from_ptr!(oth_ptr);
    slf.is_subset(oth)
}

#[no_mangle]
pub extern fn fst_set_issuperset(self_ptr: *mut Set, oth_ptr: *mut Set) -> bool {
    let slf = ref_from_ptr!(self_ptr);
    let oth = ref_from_ptr!(oth_ptr);
    slf.is_superset(oth)
}

#[no_mangle]
pub extern fn fst_levenshtein_new(ctx: *mut Context,
                                  c_key: *mut libc::c_char,
                                  max_dist: libc::uint32_t)
                                  -> *mut Levenshtein {
    let key = cstr_to_str(c_key);
    let lev = with_context!(ctx, ptr::null_mut(),
                            Levenshtein::new(key, max_dist));
    to_raw_ptr(lev)
}
make_free_fn!(fst_levenshtein_free, *mut Levenshtein);

#[no_mangle]
pub extern fn fst_set_levsearch(set_ptr: *mut Set,
                             lev_ptr: *mut Levenshtein) -> *mut Stream<'static, &'static Levenshtein> {
    let set = mutref_from_ptr!(set_ptr);
    let lev = ref_from_ptr!(lev_ptr);
    to_raw_ptr(set.search(lev).into_stream())
}
make_free_fn!(fst_levstream_free, *mut Stream<&Levenshtein>);


#[no_mangle]
pub extern fn fst_levstream_next(ptr: *mut Stream<&Levenshtein>) -> *const libc::c_char {
    let stream = mutref_from_ptr!(ptr);
    match stream.next() {
        Some(val) => CString::new(val).unwrap().into_raw(),
        None      => ptr::null()
    }
}

#[no_mangle]
pub extern fn fst_set_make_opbuilder(ptr: *mut Set) -> *mut OpBuilder<'static> {
    let set = ref_from_ptr!(ptr);
    let ob = set.op();
    to_raw_ptr(ob)
}
make_free_fn!(fst_opbuilder_free, *mut OpBuilder<'static>);

#[no_mangle]
pub extern fn fst_opbuilder_push(ptr: *mut OpBuilder, set_ptr: *mut Set) {
    let set = ref_from_ptr!(set_ptr);
    //let set = val_from_ptr!(set_ptr);
    let ob = mutref_from_ptr!(ptr);
    ob.push(set);
}

#[no_mangle]
pub extern fn fst_opbuilder_union(ptr: *mut OpBuilder<'static>)
                                  -> *mut Union<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.union())
}
make_free_fn!(fst_union_free, *mut Union<'static>);
make_next_fn!(fst_union_next, *mut Union<'static>);

#[no_mangle]
pub extern fn fst_opbuilder_intersection(ptr: *mut OpBuilder<'static>)
                                         -> *mut Intersection<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.intersection())
}
make_free_fn!(fst_intersection_free, *mut Intersection);
make_next_fn!(fst_intersection_next, *mut Intersection);

#[no_mangle]
pub extern fn fst_opbuilder_difference(ptr: *mut OpBuilder<'static>)
                                       -> *mut Difference<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.difference())
}
make_free_fn!(fst_difference_free, *mut Difference);
make_next_fn!(fst_difference_next, *mut Difference);

#[no_mangle]
pub extern fn fst_opbuilder_symmetricdifference(ptr: *mut OpBuilder<'static>)
                                                -> *mut SymmetricDifference<'static> {
    let ob = val_from_ptr!(ptr);
    to_raw_ptr(ob.symmetric_difference())
}
make_free_fn!(fst_symmetricdifference_free, *mut SymmetricDifference);
make_next_fn!(fst_symmetricdifference_next, *mut SymmetricDifference);
