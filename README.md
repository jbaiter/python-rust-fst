# python-rust-fst

Python bindings for [burntsushi's][1] [fst crate][2] ([rustdocs][3])
for FST-backed sets and maps.

For reasons why you might want to consider using it, see BurntSushi's great
article on ["Index[ing] 1,600,000,000 Keys with Automata and Rust"][4].

**tl;dr**:
- Work with larger-than-memory sets
- Perform fuzzy search using Levenshtein automata

## Installation
- You will need:
    * Python >= 3.3, Python or PyPy >= 2.7 with development headers installed
    * Rust nightly (install via [rustup][5])
- Clone the repository. Installation with `pip install git+...` does not work
  currently
- Run `rustup override add nightly` to add an override for rustup to use the
  nightly channel for the repository
- Run `python setup.py bdist_wheel` to generate a wheel
- Install the wheel with `pip install dist/rust_fst-0.1-py3-none-any.whl`


## Status
### Set
- [x]  Create and load sets on disk and in memory
- [x]  Iterate through complete set contents
- [x]  Search sets with a Levenshtein automaton
- [x]  Perform set operations (union, [symmetric] difference, intersection)
- [ ]  Iterate through a range of set contents

### Map
- [X]  Create and load maps on disk and in memory
- [X]  Iterate through complete map (key, value) pairs
- [X]  Iterate through complete map keys and items
- [X]  Search map items with a Levenshtein automaton
- [ ]  Perform set operations (union, [symmetric] difference, intersection)
       on the map
- [ ]  Iterate through a range of map contents

[1]: http://blog.burntsushi.net/transducers/
[2]: https://github.com/BurntSushi/fst
[3]: http://burntsushi.net/rustdoc/fst/
[4]: http://blog.burntsushi.net/transducers/
[5]: https://www.rustup.rs/
