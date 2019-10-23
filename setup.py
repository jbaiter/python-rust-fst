import platform

from setuptools import setup

# The AppVeyor build doesn't use rustup, so we run cargo directly there
if platform.system() == 'Windows':
    BUILD_CMD = ['cargo', 'build', '--release']
else:
    BUILD_CMD = ['rustup', 'run', 'nightly', 'cargo', 'build', '--release']


def build_native(spec):
    build = spec.add_external_build(cmd=BUILD_CMD, path='./rust')
    spec.add_cffi_module(
        module_path='rust_fst._native',
        dylib=lambda: build.find_dylib('rust_fst', in_path='target/release'),
        header_filename=lambda: build.find_header('rust_fst.h', in_path='./'),
        rtld_flags=['NOW', 'NODELETE']
    )


setup(
    name='rust-fst',
    version='0.2.0dev',
    author='Johannes Baiter',
    author_email='johannes.baiter@gmail.com',
    description=('Python bindings for the Rust `fst` create, providing sets '
                 'and maps backed by finite state transducers.'),
    license='MIT',
    keywords=['fst', 'rust', 'levenshtein', 'automata', 'transducer',
              'data_structures'],
    url='https://github.com/jbaiter/python-rust-fst',
    tests_require=['pytest', 'psutil', 'decorator'],
    packages=['rust_fst'],
    zip_safe=False,
    platforms='any',
    setup_requires=['milksnake'],
    install_requires=['milksnake'],
    milksnake_tasks=[build_native],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Text Processing :: Indexing']
)
