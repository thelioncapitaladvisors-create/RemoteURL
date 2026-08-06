def encode(bools):
    val = 0
    for i, b in enumerate(bools):
        if b:
            val += (1 << i)
    return val

def decode(val):
    temp = val
    res = []
    for _ in range(20):
        res.append((temp % 2) != 0)
        temp //= 2
    return res

bools = [True, False, True, False, False, True, True, False, True, False, True, False, True, False, True, False, True, False, True, False]
val = encode(bools)
print(f"Encoded: {val}")
decoded = decode(val)
print(f"Decoded matches: {bools == decoded}")
