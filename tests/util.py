import gc

# functools.wraps breaks the pytest fixtures, so we have to use this
# thid-party package
import decorator
import psutil


def leakcheck(fn):
    # Compare the memory (after GC) before and after the test to determine
    # if we leaked memory
    def wrapper(fn, *args, **kwargs):
        gc.collect()
        mem_before = psutil.Process().memory_info()
        rv = fn(*args, **kwargs)
        gc.collect()
        mem_after = psutil.Process().memory_info()
        assert mem_before >= mem_after
        return rv
    return decorator.decorate(fn, wrapper)
