"""Fast integer hand evaluator for 5-7 cards (cards are ints 0..51:
rank index = c >> 2 (0 = deuce .. 12 = ace), suit = c & 3).
Scores compare with < / > exactly like card_utils.evaluate."""

STRAIGHT = [0] * 8192
for _m in range(8192):
    for _hi in range(12, 3, -1):
        _need = 0b11111 << (_hi - 4)
        if _m & _need == _need:
            STRAIGHT[_m] = _hi + 1
            break
    else:
        if _m & 0x100F == 0x100F:
            STRAIGHT[_m] = 4  # wheel, five-high (index 3, +1)
POPCOUNT = [bin(_m).count("1") for _m in range(8192)]


def card_to_int(card):
    return (card.value - 2) * 4 + "CDHS".index(card.suit)


def ev(cards):
    rc = [0] * 13
    m0 = m1 = m2 = m3 = 0
    for c in cards:
        r = c >> 2
        rc[r] += 1
        s = c & 3
        if s == 0:
            m0 |= 1 << r
        elif s == 1:
            m1 |= 1 << r
        elif s == 2:
            m2 |= 1 << r
        else:
            m3 |= 1 << r
    for m in (m0, m1, m2, m3):
        if POPCOUNT[m] >= 5:
            sf = STRAIGHT[m]
            if sf:
                return (8 << 20) | sf
            score = 5
            n = 0
            r = 12
            while n < 5:
                if (m >> r) & 1:
                    score = (score << 4) | r
                    n += 1
                r -= 1
            return score
    quads = trips = -1
    trips2 = -1
    pairs = []
    singles = []
    for r in range(12, -1, -1):
        n = rc[r]
        if n == 0:
            continue
        if n == 4:
            quads = r
        elif n == 3:
            if trips < 0:
                trips = r
            elif trips2 < 0:
                trips2 = r
        elif n == 2:
            pairs.append(r)
        else:
            singles.append(r)
    if quads >= 0:
        k = -1
        for r in range(12, -1, -1):
            if r != quads and rc[r]:
                k = r
                break
        return (7 << 20) | (quads << 16) | (max(k, 0) << 12)
    if trips >= 0 and (trips2 >= 0 or pairs):
        p = trips2
        if pairs and pairs[0] > p:
            p = pairs[0]
        return (6 << 20) | (trips << 16) | (p << 12)
    allm = m0 | m1 | m2 | m3
    st = STRAIGHT[allm]
    if st:
        return (4 << 20) | st
    if trips >= 0:
        s = singles
        return (3 << 20) | (trips << 16) | (s[0] << 12) | (s[1] << 8)
    if len(pairs) >= 2:
        k = singles[0] if singles else -1
        if len(pairs) >= 3 and pairs[2] > k:
            k = pairs[2]
        return (2 << 20) | (pairs[0] << 16) | (pairs[1] << 12) | (max(k, 0) << 8)
    if pairs:
        s = singles
        return (1 << 20) | (pairs[0] << 16) | (s[0] << 12) | (s[1] << 8) | (s[2] << 4)
    s = singles
    return (s[0] << 16) | (s[1] << 12) | (s[2] << 8) | (s[3] << 4) | s[4]
