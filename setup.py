from setuptools import setup

from rust_setuptools import (build_rust_cmdclass, build_install_lib_cmdclass,
                             RustDistribution)

setup(
    name='rust-fst',
    version='0.1.2',
    author='Johannes Baiter',
    author_email='johannes.baiter@gmail.com',
    description=('Python bindings for the Rust `fst` create, providing sets '
                 'and maps backed by finite state transducers.'),
    license='MIT',
    keywords=['fst', 'rust', 'levenshtein', 'automata', 'transducer',
              'data_structures'],
    url='https://github.com/jbaiter/python-rust-fst',
    setup_requires=[
        'cffi>=1.0.0',
        'pytest-runner'],
    install_requires=['cffi>=1.0.0'],
    cffi_modules=['rust_fst/_build_ffi.py:ffi'],
    tests_require=['pytest'],
    distclass=RustDistribution,
    cmdclass={
        'build_rust': build_rust_cmdclass([('fstwrapper', 'rust_fst')]),
        'install_lib': build_install_lib_cmdclass()
    },
    packages=['rust_fst'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing :: Indexing']
)
