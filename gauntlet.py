"""
Adversarial gauntlet: runs `python -m evals` for every (candidate, opponent)
pair as separate subprocesses (in parallel), parses the evals table and
writes a combined CSV and a markdown summary.

    .venv/Scripts/python.exe gauntlet.py --models model:Model mybot:Model \
        --deals 100 --seed 11 [--jobs 8] [--out gauntlet_out] [--tag name]
        [--opponents tight equity ... (default: the full gauntlet)]

Run from the repo root (make_adv.py must have created adv_*.pkl / v4.pkl).

Pairing: evals deals deck d of a match from random.Random(f"{seed}:{d}")
(arena/match.py _deck / _play_duplicate), independent of player names, and
seeds each dummy from sha256(f"{seed}:{name}") (arena/match.py _build), so
the same --seed gives every candidate the same decks and the same dummy RNG
streams: comparisons between candidates at one seed are paired.

Seeds: dev 11, 12. HOLDOUT 777 (only for the final pick).

Self-matches (bb 0.0 +- 0.0) are excluded from the aggregate.
Aggregate = unweighted mean of per-opponent bb/100 (opponents are fixed
strata); SE_agg = sqrt(sum SE_i^2) / k with SE_i = ci95_i / 1.96.
"""

import argparse
import csv
import glob
import math
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.abspath(__file__))
DUMMIES = ["tight", "equity", "call", "shove", "random"]
ADVS = ["adv_station.pkl", "adv_maniac.pkl", "adv_jammer.pkl",
        "adv_nit3bet.pkl", "adv_smallball.pkl"]
HOLDOUT_SEED = 777

ROW = re.compile(
    r"^(?P<label>\S+)\s+(?P<bb>[+-]?\d+(?:\.\d+)?)\s+±\s+(?P<ci>\S+)\s+"
    r"(?P<verdict>ahead|behind|unclear)\s+(?P<hands>\d+)\s+"
    r"(?P<faults>\d+)\s+(?P<slow>[\d.]+)s\s*$"
)


def default_opponents():
    opps = list(DUMMIES) + [a for a in ADVS if os.path.exists(os.path.join(ROOT, a))]
    if os.path.exists(os.path.join(ROOT, "v4.pkl")):
        opps.append("v4.pkl")
    return opps


def run_one(model, opponent, deals, seed, timeout):
    cmd = [sys.executable, "-m", "evals", "--model", model, "--opponents",
           opponent, "--deals", str(deals), "--seed", str(seed)]
    if timeout is not None:
        cmd += ["--timeout", str(timeout)]
    t0 = time.time()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)
    wall = time.time() - t0
    row = {"model": model, "opponent": os.path.splitext(os.path.basename(opponent))[0],
           "deals": deals, "seed": seed, "bb100": None, "ci95": None,
           "se": None, "verdict": "ERROR", "hands": 0, "faults": None,
           "slowest_s": None, "wall_s": round(wall, 1), "first_fault": ""}
    lines = proc.stdout.splitlines()
    for i, line in enumerate(lines):
        m = ROW.match(line.strip())
        if m:
            ci = float(m["ci"]) if m["ci"] not in ("inf", "nan") else math.inf
            row.update(bb100=float(m["bb"]), ci95=ci, se=ci / 1.96,
                       verdict=m["verdict"], hands=int(m["hands"]),
                       faults=int(m["faults"]), slowest_s=float(m["slow"]))
            if i + 1 < len(lines) and "first fault" in lines[i + 1]:
                row["first_fault"] = lines[i + 1].split(":", 1)[1].strip()
            break
    if row["bb100"] is None:
        row["first_fault"] = ("evals failed: " + (proc.stderr or proc.stdout)[-500:]).replace("\n", " | ")
    return row


