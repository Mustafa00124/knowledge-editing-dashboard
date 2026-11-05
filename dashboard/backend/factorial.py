"""Two-level factorial designs (step 1 of hyperparameter tuning) and their
effects analysis. Pure Python: the backend has no numpy.

Design. Each swept setting is a factor with a low and a high value, coded -1
and +1. With k factors a full design is every one of the 2^k corners. A
regular fraction 2^(k-p) keeps the first k-p factors (the basic factors) as
a full design and sets each of the last p factors to the product of some
basic factors (its generator), so it costs 2^(k-p) runs. Its resolution is
the length of the shortest word in the defining relation: at resolution V
or more no main effect or two-factor interaction is aliased with another
main effect or two-factor interaction; at IV main effects are clear but
two-factor interactions are aliased with each other. Centre points set
every factor to its middle value (coded 0) and test for curvature.

Generators are the standard published ones (Montgomery, Design and Analysis
of Experiments, Table 8.14; Box, Hunter and Hunter, Table 6.22) where those
exist; the resolution of every entry is recomputed by `resolution()` and
checked in test_factorial.py.

Analysis. A main effect is the mean response at +1 minus the mean at -1; a
two-factor interaction is the same contrast on the product of the two
columns. Lenth's method (Lenth 1989) estimates the noise from the effects
themselves: with m contrasts c_j, s0 = 1.5 median|c_j|, the pseudo standard
error PSE = 1.5 median{|c_j| : |c_j| < 2.5 s0}, and an effect is active when
|c| exceeds the margin of error ME = t(0.975, m/3) PSE, or, more strictly,
the simultaneous margin SME = t((1 + 0.95^(1/m)) / 2, m/3) PSE.
"""
import itertools
import math

# I is left out, as in the literature, where it names the identity.
LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"

# (k, p) -> generator words over the basic factors' letters, one per added
# factor in order. p = 1 needs no entry: the added factor is the product of
# all the others (resolution k). Only fractions of resolution IV or more.
GENERATORS = {
    (6, 2): ["ABC", "BCD"],                      # 2^(6-2) IV
    (7, 2): ["ABCD", "ABDE"],                    # 2^(7-2) IV
    (8, 2): ["ABCD", "ABEF"],                    # 2^(8-2) V
    (8, 3): ["ABC", "ABD", "BCDE"],              # 2^(8-3) IV
    (9, 2): ["ACDFG", "BCEFG"],                  # 2^(9-2) VI
    (9, 3): ["ABCD", "ACEF", "CDEF"],            # 2^(9-3) IV
    (10, 2): ["ABCDE", "ABCFGH"],                # 2^(10-2) VI (found by search; resolution checked)
    (10, 3): ["ABCG", "BCDE", "ACDF"],           # 2^(10-3) V
    (10, 4): ["BCDF", "ACDF", "ABDE", "ABCE"],   # 2^(10-4) IV
    (11, 4): ["ABCD", "ABEF", "ACEG", "BDFG"],   # 2^(11-4) V (found by search; resolution checked)
}
MAX_FACTORS = 11
FULL_UP_TO = 6  # default to the full design up to this many factors (32 or 64 runs)


def generators(k, p):
    """The generator words for 2^(k-p), or None when there is no standard one."""
    if p == 0:
        return []
    if p == 1:
        return [LETTERS[:k - 1]] if k >= 3 else None
    return GENERATORS.get((k, p))


def _word_masks(k, gens):
    """Each generator as a bit mask over the k factors (its basic letters
    plus the factor it defines)."""
    base = k - len(gens)
    masks = []
    for i, word in enumerate(gens):
        mask = 1 << (base + i)
        for letter in word:
            mask |= 1 << LETTERS.index(letter)
        masks.append(mask)
    return masks


def defining_words(k, gens):
    """Every word of the defining relation (products of the generators), as
    tuples of factor indices."""
    masks = _word_masks(k, gens)
    words = []
    for r in range(1, len(masks) + 1):
        for combo in itertools.combinations(masks, r):
            mask = 0
            for m in combo:
                mask ^= m
            words.append(tuple(i for i in range(k) if mask >> i & 1))
    return words


def resolution(k, p):
    """Length of the shortest defining word; None for a full design."""
    gens = generators(k, p)
    if gens is None:
        raise ValueError(f"no standard 2^({k}-{p}) design")
    if not gens:
        return None
    return min(len(w) for w in defining_words(k, gens))


