"""Merge overlapping closed intervals."""


def merge(spans):
    if not spans:
        return []
    ordered = list(spans)
    out = [list(ordered[0])]
    for start, end in ordered[1:]:
        if start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [tuple(s) for s in out]


def covered(spans):
    return sum(end - start for start, end in merge(spans))
