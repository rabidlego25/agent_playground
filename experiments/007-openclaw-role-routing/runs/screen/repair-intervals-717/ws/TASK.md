# Task

`intervals.py` merges overlapping closed intervals and reports total coverage.

`merge(spans)` takes a list of `(start, end)` pairs and returns them merged and sorted,
with touching intervals (`(1, 3)` and `(3, 5)`) counted as overlapping and combined into `(1, 5)`.
`covered(spans)` returns the total length covered, counting overlap once.

Something in here is wrong. The smoke tests pass and the module is still incorrect.
Fix `intervals.py` so it matches the specification above. Do not change the function
signatures.
