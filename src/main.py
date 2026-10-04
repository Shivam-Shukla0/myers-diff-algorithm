import sys
from array import array


def myers(A, B):
    """Return a minimal edit script for sequences A -> B as a list of
    ' ' (keep), '-' (delete from A), '+' (insert from B)."""
    n, m = len(A), len(B)
    # Trim the common prefix and suffix; this makes most real diffs tiny.
    p = 0
    while p < n and p < m and A[p] == B[p]:
        p += 1
    s = 0
    while s < n - p and s < m - p and A[n - 1 - s] == B[m - 1 - s]:
        s += 1
    core = _myers_core(A[p:n - s], B[p:m - s])
    return [' '] * p + core + [' '] * s


def _myers_core(A, B):
    N, M = len(A), len(B)
    if N == 0:
        return ['+'] * M
    if M == 0:
        return ['-'] * N
    maxd = N + M
    off = maxd + 1
    V = [0] * (2 * maxd + 3)
    trace = []  # trace[d-1] = V of round d-1, only the k values that matter
    found = -1
    for d in range(maxd + 1):
        if d > 0:
            trace.append(array('i', V[off - (d - 1): off + d: 2]))
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and V[off + k - 1] < V[off + k + 1]):
                x = V[off + k + 1]          # move down (insert)
            else:
                x = V[off + k - 1] + 1      # move right (delete)
            y = x - k
            while x < N and y < M and A[x] == B[y]:
                x += 1
                y += 1
            V[off + k] = x
            if x >= N and y >= M:
                found = d
                break
        if found >= 0:
            break

    # Walk back from (N, M) to (0, 0) using the saved V arrays.
    ops = []
    x, y = N, M
    for d in range(found, 0, -1):
        tr = trace[d - 1]
        base = d - 1

        def get(kk):
            return tr[(kk + base) // 2]

        k = x - y
        if k == -d or (k != d and get(k - 1) < get(k + 1)):
            pk = k + 1
            insert = True
        else:
            pk = k - 1
            insert = False
        px = get(pk)
        py = px - pk
        ex, ey = (px, py + 1) if insert else (px + 1, py)
        while x > ex:               # the snake (keeps)
            ops.append(' ')
            x -= 1
            y -= 1
        ops.append('+' if insert else '-')
        x, y = px, py
    while x > 0:                    # leading snake at d = 0
        ops.append(' ')
        x -= 1
    ops.reverse()
    return ops


def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    parts = data.split(b"\n")
    if parts and parts[-1] == b"":
        parts.pop()
    return parts


def blocks(ops, a, b):
    """Yield ('keep', line) or ('block', dels, ins) with delete-first order."""
    i = j = 0
    dels, ins = [], []
    for op in ops:
        if op == ' ':
            if dels or ins:
                yield ('block', dels, ins)
                dels, ins = [], []
            yield ('keep', a[i])
            i += 1
            j += 1
        elif op == '-':
            dels.append(a[i])
            i += 1
        else:
            ins.append(b[j])
            j += 1
    if dels or ins:
        yield ('block', dels, ins)


def ranges_to_str(r):
    if not r:
        return "."
    return ",".join("%d-%d" % (s, e) for s, e in r)


def add_range(r, pos):
    if r and r[-1][1] == pos:
        r[-1][1] = pos + 1
    else:
        r.append([pos, pos + 1])


def highlight_pair(old, new):
    o = old.decode("utf-8")
    nw = new.decode("utf-8")
    ops = myers(o, nw)
    i = j = 0
    old_r, new_r = [], []
    for op in ops:
        if op == ' ':
            i += 1
            j += 1
        elif op == '-':
            add_range(old_r, i)
            i += 1
        else:
            add_range(new_r, j)
            j += 1
    return ("? " + ranges_to_str(old_r) + " | " + ranges_to_str(new_r)).encode()


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        sys.stderr.write("usage: main.py lines|highlight A B\n")
        sys.exit(2)
    mode, pa, pb = sys.argv[1:4]
    try:
        a = read_lines(pa)
        b = read_lines(pb)
    except OSError as e:
        sys.stderr.write("error: %s\n" % e)
        sys.exit(2)

    ops = myers(a, b)
    out = []
    for item in blocks(ops, a, b):
        if item[0] == 'keep':
            out.append(b" " + item[1] + b"\n")
            continue
        _, dels, ins = item
        for d in dels:
            out.append(b"-" + d + b"\n")
        for idx, line in enumerate(ins):
            out.append(b"+" + line + b"\n")
            if mode == "highlight" and idx < len(dels):
                out.append(highlight_pair(dels[idx], line) + b"\n")
    sys.stdout.buffer.write(b"".join(out))


if __name__ == "__main__":
    main()