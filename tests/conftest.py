from util import MemoryUsage


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, MemoryUsage) and isinstance(right, MemoryUsage) and op == ">=":
        return ['Detected memory leak: {} bytes'.format(right._rss - left._rss)]
