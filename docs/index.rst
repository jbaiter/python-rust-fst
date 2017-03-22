.. rust-fst documentation master file, created by
   sphinx-quickstart on Wed May 25 21:05:04 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to rust-fst's documentation!
====================================

Python bindings for `burntsushi's`_ `fst crate`_ (rustdocs_) for FST-backed
sets and maps.

For reasons why you might want to consider using it, see BurntSushi's great
article on `"Index[ing] 1,600,000,000 Keys with Automata and  Rust" <http://blog.burntsushi.net/transducers/>`__.

If you want to know more about performance characteristics, memory usage
and about the implementation details, please head over to the
`documentation for the Rust crate <http://burntsushi.net/rustdoc/fst/>`_.

**tl;dr**:

-  Work with larger-than-memory sets
-  Perform fuzzy search using Levenshtein automata

Installation
------------

-  You will need:

   -  Python >= 3.3, Python or PyPy >= 2.7 with development headers
      installed
   -  Rust nightly (install via rustup_)

-  Clone the repository. Installation with ``pip install git+...`` does
   not work
   currently
-  Run ``rustup override add nightly`` to add an override for rustup to
   use the
   nightly channel for the repository
-  Run ``python setup.py bdist_wheel`` to generate a wheel
-  Install the wheel with
   ``pip install dist/rust_fst-0.1-py3-none-any.whl``

Status
------

The package exposes almost all functionality of the ``fst`` crate,
except for:

-  Combining the results of slicing, ``search`` and ``search_re`` with
   set operations
-  Using raw transducers

Examples
--------

.. code:: python

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

API Reference
-------------

.. autoclass:: rust_fst.Set
    :member-order: bysource
    :members:
    :special-members:
    :exclude-members: __weakref__

.. autoclass:: rust_fst.Map
    :member-order: bysource
    :members:
    :special-members:
    :exclude-members: __weakref__

.. _burntsushi's: http://burntsushi.net
.. _fst crate: https://github.com/BurntSushi/fst
.. _rustdocs: http://burntsushi.net/rustdoc/fst/
.. _rustup: https://www.rustup.rs/
