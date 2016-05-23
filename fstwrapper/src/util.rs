extern crate libc;


use std::error::Error;
use std::ffi::{CStr, CString};
use std::fs::File;
use std::intrinsics;
use std::io;
use std::ptr;
use fst::Levenshtein;


/// Exposes information about errors over the ABI
pub struct Context {
    pub has_error: bool,
    pub error_type: *const libc::c_char,
    pub error_debug: *const libc::c_char,
    pub error_display: *const libc::c_char,
    pub error_description: *const libc::c_char,
}


pub fn cstr_to_str<'a>(s: *mut libc::c_char) -> &'a str {
    let cstr = unsafe { CStr::from_ptr(s) };
    cstr.to_str().unwrap()
}

pub fn str_to_cstr(string: &str) -> *mut libc::c_char {
    CString::new(string).unwrap().into_raw()
}

pub fn to_raw_ptr<T>(v: T) -> *mut T {
    Box::into_raw(Box::new(v))
}

// FIXME: This requires the nightly channel, isn't there a better way to
//        get this information?
pub fn get_typename<T>(_: &T) -> &'static str {
    unsafe { intrinsics::type_name::<T>() }
}

#[no_mangle]
pub extern "C" fn fst_context_new() -> *mut Context {
    to_raw_ptr(Context {
        has_error: false,
        error_type: ptr::null(),
        error_description: ptr::null(),
        error_display: ptr::null(),
        error_debug: ptr::null(),
    })
}
make_free_fn!(fst_context_free, *mut Context);

#[no_mangle]
pub extern "C" fn fst_string_free(s: *mut libc::c_char) {
    unsafe { CString::from_raw(s) };
}

#[no_mangle]
pub extern "C" fn fst_bufwriter_new(ctx: *mut Context,
                                    s: *mut libc::c_char)
                                    -> *mut io::BufWriter<File> {
    let path = cstr_to_str(s);
    let file = with_context!(ctx, ptr::null_mut(), File::create(path));
    to_raw_ptr(io::BufWriter::new(file))
}
make_free_fn!(fst_bufwriter_free, *mut io::BufWriter<File>);


#[no_mangle]
pub extern "C" fn fst_levenshtein_new(ctx: *mut Context,
                                      c_key: *mut libc::c_char,
                                      max_dist: libc::uint32_t)
                                      -> *mut Levenshtein {
    let key = cstr_to_str(c_key);
    let lev = with_context!(ctx, ptr::null_mut(),
                            Levenshtein::new(key, max_dist));
    to_raw_ptr(lev)
}
make_free_fn!(fst_levenshtein_free, *mut Levenshtein);
