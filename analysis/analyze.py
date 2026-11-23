"""Me or the Machine: analysis of the blind test.

Reads data/lines.json and data/results.json, prints accuracy, the twin pass
rate, an exact binomial test against chance (50%) and Wilson 95% intervals,
and writes analysis/summary.json. Standard library only.

Run:  python3 analysis/analyze.py
"""
import json, math, pathlib

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


def main():
    results = json.loads((ROOT / "data/results.json").read_text())
    rows, tot = [], dict(n=0, ok=0, real=0, real_ok=0, twin=0, twin_pass=0, said_real=0)
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
    lo, hi = wilson(tot["ok"], tot["n"])
    summary = dict(
        participants=len(rows), judgments=tot["n"], correct=tot["ok"],
        accuracy=tot["ok"] / tot["n"], accuracy_ci95=[lo, hi],
        p_vs_chance=binom_two_sided(tot["ok"], tot["n"]),
        real_called_real=tot["real_ok"] / tot["real"], real_counts=[tot["real_ok"], tot["real"]],
        twin_called_real=tot["twin_pass"] / tot["twin"], twin_counts=[tot["twin_pass"], tot["twin"]],
        said_real_rate=tot["said_real"] / tot["n"], per_participant=rows,
    )
    (ROOT / "analysis/summary.json").write_text(json.dumps(summary, indent=1))
    print(f"{'who':4} {'set':3} {'right':>7} {'real ok':>8} {'twin passed':>12}")
    for r in rows:
        print(f"{r['participant']:4} {r['set']:3} {r['correct']:>3}/{r['n']:<3} {r['real_recognised']:>4}/{r['real_lines']:<3} {r['twin_passed']:>7}/{r['twin_lines']:<3}")
    print(f"\nAll: {tot['ok']}/{tot['n']} right = {summary['accuracy']:.1%}  (95% CI {lo:.1%} to {hi:.1%}, p vs 50% = {summary['p_vs_chance']:.2f})")
    print(f"Real lines called real: {tot['real_ok']}/{tot['real']} = {summary['real_called_real']:.1%}")
    print(f"Twin lines called real: {tot['twin_pass']}/{tot['twin']} = {summary['twin_called_real']:.1%}")


if __name__ == "__main__":
    main()
