from pathgrid import steps

assert steps(["...", "...", "..."], (0, 0), (0, 2)) == 2
assert steps(["...", "...", "..."], (1, 1), (1, 1)) == 0
print("smoke ok")
