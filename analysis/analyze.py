"""Me or the Machine: analysis of the blind test.

Reads data/lines.json and data/results.json, prints accuracy, the twin pass
rate, an exact binomial test against chance (50%) and Wilson 95% intervals,
and writes analysis/summary.json. Standard library only.

Run:  python3 analysis/analyze.py
"""
import json, math, pathlib, random
from statistics import NormalDist, mean, stdev

ROOT = pathlib.Path(__file__).resolve().parent.parent


def wilson(k, n, z=1.96):
    """Wilson score 95% interval for a proportion k/n."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def binom_two_sided(k, n, p=0.5):
    """Exact two-sided binomial p-value: sum of outcomes as or less likely than k."""
    pmf = [math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(x for x in pmf if x <= pmf[k] + 1e-12))


def sign_test(above, below):
    """Two-sided sign test: judges above vs below 50%, ties dropped."""
    n = above + below
    return binom_two_sided(min(above, below), n) if n else 1.0


def t_test_vs_half(xs):
    """One-sample t statistic of per-judge accuracy against 0.5 and a normal-approximation p."""
    if len(xs) < 2 or stdev(xs) == 0:
        return 0.0, 1.0
    t = (mean(xs) - 0.5) / (stdev(xs) / math.sqrt(len(xs)))
    return t, 2 * (1 - NormalDist().cdf(abs(t)))


def cluster_bootstrap(judges, reps=10000, seed=590):
    """95% interval for pooled accuracy, resampling whole judges (keeps their answers together)."""
    rng = random.Random(seed)
    out = []
    for _ in range(reps):
        pick = [judges[rng.randrange(len(judges))] for _ in judges]
        out.append(sum(k for k, n in pick) / sum(n for k, n in pick))
    out.sort()
    return out[int(.025 * reps)], out[int(.975 * reps) - 1]


def main():
    results = json.loads((ROOT / "data/results.json").read_text())
    rows, tot = [], dict(n=0, ok=0, real=0, real_ok=0, twin=0, twin_pass=0, said_real=0)
    score_only = [r for r in results if r.get("score_only")]
    results = [r for r in results if not r.get("score_only")]
    for r in results:
        a = r["answers"]
        n = len(a)
        ok = sum(x["real"] == x["guessedReal"] for x in a)
        real = sum(x["real"] for x in a)
        real_ok = sum(x["real"] and x["guessedReal"] for x in a)
        twin = n - real
        twin_pass = sum((not x["real"]) and x["guessedReal"] for x in a)
        said = sum(x["guessedReal"] for x in a)
        rows.append(dict(participant=r["participant"], relationship=r["relationship"], set=r["set"],
                         attempt=r["attempt"], n=n, correct=ok, real_lines=real, real_recognised=real_ok,
                         twin_lines=twin, twin_passed=twin_pass, said_real=said))
        for k, v in dict(n=n, ok=ok, real=real, real_ok=real_ok, twin=twin, twin_pass=twin_pass, said_real=said).items():
            tot[k] += v
    # Set D: several judges saw the same 20 lines. Unanimity and majority vote.
    d = [r for r in results if r["set"] == "D"]
    votes = {}
    for r in d:
        for x in r["answers"]:
            votes.setdefault(x["line"], [x["real"], []])[1].append(x["guessedReal"])
    unanimous = [l for l, (_, g) in votes.items() if len(set(g)) == 1]
    maj_right = maj_tie = 0
    for l, (real, g) in votes.items():
        yes = sum(g)
        if yes * 2 == len(g):
            maj_tie += 1
        elif (yes * 2 > len(g)) == real:
            maj_right += 1
    set_d = dict(judges=len(d), lines=len(votes), unanimous=len(unanimous),
                 unanimous_wrong=sum((votes[l][1][0] != votes[l][0]) for l in unanimous),
                 majority_right=maj_right, majority_tied=maj_tie)
    # Per-line judgments plus score-only rounds (no line detail) for overall accuracy.
    for r in score_only:
        rows.append(dict(participant=r["participant"], relationship=r["relationship"], set=r["set"],
                         attempt=r["attempt"], n=r["n"], correct=r["correct"], score_only=True))
    all_n = tot["n"] + sum(r["n"] for r in score_only)
    all_ok = tot["ok"] + sum(r["correct"] for r in score_only)
    alo, ahi = wilson(all_ok, all_n)
    lo, hi = wilson(tot["ok"], tot["n"])
    # Judge-level view: one accuracy per judge, so no judge counts more than once.
    saved_j = [(r["correct"], r["n"]) for r in rows if not r.get("score_only")]
    all_j = [(r["correct"], r["n"]) for r in rows]
    def judge_level(js):
        accs = [k / n for k, n in js]
        t, p = t_test_vs_half(accs)
        lo_b, hi_b = cluster_bootstrap(js)
        return dict(judges=len(js), mean_accuracy=mean(accs), above=sum(a > .5 for a in accs),
                    below=sum(a < .5 for a in accs), at_half=sum(a == .5 for a in accs),
                    sign_test_p=sign_test(sum(a > .5 for a in accs), sum(a < .5 for a in accs)),
                    t=t, t_p=p, cluster_bootstrap_ci95=[lo_b, hi_b])
    # Signal detection: "real" is the signal; a hit is a real line called real.
    z = NormalDist().inv_cdf
    H, F = tot["real_ok"] / tot["real"], tot["twin_pass"] / tot["twin"]
    sdt = dict(hit_rate=H, false_alarm_rate=F, d_prime=z(H) - z(F), criterion_c=-(z(H) + z(F)) / 2)
    # Item analysis: how often each line was called "him", for lines seen by 2 or more judges.
    lines = {l["id"]: l for l in json.loads((ROOT / "data/lines.json").read_text())["lines"]}
    seen = {}
    for r in results:
        for x in r["answers"]:
            seen.setdefault(x["line"], []).append(x["guessedReal"])
    items = sorted(([dict(line=l, source=lines[l]["source"], text=lines[l]["text"], judges=len(g),
                          called_him=sum(g)) for l, g in seen.items() if len(g) >= 2]),
                   key=lambda d: (-d["called_him"] / d["judges"], d["line"]))
    summary = dict(
        judge_level_saved=judge_level(saved_j), judge_level_all=judge_level(all_j),
        signal_detection=sdt, items_seen_by_2_or_more=items,
        all_participants=len(rows), all_judgments=all_n, all_correct=all_ok,
        all_accuracy=all_ok / all_n, all_accuracy_ci95=[alo, ahi], all_p_vs_chance=binom_two_sided(all_ok, all_n),
        set_d=set_d,
        participants=len(results), judgments=tot["n"], correct=tot["ok"],
        accuracy=tot["ok"] / tot["n"], accuracy_ci95=[lo, hi],
        p_vs_chance=binom_two_sided(tot["ok"], tot["n"]),
        real_called_real=tot["real_ok"] / tot["real"], real_counts=[tot["real_ok"], tot["real"]],
        twin_called_real=tot["twin_pass"] / tot["twin"], twin_counts=[tot["twin_pass"], tot["twin"]],
        said_real_rate=tot["said_real"] / tot["n"], per_participant=rows,
    )
    (ROOT / "analysis/summary.json").write_text(json.dumps(summary, indent=1))
    print(f"{'who':4} {'set':3} {'right':>7} {'real ok':>8} {'twin passed':>12}")
    for r in rows:
        if r.get("score_only"):
            print(f"{r['participant']:4} {'30':3} {r['correct']:>3}/{r['n']:<3}   (score only)")
        else:
            print(f"{r['participant']:4} {r['set']:3} {r['correct']:>3}/{r['n']:<3} {r['real_recognised']:>4}/{r['real_lines']:<3} {r['twin_passed']:>7}/{r['twin_lines']:<3}")
    print(f"\nEveryone: {all_ok}/{all_n} right = {all_ok/all_n:.1%}  (95% CI {alo:.1%} to {ahi:.1%}, p vs 50% = {summary['all_p_vs_chance']:.3f})")
    print(f"Set D: {set_d}")
    for k in ("judge_level_saved", "judge_level_all"):
        j = summary[k]
        print(f"{k}: mean {j['mean_accuracy']:.1%}, {j['above']} above / {j['below']} below / {j['at_half']} at 50%, sign p = {j['sign_test_p']:.2f}, t p = {j['t_p']:.2f}, judge bootstrap 95% {j['cluster_bootstrap_ci95'][0]:.1%} to {j['cluster_bootstrap_ci95'][1]:.1%}")
    print(f"Signal detection: d' = {sdt['d_prime']:.2f}, c = {sdt['criterion_c']:.2f} (negative c = leans towards 'him')")
    print(f"Lines seen by 2+ judges: {len(items)}; most believed: {items[0]['source']} line {items[0]['line']} ({items[0]['called_him']}/{items[0]['judges']})")
    print(f"Per-line rounds only: {tot['ok']}/{tot['n']} right = {summary['accuracy']:.1%}  (95% CI {lo:.1%} to {hi:.1%}, p vs 50% = {summary['p_vs_chance']:.2f})")
    print(f"Real lines called real: {tot['real_ok']}/{tot['real']} = {summary['real_called_real']:.1%}")
    print(f"Twin lines called real: {tot['twin_pass']}/{tot['twin']} = {summary['twin_called_real']:.1%}")


if __name__ == "__main__":
    main()