def roman(n):
    return {3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X", 11: "XI"}.get(n, str(n))


def fractions(k):
    """Every design on offer for k factors, largest first: the full design
    and each standard fraction of resolution IV or more."""
    out = []
    for p in range(0, k):
        gens = generators(k, p)
        if gens is None:
            continue
        res = resolution(k, p)
        if res is not None and res < 4:
            continue
        runs = 2 ** (k - p)
        out.append({"p": p, "runs": runs, "resolution": res,
                    "label": f"full 2^{k}, {runs} runs" if p == 0
                    else f"2^({k}-{p}), {runs} runs, resolution {roman(res)}",
                    "generators": describe_generators(k, gens)})
    default = default_fraction(k)
    for option in out:
        option["default"] = option["p"] == default
    return out


def default_fraction(k):
    """The full design up to FULL_UP_TO factors, else the smallest fraction
    that still has resolution V (every main effect and two-factor
    interaction separate)."""
    if k <= FULL_UP_TO:
        return 0
    best = 0
    for p in range(1, k):
        gens = generators(k, p)
        if gens is not None and resolution(k, p) >= 5:
            best = p
    return best


def describe_generators(k, gens):
    base = k - len(gens)
    return [f"{LETTERS[base + i]}={word}" for i, word in enumerate(gens)]


def design(k, p):
    """The 2^(k-p) corner runs in standard order (the first factor changes
    fastest), each a list of k levels in {-1, +1}."""
    if k > MAX_FACTORS:
        raise ValueError(f"at most {MAX_FACTORS} settings in a factorial design, not {k}")
    gens = generators(k, p)
    if gens is None:
        raise ValueError(f"no standard 2^({k}-{p}) design; choose another fraction")
    base = k - p
    rows = []
    for i in range(2 ** base):
        row = [1 if i >> j & 1 else -1 for j in range(base)]
        for word in gens:
            level = 1
            for letter in word:
                level *= row[LETTERS.index(letter)]
            row.append(level)
        rows.append(row)
    return rows


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _round_half_up(x):
    return int(math.floor(x + 0.5))


def centre_value(low, high, kind=None):
    """The middle of a setting's two levels, and whether it is categorical
    (no middle: the centre runs use the low level).

    Numbers: the log midpoint when both are positive and at least three
    times apart (log-scale settings such as rates and weights), else the
    arithmetic midpoint; whole numbers (and `int` settings) round to the
    nearest whole number. A single layer: the nearest layer to the middle.
    A layer window: the window whose first and last layers are the middle of
    the two windows' (so two halves give the middle half)."""
    if _is_number(low) and _is_number(high):
        a, b = float(low), float(high)
        if a > 0 and b > 0 and max(a, b) / min(a, b) >= 3:
            mid = math.sqrt(a * b)
        else:
            mid = (a + b) / 2
        if kind == "int" or (isinstance(low, int) and isinstance(high, int)):
            return _round_half_up(mid), False
        return float(f"{mid:.3g}"), False
    if isinstance(low, list) and isinstance(high, list) and low and high \
            and all(isinstance(v, int) and not isinstance(v, bool) for v in low + high):
        start = _round_half_up((low[0] + high[0]) / 2)
        end = _round_half_up((low[-1] + high[-1]) / 2)
        if len(low) == 1 and len(high) == 1:
            return [start], False
        return list(range(start, max(start, end) + 1)), False
    return low, True


def code_label(coded, factors):
    """A run's levels as letters in factor order: H high, L low, M middle."""
    return "".join({1: "H", -1: "L", 0: "M"}[coded[f]] for f in factors)


# ------------------------------------------------------------------ analysis

def _t_cdf(t, df):
    """Student's t distribution function, via the regularized incomplete beta."""
    x = df / (df + t * t)
    tail = 0.5 * _betainc(df / 2, 0.5, x)
    return 1 - tail if t > 0 else tail


def _betainc(a, b, x):
    """Regularized incomplete beta I_x(a, b) (Numerical Recipes' continued fraction)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x > (a + 1) / (a + b + 2):
        return 1 - _betainc(b, a, 1 - x)
    f, c, d = 1.0, 1.0, 0.0
    for i in range(400):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1 / d
        c = 1 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1 - c * d) < 1e-12:
            break
    return front * (f - 1) / a


def t_quantile(q, df):
    """Inverse of _t_cdf by bisection (df may be fractional, as in Lenth's m/3)."""
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if _t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def lenth(contrasts):
    """Lenth's pseudo standard error and margins for a list of effects."""
    abs_c = sorted(abs(c) for c in contrasts)
    m = len(abs_c)
    if m < 3:
        return {"m": m, "pse": None, "me": None, "sme": None}
    s0 = 1.5 * _median(abs_c)
    trimmed = [c for c in abs_c if c < 2.5 * s0]
    pse = 1.5 * _median(trimmed) if trimmed else 0.0
    d = m / 3
    gamma = (1 + 0.95 ** (1 / m)) / 2
    return {"m": m, "pse": pse, "df": d, "me": t_quantile(0.975, d) * pse, "sme": t_quantile(gamma, d) * pse}


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return 0.0
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _contrast(column, y):
    plus = [v for c, v in zip(column, y) if v is not None and c > 0]
    minus = [v for c, v in zip(column, y) if v is not None and c < 0]
    if not plus or not minus:
        return None
    return _mean(plus) - _mean(minus)


def _term_name(term, factors):
    return " x ".join(factors[i] for i in term)


def analyse(factors, corners, centres, response):
    """Effects of each factor and each pair on one response.

    factors: the factor names in design order; corners and centres: run
    dicts with "coded" ({factor: -1/0/+1}) and the response under
    `response` (None when missing: failed or unfinished). Corners missing a
    response leave the contrasts slightly unbalanced; the result says how
    many were used."""
    k = len(factors)
    levels = [[run["coded"][f] for f in factors] for run in corners]
    y = [run.get(response) for run in corners]
    n_used = sum(v is not None for v in y)
    out = {"runs": len(corners), "used": n_used, "complete": n_used == len(corners)}
    if n_used < 4:
        out.update(main=[], interactions=[], noise=None, curvature=None)
        return out
    # Every distinct contrast column of the design (all products of
    # factors), with the terms that share it: that is the alias structure,
    # and all of them together feed Lenth's noise estimate.
    columns = {}
    for r in range(1, k + 1):
        for term in itertools.combinations(range(k), r):
            col = tuple(math.prod(row[i] for i in term) for row in levels)
            key = col if col[0] > 0 else tuple(-c for c in col)
            entry = columns.setdefault(key, {"terms": [], "column": col})
            entry["terms"].append(term)
    contrasts = []
    for entry in columns.values():
        effect = _contrast(entry["column"], y)
        entry["effect"] = effect
        if effect is not None:
            contrasts.append(effect)
    noise = lenth(contrasts)
    me, sme = noise.get("me"), noise.get("sme")

    def verdict(effect):
        if effect is None or not me:
            return None
        return "strong" if abs(effect) > sme else "active" if abs(effect) > me else "noise"

    def short_aliases(entry, own):
        return [_term_name(t, factors) for t in entry["terms"] if t != own and len(t) <= 2]

    by_term = {t: e for e in columns.values() for t in e["terms"]}
    main = []
    for i, name in enumerate(factors):
        entry = by_term[(i,)]
        effect = _contrast([row[i] for row in levels], y)
        lo = [v for row, v in zip(levels, y) if v is not None and row[i] < 0]
        hi = [v for row, v in zip(levels, y) if v is not None and row[i] > 0]
        main.append({"factor": name, "effect": effect, "low_mean": _mean(lo), "high_mean": _mean(hi),
                     "aliases": short_aliases(entry, (i,)), "verdict": verdict(effect)})
    interactions, seen = [], set()
    for term in itertools.combinations(range(k), 2):
        entry = by_term[term]
        if id(entry) in seen:
            continue
        seen.add(id(entry))
        col = [row[term[0]] * row[term[1]] for row in levels]
        effect = _contrast(col, y)
        interactions.append({"factors": [factors[term[0]], factors[term[1]]], "effect": effect,
                             "aliases": short_aliases(entry, term), "verdict": verdict(effect)})
    interactions.sort(key=lambda e: -abs(e["effect"] or 0))
    out.update(main=main, interactions=interactions, noise=noise,
               noise_note=None if me else "no noise estimate: most contrasts are exactly 0, so effects are not tested")
    out["curvature"] = curvature([v for v in y if v is not None],
                                 [c.get(response) for c in centres if c.get(response) is not None])
    return out


def curvature(corner_y, centre_y):
    """Centre mean minus corner mean, tested against the centre runs' own
    spread when there are two or more of them."""
    if not corner_y or not centre_y:
        return None
    diff = _mean(centre_y) - _mean(corner_y)
    out = {"centre_mean": _mean(centre_y), "corner_mean": _mean(corner_y), "difference": diff,
           "centre_runs": len(centre_y), "significant": None}
    if len(centre_y) >= 2:
        mean = _mean(centre_y)
        sd = math.sqrt(sum((v - mean) ** 2 for v in centre_y) / (len(centre_y) - 1))
        se = sd * math.sqrt(1 / len(corner_y) + 1 / len(centre_y))
        out["se"] = se
        if se > 0:
            out["t"] = diff / se
            out["significant"] = abs(diff / se) > t_quantile(0.975, len(centre_y) - 1)
        else:
            out["significant"] = diff != 0
    return out
