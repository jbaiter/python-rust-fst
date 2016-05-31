import gc

# functools.wraps breaks the pytest fixtures, so we have to use this
# thid-party package
import decorator
import psutil


# Custom type for nicer assertion error message
class MemoryUsage(object):
    def __init__(self):
        self._rss = psutil.Process().memory_info().rss

    def __cmp__(self, other):
        return self._rss.__cmp__(other._rss)


def leakcheck(fn):
    # Compare the memory (after GC) before and after the test to determine
    # if we leaked memory
    def wrapper(fn, *args, **kwargs):
        gc.collect()
        mem_before = MemoryUsage()
        rv = fn(*args, **kwargs)
        gc.collect()
        mem_after = MemoryUsage()
        assert mem_before >= mem_after
        return rv
    return decorator.decorate(fn, wrapper)
