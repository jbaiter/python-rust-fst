# python-rust-fst

[![appveyor](https://ci.appveyor.com/api/projects/status/github/jbaiter/python-rust-fst)](https://ci.appveyor.com/project/jbaiter/python-rust-fst)
[![travis](https://travis-ci.org/jbaiter/python-rust-fst.svg)](https://travis-ci.org/jbaiter/python-rust-fst)
[![pypi downloads](https://img.shields.io/pypi/dm/rust_fst.svg?maxAge=2592000)](https://pypi.python.org/pypi/rust-fst)
[![pypi version](https://img.shields.io/pypi/v/rust_fst.svg?maxAge=2592000)](https://pypi.python.org/pypi/rust_fst)
[![pypi wheel](https://img.shields.io/pypi/wheel/rust_fst.svg?maxAge=2592000)](https://pypi.python.org/pypi/rust_fst)

Python bindings for [burntsushi's][1] [fst crate][2] ([rustdocs][3])
for FST-backed sets and maps.

For reasons why you might want to consider using it, see BurntSushi's great
article on ["Index[ing] 1,600,000,000 Keys with Automata and Rust"][4].

**tl;dr**:
- Work with larger-than-memory sets
- Perform fuzzy search using Levenshtein automata


## Installation
`rust_fst` is available as a binary wheel for the most common platforms (Linux
64bit x86, Windows 32/64bit x86 and OSX 64bit x86) and thus **does not require
a Rust installation.**

Just run `pip install rust_fst` to install the latest stable version of the
package.


## Development
- You will need:
    * Python >= 3.3, Python or PyPy >= 2.7 with development headers installed
    * Rust nightly (install via [rustup][5])
- Run `rustup override add nightly` to add an override for rustup to use the
  nightly channel for the repository
- Install with pip (without the `-e` flag, it does not work!)
- Run tests with `py.test python-rust-fst/tests` and make sure you are not
  in the root of the repo, since the installed (and compiled) package will not
  be used in that case.


## Status
The package exposes almost all functionality of the `fst` crate, except for:

- Combining the results of slicing, `search` and `search_re` with set operations
- Using raw transducers


## Examples
```python
from rust_fst import Map, Set

# Building a set in memory
keys = ["fa", "fo", "fob", "focus", "foo", "food", "foul"]
s = Set.from_iter(keys)

# Fuzzy searches on the set
matches = list(s.search(term="foo", max_dist=1))
assert matches == ["fo", "fob", "foo", "food"]

# Searching with a regular expression
matches = list(s.search_re(r'f\w{2}'))
assert matches == ["fob", "foo"]

# Store map on disk, requiring only constant memory for querying
items = [("bruce", 1), ("clarence", 2), ("stevie", 3)]
m = Map.from_iter(items, path="/tmp/map.fst")

# Find all items whose key is greater or equal (in lexicographical sense) to
# 'clarence'
matches = dict(m['clarence':])
assert matches == {'clarence': 2, 'stevie': 3}

# Create a map from a file input, using generators/yield
# The input file must be sorted on the first column, and look roughly like
#   keyA 123
#   keyB 456
def file_iterator(fpath):
  with open(fpath, 'rt') as fp:
    for line in fp:
      key, value = line.strip().split()
      yield key, int(value)
m = Map.from_iter( file_iterator('/your/input/file/'), '/your/mmapped/output.fst')

# re-open a file you built previously with from_iter()
m = Map(path='/path/to/existing.fst')
```


## Documentation
Head over to [readthedocs.org][6] for the API documentation.

If you want to know more about performance characteristics, memory usage
and about the implementation details, please head over to the
[documentation for the Rust crate][2]


[1]: http://burntsushi.net
[2]: https://github.com/BurntSushi/fst
[3]: http://burntsushi.net/rustdoc/fst/
[4]: http://blog.burntsushi.net/transducers/
[5]: https://www.rustup.rs/
[6]: https://rust-fst.readthedocs.org/
