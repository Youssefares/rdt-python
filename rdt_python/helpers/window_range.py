def window_range(start, n, mod=None):
    if mod is None:
        mod = 2*n
    current = start
    while True:
        yield current
        current = (current + 1) % mod
        n -= 1
        if not n:
           return