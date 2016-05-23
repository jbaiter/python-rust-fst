from setuptools import setup


setup(
    name='rust-fst',
    version='0.1',
    author='Johannes Baiter',
    author_email='johannes.baiter@gmail.com',
    description=('Python bindings for the Rust `fst` create, providing sets '
                 'and maps backed by finite state transducers.'),
    license='MIT',
    keywords=['fst', 'rust', 'levenshtein', 'automata', 'transducer',
              'data_structures'],
    url='https://github.com/jbaiter/python-rust-fst',
    setup_requires=['cffi>=1.0.0'],
    install_requires=['cffi>=1.0.0'],
    cffi_modules=['rust_fst/_build_ffi.py:ffi'],
    entry_points={'distutils.setup_keywords': [
        'rust_crates = rust_setuptools:rust_crates'
    ]},
    rust_crates=[('fstwrapper', 'rust_fst')],
    packages=['rust_fst'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing :: Indexing']
)
