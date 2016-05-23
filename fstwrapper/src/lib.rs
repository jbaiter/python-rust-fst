#![crate_type = "dylib"]
#![feature(core_intrinsics)]

extern crate libc;
extern crate fst;


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

/// Declare a function that returns the next item from a set stream
macro_rules! set_make_next_fn {
    ($name:ident, $t:ty) => (
        #[no_mangle]
        pub extern fn $name(ptr: $t) -> *const libc::c_char {
            let stream = mutref_from_ptr!(ptr);
            match stream.next() {
                Some(val) => ::std::ffi::CString::new(val).unwrap().into_raw(),
                None      => ::std::ptr::null()
            }
        }
    )
}

/// Declare a function that returns the next item from a map stream
macro_rules! map_make_next_fn {
    ($name:ident, $t:ty) => (
        #[no_mangle]
        pub extern fn $name(ptr: $t) -> *mut MapItem {
            let stream = mutref_from_ptr!(ptr);
            match stream.next() {
                Some((k, v)) => to_raw_ptr(
                    MapItem { key: ::std::ffi::CString::new(k).unwrap().into_raw(),
                              value: v }),
                None         => ::std::ptr::null_mut()
            }
        }
    )
}

/// Evaluate an expression and in case of an error, store information about the error in the passed
/// Context struct and return a default value.
macro_rules! with_context {
    ($ctx_ptr:ident, $default_rval:expr, $e:expr) => {{
        let ctx = mutref_from_ptr!($ctx_ptr);
        ctx.has_error = false;
        match $e {
            Ok(val) => val,
            Err(err) => {
                ctx.has_error = true;
                ctx.error_type = $crate::util::str_to_cstr($crate::util::get_typename(&err));
                ctx.error_debug = $crate::util::str_to_cstr(&format!("{:?}", err));
                ctx.error_display = $crate::util::str_to_cstr(&format!("{}", err));
                ctx.error_description = $crate::util::str_to_cstr(err.description());
                return $default_rval;
            }
        }
    }}
}

pub mod util;
pub mod set;
pub mod map;
