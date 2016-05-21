# -*- coding: utf-8 -*-
import random
import string

import pytest

import rust_fst.lib as lib
from rust_fst import Set

TEST_KEYS = [u"möö", u"bar", u"baz", u"foo"]


def random_keys(n=10, max_length=128):
    for _ in range(n):
        length = random.randint(1, max_length)
        yield u''.join(random.choice(string.ascii_uppercase + string.digits)
                      for _ in range(length))


def do_build(path, keys=TEST_KEYS, sorted_=True):
    with Set.build(path) as builder:
        for key in (sorted(keys) if sorted_ else keys):
            builder.insert(key)


@pytest.fixture
def fst_set(tmpdir):
    fst_path = str(tmpdir.join('test.fst'))
    do_build(fst_path)
    return Set(fst_path)


def test_build(tmpdir):
    fst_path = str(tmpdir.join('test.fst'))
    do_build(fst_path)
    assert True


def test_build_outoforder(tmpdir):
    fst_path = str(tmpdir.join('test.fst'))
    with pytest.raises(lib.TransducerError):
        do_build(fst_path, sorted_=False)


def test_build_baddir():
    fst_path = "/guaranteed-to-not-exist/set.fst"
    with pytest.raises(OSError):
        with Set.build(fst_path) as builder:
            for key in sorted(TEST_KEYS):
                builder.insert(key)


def test_load_badfile(tmpdir):
    bad_path = tmpdir.join("bad.fst")
    with bad_path.open('wb') as fp:
        fp.write(b'\xFF'*16)
    with pytest.raises(lib.TransducerError):
        fst_set = Set(str(bad_path))


def test_iter(fst_set):
    stored_keys = list(fst_set)
    assert stored_keys == sorted(TEST_KEYS)


def test_len(fst_set):
    assert len(fst_set) == 4


def test_contains(fst_set):
    for key in TEST_KEYS:
        assert key in fst_set


def test_issubset(tmpdir, fst_set):
    oth_path = tmpdir.join('other.fst')
    do_build(str(oth_path), keys=TEST_KEYS[:-2])
    other_set = Set(str(oth_path))
    assert other_set.issubset(fst_set)
    assert fst_set.issubset(fst_set)


def test_issuperset(tmpdir, fst_set):
    oth_path = tmpdir.join('other.fst')
    do_build(str(oth_path), keys=TEST_KEYS[:-2])
    other_set = Set(str(oth_path))
    assert fst_set.issuperset(other_set)
    assert fst_set.issuperset(fst_set)


def test_isdisjoint(tmpdir, fst_set):
    oth_path = tmpdir.join('other.fst')
    do_build(str(oth_path), keys=[u'ene', u'mene'])
    other_set = Set(str(oth_path))
    assert fst_set.isdisjoint(other_set)
    assert other_set.isdisjoint(fst_set)
    assert not fst_set.isdisjoint(fst_set)
    assert not fst_set.issuperset(other_set)
    assert not fst_set.issubset(other_set)


def test_search(fst_set):
    matches = list(fst_set.search("bam", 1))
    assert matches == [u"bar", u"baz"]


def test_levautomaton_too_big(fst_set):
    with pytest.raises(lib.LevenshteinError):
        next(fst_set.search(u"a"*24, 24))
