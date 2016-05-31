import sys
platform = sys.platform
if 'linux' in platform:
    from psutil._pslinux import pmem
elif 'darwin' in platform:
    from psutil._psosx import pmem
elif 'win' in platform:
    from psutil._pswindows import pmem


def pytest_assertrepr_compare(op, left, right):
    if isinstance(left, pmem) and isinstance(right, pmem) and op == ">=":
        return ['Detected memory leak: {} bytes'.format(right.rss - left.rss)]
