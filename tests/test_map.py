# -*- coding: utf-8 -*-
import pytest

import rust_fst.lib as lib
from rust_fst import Map


TEST_ITEMS = [(u"möö", 1), (u"bar", 2), (u"baz", 1337), (u"foo", 2**16)]


def do_build(path=None, keys=TEST_ITEMS, sorted_=True):
    if sorted_:
        it = sorted(keys)
    else:
        it = keys
    if path:
        with Map.build(path) as builder:
            for key, val in it:
                builder.insert(key, val)
    else:
        return Map.from_iter(it)


@pytest.fixture
def fst_map():
    return do_build()


def test_build(tmpdir):
    fst_path = str(tmpdir.join('test.fst'))
    do_build(fst_path)


def test_build_outoforder(tmpdir):
    fst_path = str(tmpdir.join('test.fst'))
    with pytest.raises(lib.TransducerError):
        do_build(fst_path, sorted_=False)


def test_build_baddir():
    fst_path = "/guaranteed-to-not-exist/set.fst"
    with pytest.raises(OSError):
        do_build(fst_path)


def test_build_memory(fst_map):
    assert len(fst_map) == 4


def test_map_contains(fst_map):
    for key, _ in TEST_ITEMS:
        assert key in fst_map


def test_map_items(fst_map):
    items = list(fst_map.items())
    assert items == sorted(TEST_ITEMS)


def test_map_getitem(fst_map):
    for key, val in TEST_ITEMS:
        assert fst_map[key] == val


def test_map_keys(fst_map):
    keys = list(fst_map.keys())
    assert keys == sorted([k for k, _ in TEST_ITEMS])


def test_map_iter(fst_map):
    assert list(fst_map) == sorted([k for k, _ in TEST_ITEMS])


def test_map_values(fst_map):
    values = list(fst_map.values())
    assert values == [v for _, v in sorted(TEST_ITEMS)]


def test_map_search(fst_map):
    matches = list(fst_map.search("bam", 1))
    assert matches == [(u"bar", 2), (u"baz", 1337)]


def test_map_union():
    a = Map.from_iter({'bar': 8, 'baz': 16})
    b = Map.from_iter({'bar': 32, 'moo': 64})
    u = dict(a.union(b))
    assert len(u) == 3
    assert u['bar'] == ((0, 8), (1, 32))
    assert u['baz'] == ((0, 16),)
    assert u['moo'] == ((1, 64),)


def test_map_intersection():
    a = Map.from_iter({'bar': 8, 'baz': 16})
    b = Map.from_iter({'bar': 32, 'moo': 64})
    i = dict(a.intersection(b))
    assert len(i) == 1
    assert i['bar'] == ((0, 8), (1, 32))


def test_map_difference():
    a = Map.from_iter({'bar': 8, 'baz': 16})
    b = Map.from_iter({'bar': 32, 'moo': 64})
    d = dict(a.difference(b))
    assert len(d) == 1
    assert d['baz'] == ((0, 16),)


def test_map_symmetric_difference():
    a = Map.from_iter({'bar': 8, 'baz': 16})
    b = Map.from_iter({'bar': 32, 'moo': 64})
    s = dict(a.symmetric_difference(b))
    assert len(s) == 2
    assert s['baz'] == ((0, 16),)
    assert s['moo'] == ((1, 64),)


def test_range(fst_map):
    assert dict(fst_map['f':]) == {'foo': 2**16, u'möö': 1}
    assert dict(fst_map[:'m']) == {'bar': 2, 'baz': 1337, 'foo': 2**16}
    assert dict(fst_map['baz':'m']) == {'baz': 1337, 'foo': 2**16}
    with pytest.raises(ValueError):
        fst_map['c':'a']