def summarise(rows, model):
    # ci95 == 0 with bb == 0 is a deterministic self-match (e.g. v4 vs
    # v4.pkl): exactly zero by symmetry, so it is left out of the aggregate.
    mine = [r for r in rows if r["model"] == model and r["bb100"] is not None
            and not (r["ci95"] == 0 and r["bb100"] == 0)]
    k = len(mine)
    if k == 0:
        return None
    mean = sum(r["bb100"] for r in mine) / k
    se = math.sqrt(sum(r["se"] ** 2 for r in mine)) / k
    worst = min(mine, key=lambda r: r["bb100"])
    return {
        "model": model, "k": k, "mean": mean, "ci95": 1.96 * se,
        "worst": f'{worst["opponent"]} ({worst["bb100"]:+.1f})',
        "faults": sum(r["faults"] for r in mine),
        "max_latency": max(r["slowest_s"] for r in mine),
        "errors": sum(1 for r in rows if r["model"] == model and r["bb100"] is None),
        "wall": sum(r["wall_s"] for r in rows if r["model"] == model),
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", required=True, help="module:Class ...")
    p.add_argument("--opponents", nargs="+", default=None)
    p.add_argument("--deals", type=int, default=100)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    p.add_argument("--timeout", type=float, default=None, help="per-move, passed to evals")
    p.add_argument("--out", default="gauntlet_out")
    p.add_argument("--tag", default=None)
    p.add_argument("--allow-holdout", action="store_true")
    a = p.parse_args(argv)
    if a.seed == HOLDOUT_SEED and not a.allow_holdout:
        p.error(f"seed {HOLDOUT_SEED} is the HOLDOUT; pass --allow-holdout for the final pick only")
    opps = a.opponents or default_opponents()
    jobs = [(m, o) for m in a.models for o in opps]
    t0 = time.time()
    with ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(run_one, m, o, a.deals, a.seed, a.timeout) for m, o in jobs]
        rows = []
        for f in futs:
            r = f.result()
            rows.append(r)
            print(f'{r["model"]:<24} {r["opponent"]:<14} {r["bb100"] if r["bb100"] is not None else "ERR":>8} '
                  f'± {r["ci95"]}  faults={r["faults"]} slow={r["slowest_s"]}s wall={r["wall_s"]}s', flush=True)
    total_wall = time.time() - t0

    os.makedirs(os.path.join(ROOT, a.out), exist_ok=True)
    tag = a.tag or f"s{a.seed}_d{a.deals}_{int(time.time())}"
    csv_path = os.path.join(ROOT, a.out, f"gauntlet_{tag}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    names = [os.path.splitext(os.path.basename(o))[0] for o in opps]
    md = [f"# Gauntlet seed={a.seed} deals={a.deals} (x2 seats per deal)", "",
          "bb/100 ± 95% CI per opponent (evals duplicate scoring).", ""]
    md.append("| model | " + " | ".join(names) + " |")
    md.append("|---|" + "---|" * len(names))
    for m in a.models:
        cells = []
        for n in names:
            r = next((r for r in rows if r["model"] == m and r["opponent"] == n), None)
            if r is None or r["bb100"] is None:
                cells.append("ERR")
            else:
                flag = f' F{r["faults"]}' if r["faults"] else ""
                cells.append(f'{r["bb100"]:+.1f} ± {r["ci95"]:.1f}{flag}')
        md.append(f"| {m} | " + " | ".join(cells) + " |")
    md += ["", "| model | mean bb/100 | ± 95% CI | worst matchup | faults | max latency s | errors | cpu-wall s |",
           "|---|---|---|---|---|---|---|---|"]
    for m in a.models:
        s = summarise(rows, m)
        if s is None:
            md.append(f"| {m} | ERR | | | | | | |")
            continue
        md.append(f'| {m} | {s["mean"]:+.1f} | {s["ci95"]:.1f} | {s["worst"]} | {s["faults"]} | '
                  f'{s["max_latency"]:.2f} | {s["errors"]} | {s["wall"]:.0f} |')
    if len(a.models) > 1:
        base = a.models[0]
        md += ["", f"Difference vs {base} (same seed => same decks; CI below is the "
               "conservative unpaired one, sqrt(SE_a^2+SE_b^2)):", "",
               "| model | mean diff | ± 95% CI (unpaired, conservative) |", "|---|---|---|"]
        sb = summarise(rows, base)
        for m in a.models[1:]:
            s = summarise(rows, m)
            if s and sb:
                d = s["mean"] - sb["mean"]
                ci = math.sqrt(s["ci95"] ** 2 + sb["ci95"] ** 2)
                md.append(f"| {m} | {d:+.1f} | {ci:.1f} |")
    errs = [r for r in rows if r["first_fault"]]
    if errs:
        md += ["", "## Faults / errors", ""]
        for r in errs:
            md.append(f'- {r["model"]} vs {r["opponent"]}: {r["first_fault"]}')
    md += ["", f"Total wall time {total_wall:.0f}s with --jobs {a.jobs}."]
    md_path = os.path.join(ROOT, a.out, f"gauntlet_{tag}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nwrote {csv_path}\nwrote {md_path}")


if __name__ == "__main__":
    main()
