#![crate_type = "dylib"]
extern crate libc;
extern crate fst;

use libc::uint32_t;
use std::ffi::{CStr,CString};
use std::fs::File;
use std::io;
use std::ptr;
use fst::{IntoStreamer, Streamer, Levenshtein, Set, SetBuilder};
use fst::set::Stream;

pub type FileSetBuilder = SetBuilder<&'static mut io::BufWriter<File>>;

fn cstr_to_str<'a>(s: *mut libc::c_char) -> &'a str {
    let cstr = unsafe { CStr::from_ptr(s) };
    cstr.to_str().unwrap()
}

#[no_mangle]
pub extern fn string_free(s: *mut libc::c_char) {
    unsafe { CString::from_raw(s) };
}

#[no_mangle]
pub extern fn bufwriter_new(s: *mut libc::c_char) -> *mut io::BufWriter<File> {
    let path = cstr_to_str(s);
    Box::into_raw(Box::new(io::BufWriter::new(File::create(path).unwrap())))
}

#[no_mangle]
pub extern fn bufwriter_free(ptr: *mut io::BufWriter<File>) {
    unsafe { ptr::read(ptr) };
}

#[no_mangle]
pub extern fn fst_setbuilder_new(wtr_ptr: *mut io::BufWriter<File>) -> *mut FileSetBuilder {
    let wtr = unsafe {
        assert!(!wtr_ptr.is_null());
        &mut *wtr_ptr
    };
    let build = SetBuilder::new(wtr).unwrap();
    Box::into_raw(Box::new(build))
}

#[no_mangle]
pub extern fn fst_setbuilder_insert(ptr: *mut FileSetBuilder, s: *mut libc::c_char) {
    let build = unsafe {
        assert!(!ptr.is_null());
        &mut *ptr
    };
    build.insert(cstr_to_str(s)).unwrap();
}

#[no_mangle]
pub extern fn fst_setbuilder_finish(ptr: *mut FileSetBuilder) {
    let build = unsafe {
        assert!(!ptr.is_null());
        ptr::read(ptr)
    };
    build.finish().unwrap()
}

#[no_mangle]
pub extern fn fst_set_open(cpath: *mut libc::c_char) -> *mut Set {
    let path = cstr_to_str(cpath);
    Box::into_raw(Box::new(Set::from_path(path).unwrap()))
}

#[no_mangle]
pub extern fn fst_set_free(ptr: *mut Set) {
    unsafe { ptr::read(ptr) };
}

#[no_mangle]
pub extern fn fst_set_contains(ptr: *mut Set, s: *mut libc::c_char) -> bool {
    let set = unsafe {
        assert!(!ptr.is_null());
        &mut *ptr
    };
    set.contains(cstr_to_str(s))
}

#[no_mangle]
pub extern fn fst_set_stream(ptr: *mut Set) -> *mut Stream<'static> {
    let set = unsafe {
        assert!(!ptr.is_null());
        &mut *ptr
    };
    Box::into_raw(Box::new(set.stream()))
}

#[no_mangle]
pub extern fn fst_stream_next(ptr: *mut Stream) -> *const libc::c_char {
    let stream = unsafe {
        assert!(!ptr.is_null());
        &mut *ptr
    };
    match stream.next() {
        Some(val) => CString::new(val).unwrap().into_raw(),
        None      => ptr::null()
    }
}

#[no_mangle]
pub extern fn fst_stream_free(ptr: *mut Stream) {
    unsafe { ptr::read(ptr) };
}

#[no_mangle]
pub extern fn levenshtein_new(c_key: *mut libc::c_char,
                              max_dist: uint32_t) -> *mut Levenshtein {
    let key = cstr_to_str(c_key);
    Box::into_raw(Box::new(Levenshtein::new(key, max_dist).unwrap()))
}

#[no_mangle]
pub extern fn levenshtein_free(ptr: *mut Levenshtein) {
    unsafe { ptr::read(ptr) };
}

#[no_mangle]
pub extern fn fst_set_search(set_ptr: *mut Set,
                             lev_ptr: *mut Levenshtein) -> *mut Stream<'static, &'static Levenshtein> {
    let set = unsafe {
        assert!(!set_ptr.is_null());
        &mut *set_ptr
    };
    let lev = unsafe {
        assert!(!lev_ptr.is_null());
        &*lev_ptr
    };
    let sb = set.search(lev);
    Box::into_raw(Box::new(sb.into_stream()))
}


#[no_mangle]
pub extern fn lev_stream_next(ptr: *mut Stream<&Levenshtein>) -> *const libc::c_char {
    let stream = unsafe {
        assert!(!ptr.is_null());
        &mut *ptr
    };
    match stream.next() {
        Some(val) => CString::new(val).unwrap().into_raw(),
        None      => ptr::null()
    }
}

#[no_mangle]
pub extern fn lev_stream_free(ptr: *mut Stream<&Levenshtein>) {
    unsafe { ptr::read(ptr) };
}
