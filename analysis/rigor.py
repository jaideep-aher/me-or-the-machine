"""Robustness checks for Me or the Machine. Standard library only.

1. Power: the smallest accuracy this sample could reliably detect.
2. Equivalence (TOST): is accuracy inside 50% +/- 10 points?
3. Bayes factor for "pure guessing" against "some ability" (uniform prior).
4. Fleiss' kappa: do the four set-D judges agree beyond chance?
5. Machine baseline: can a simple style detector separate real from twin
   lines when people could not? Nearest-centroid on surface features,
   leave-one-out, with a permutation test.

Run:  python3 analysis/rigor.py   (writes analysis/rigor.json)
"""
import json, math, pathlib, random, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "analysis/summary.json").read_text())
LINES = json.loads((ROOT / "data/lines.json").read_text())["lines"]
RES = json.loads((ROOT / "data/results.json").read_text())


def pmf(n, p):
    return [math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(n + 1)]


def binom_two_sided(k, n, p=0.5):
    f = pmf(n, p)
    return min(1.0, sum(x for x in f if x <= f[k] + 1e-12))


def binom_cdf(k, n, p):
    return sum(pmf(n, p)[: k + 1])


# 1. Power: smallest true accuracy detected 80% of the time at alpha .05, n = 160
def minimum_detectable(n, alpha=.05, power=.8):
    f0 = pmf(n, .5)
    crit = next(k for k in range(n // 2, n + 1) if binom_two_sided(k, n) < alpha)
    for acc in [x / 1000 for x in range(500, 1000)]:
        if 1 - binom_cdf(crit - 1, n, acc) >= power:
            return acc, crit
    return None, crit


# 2. TOST equivalence: H0 accuracy outside [.4, .6]
def tost(k, n, lo=.4, hi=.6):
    p_low = 1 - binom_cdf(k - 1, n, lo)   # P(X >= k | p = lo): evidence acc > lo
    p_high = binom_cdf(k, n, hi)          # P(X <= k | p = hi): evidence acc < hi
    return max(p_low, p_high)


# 3. Bayes factor BF01 = P(data | p = .5) / P(data | p ~ Uniform(0, 1))
def bf01(k, n):
    like0 = math.comb(n, k) * .5**n
    like1 = 1 / (n + 1)  # beta-binomial with a uniform prior
    return like0 / like1


# 4. Fleiss' kappa on set D (4 judges x 20 lines, 2 categories)
def fleiss_kappa():
    d = [r for r in RES if r.get("set") == "D"]
    votes = {}
    for r in d:
        for a in r["answers"]:
            votes.setdefault(a["line"], []).append(a["guessedReal"])
    m = len(d)
    P_i, yes_total = [], 0
    for v in votes.values():
        y = sum(v); n_ = m - y; yes_total += y
        P_i.append((y * (y - 1) + n_ * (n_ - 1)) / (m * (m - 1)))
    Pbar = sum(P_i) / len(P_i)
    py = yes_total / (m * len(votes))
    Pe = py**2 + (1 - py) ** 2
    return (Pbar - Pe) / (1 - Pe), len(votes), m


# 5. Machine baseline
FILLERS = ["like", "you know", "man", "i mean", "basically", "stuff", "honestly", "kind of", "sort of", "bro", "yeah", "okay"]


def features(t):
    low = t.lower()
    words = re.findall(r"[a-z']+", low)
    n = max(len(words), 1)
    bigrams = list(zip(words, words[1:]))
    repeated = sum(1 for i in range(len(bigrams) - 2) if bigrams[i] == bigrams[i + 2] or bigrams[i] == bigrams[i + 1])
    return [
        len(words),
        sum(len(w) for w in words) / n,
        low.count(",") / n,
        sum(low.count(f) for f in FILLERS) / n,
        float(repeated > 0),
        float(t.strip().endswith("?")),
        float(bool(re.match(r"(yeah|no|so|and|but|oh)\b", low))),
        float(" ai" in " " + low or "chatgpt" in low or "app" in words),
        float(any(c.isdigit() for c in t)),
        len(set(words)) / n,
    ]


def nearest_centroid_loo(X, y):
    k = len(X[0]); right = 0
    for i in range(len(X)):
        tr = [j for j in range(len(X)) if j != i]
        mu = [sum(X[j][f] for j in tr) / len(tr) for f in range(k)]
        sd = [math.sqrt(sum((X[j][f] - mu[f]) ** 2 for j in tr) / len(tr)) or 1 for f in range(k)]
        Z = lambda v: [(v[f] - mu[f]) / sd[f] for f in range(k)]
        cents = {}
        for c in (0, 1):
            rows = [Z(X[j]) for j in tr if y[j] == c]
            cents[c] = [sum(r[f] for r in rows) / len(rows) for f in range(k)]
        z = Z(X[i])
        pred = min((0, 1), key=lambda c: sum((z[f] - cents[c][f]) ** 2 for f in range(k)))
        right += pred == y[i]
    return right


def main():
    k, n = S["correct"], S["judgments"]
    mde, crit = minimum_detectable(n)
    kappa, kl, km = fleiss_kappa()
    X = [features(l["text"]) for l in LINES]
    y = [1 if l["source"] == "real" else 0 for l in LINES]
    m_right = nearest_centroid_loo(X, y)
    rng = random.Random(590); perm_ge = 0; reps = 300
    for _ in range(reps):
        yp = y[:]; rng.shuffle(yp)
        perm_ge += nearest_centroid_loo(X, yp) >= m_right
    out = dict(
        power=dict(n=n, critical_correct=crit, min_detectable_accuracy_80pct_power=mde),
        equivalence_tost=dict(bounds=[.4, .6], p=tost(k, n)),
        bayes_factor_01=bf01(k, n),
        fleiss_kappa_set_d=dict(kappa=kappa, lines=kl, judges=km),
        machine_baseline=dict(method="nearest centroid on 10 surface features, leave-one-out",
                              lines=len(X), correct=m_right, accuracy=m_right / len(X),
                              p_vs_chance=binom_two_sided(m_right, len(X)),
                              permutation_p=(perm_ge + 1) / (reps + 1), permutations=reps),
    )
    (ROOT / "analysis/rigor.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
