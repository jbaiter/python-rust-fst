from setuptools import setup


setup(name='rust-fst',
    version='0.1',
    setup_requires=['cffi>=1.0.0'],
    install_requires=['cffi>=1.0.0'],
    cffi_modules=['rust_fst/_build_ffi.py:ffi'],
    entry_points={'distutils.setup_keywords': [
        'rust_crates = rust_setuptools:rust_crates'
    ]},
    rust_crates=[('fstwrapper', 'rust_fst')],
    packages=['rust_fst'],
    zip_safe=False
)
