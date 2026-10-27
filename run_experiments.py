#!/usr/bin/env python3
"""
run_experiments.py -- reproduces every number reported in the paper.

Experiments
  E1  14 constructed (synthetic) events through the two domain adapters,
      compared against (a) outcomes declared in PATTERN below, written from
      the design before any solver run, and (b) an independent Python
      reference implementation of the specification (oracle).
  E2  Exhaustive sweep of the governance core: all 16 (criticality,
      urgency) pairs x 101 confidence scores x 36 threshold settings,
      compared against the oracle; also checks that the matrix is monotone.
  E3  Policy-change test: ONE line of priority_matrix.lp (theta_p 3 -> 4)
      is edited in a scratch copy; file hashes prove nothing else changed.
  E4  Size metrics (statement counts via the clingo parser).
  E5  Fault injection: four deliberately broken variants of the core, run
      against the 14 events and against the exhaustive sweep.
  E6  Decision time (machine dependent; written to results/timing_latest.json).
  E7  Matrix-cell test: a safety-critical event with ample time is
      autonomous under the shipped matrix and escalates after changing the
      single fact matrix(4,1,2) to matrix(4,1,3).

Requires: pip install clingo   (tested with 5.8.2)
"""
import hashlib
import itertools
import json
import shutil
import tempfile
from pathlib import Path

import clingo
from clingo import ast

ROOT = Path(__file__).resolve().parent
STRICT = True   # fail on any clingo message; relaxed only for fault injection
CORE = ["core/governance_core.lp", "core/priority_matrix.lp"]
DOMAINS = {
    "cobot": ("adapters/cobot_adapter.lp",
              "test_events/cobot/cobot_events.lp", "CB", "cobot_reallocation"),
    "scheduling": ("adapters/scheduling_adapter.lp",
                   "test_events/scheduling/scheduling_events.lp", "SS",
                   "sustainable_scheduling"),
}

# ---------------------------------------------------------------------------
# Pre-declared expectations (tier, set of escalation reasons). Written from
# the test design, independently of any solver output.
#   LC = low_confidence (R2), HP = high_priority (R3)
# ---------------------------------------------------------------------------
PATTERN = {  # event number -> (tier, reasons) under theta_k=60, d=1, p=3
    1: (1, set()),
    2: (2, set()),
    3: (3, {"high_priority"}),
    4: (4, {"high_priority"}),
    5: (2, {"low_confidence"}),
    6: (1, set()),
    7: (3, {"low_confidence", "high_priority"}),
}
# After raising theta_p from 3 to 4
PATTERN_P4 = {
    1: (1, set()),
    2: (2, set()),
    3: (3, set()),                      # Priority no longer escalated
    4: (4, {"high_priority"}),
    5: (2, {"low_confidence"}),
    6: (1, set()),
    7: (3, {"low_confidence"}),         # R3 silent, R2 still fires
}

# ---------------------------------------------------------------------------
# Independent reference implementation (oracle). Deliberately does not use
# ASP and does not read the .lp matrix: it has its own copy of Table 1.
# ---------------------------------------------------------------------------
MATRIX = [[1, 1, 2, 2],
          [1, 2, 3, 3],
          [2, 3, 3, 4],
          [2, 3, 4, 4]]          # MATRIX[C-1][U-1]


def oracle_decide(c, u, k, tk=60, td=1, tp=3):
    t = MATRIX[c - 1][u - 1]
    reasons = set()
    if k < tk and t > td:
        reasons.add("low_confidence")
    if t >= tp:
        reasons.add("high_priority")
    return t, reasons


def oracle_cobot(raw):
    c = {"safety_critical": 4, "safety_adjacent": 3,
         "process_disruption": 2, "non_safety": 1}[raw["task_class"]]
    b = raw["cycle_budget"]
    u = 4 if b < 5 else 3 if b < 30 else 2 if b < 120 else 1
    return c, u, raw["detection_certainty"]


def oracle_scheduling(raw):
    c = {"hard_contractual_cap": 4, "regulatory_threshold": 3,
         "soft_target": 2, "advisory": 1}[raw["breach_type"]]
    s = raw["time_to_violation"]
    u = 4 if s < 60 else 3 if s < 900 else 2 if s < 3600 else 1
    return c, u, raw["data_quality_score"]


ORACLE = {"cobot": oracle_cobot, "scheduling": oracle_scheduling}


# ---------------------------------------------------------------------------
# Solver helpers
# ---------------------------------------------------------------------------
def solve(files, root=ROOT, consts=None, text=""):
    args = ["0"]
    for k, v in (consts or {}).items():
        args += ["-c", f"{k}={v}"]
    msgs = []
    ctl = clingo.Control(args, logger=lambda code, m: msgs.append(m))
    for f in files:
        ctl.load(str(root / f))
    if text:
        ctl.add("base", [], text)
    ctl.ground([("base", [])])
    models = []
    ctl.solve(on_model=lambda m: models.append(
        [(s.name, [str(a) for a in s.arguments]) for s in m.symbols(atoms=True)]))
    assert not (STRICT and msgs), f"clingo messages: {msgs}"
    assert len(models) == 1, f"expected exactly one answer set, got {len(models)}"
    return models[0]


def records(model):
    """Group atoms by event id -> audit record (raw atoms + derived atoms)."""
    rec = {}
    for name, args in model:
        if name in ("matrix",) or not args:
            continue
        e = args[0]
        r = rec.setdefault(e, {"reasons": set(), "autonomous": False, "raw": {}})
        if name == "escalate":
            r["reasons"].add(args[1])
        elif name == "autonomous":
            r["autonomous"] = True
        elif name in ("criticality", "urgency", "confidence", "priority"):
            r[name] = int(args[1])
        elif name == "source":
            r["source"] = args[1]
        elif name == "event":
            pass
        else:
            v = args[1]
            r["raw"][name] = int(v) if v.lstrip("-").isdigit() else v
    return rec


def eid(e):  # cb03 -> CB-03
    return f"{e[:2].upper()}-{e[2:]}"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def count_statements(files, root=ROOT):
    n = 0
    for f in files:
        stmts = []
        ast.parse_files([str(root / f)], stmts.append)
        n += sum(1 for s in stmts
                 if s.ast_type not in (ast.ASTType.Program, ast.ASTType.Comment))
    return n


# ---------------------------------------------------------------------------
# E1  Domain events through adapters
# ---------------------------------------------------------------------------
def run_events(root=ROOT, consts=None, pattern=PATTERN, tp_in_force=None):
    out = {}
    for dom, (adp, evs, pref, src) in DOMAINS.items():
        rec = records(solve(CORE + [adp, evs], root, consts))
        tk = (consts or {}).get("theta_k", 60)
        tp = tp_in_force if tp_in_force is not None else (consts or {}).get("theta_p", 3)
        rows = []
        for e in sorted(rec):
            n = int(e[2:])
            r = rec[e]
            exp_t, exp_r = pattern[n]
            c, u, k = ORACLE[dom](r["raw"])
            o_t, o_r = oracle_decide(c, u, k, tk=tk, tp=tp)
            solver_auto = r["autonomous"]
            complete = (all(x in r for x in ("criticality", "urgency", "confidence",
                                             "priority", "source"))
                        and r["source"] == src
                        and (solver_auto or len(r["reasons"]) > 0)
                        and not (solver_auto and r["reasons"]))
            rows.append({
                "id": eid(e), "C": r["criticality"], "U": r["urgency"],
                "K": r["confidence"], "tier": r["priority"],
                "reasons": sorted(r["reasons"]), "autonomous": solver_auto,
                "matches_expected": (r["priority"] == exp_t and r["reasons"] == exp_r
                                     and solver_auto == (not exp_r)),
                "matches_oracle": (r["priority"] == o_t and r["reasons"] == o_r
                                   and solver_auto == (not o_r)
                                   and (c, u) == (r["criticality"], r["urgency"])),
                "audit_complete": complete,
            })
        out[dom] = rows
    return out


# ---------------------------------------------------------------------------
# E2  Exhaustive sweep of the core
# ---------------------------------------------------------------------------
def run_sweep(root=ROOT):
    facts = []
    for c, u, k in itertools.product(range(1, 5), range(1, 5), range(0, 101)):
        e = f"x_{c}_{u}_{k}"
        facts.append(f"event({e}). criticality({e},{c}). urgency({e},{u}). "
                     f"confidence({e},{k}). source({e},sweep).")
    text = "\n".join(facts)
    n_events = 16 * 101
    configs = list(itertools.product((40, 60, 80), (0, 1, 2, 3), (2, 3, 4)))
    decisions = mismatches = 0
    for tk, td, tp in configs:
        rec = records(solve(CORE, root=root, consts={"theta_k": tk, "theta_d": td,
                                                      "theta_p": tp}, text=text))
        assert len(rec) == n_events
        for e, r in rec.items():
            _, c, u, k = e.split("_")
            o_t, o_r = oracle_decide(int(c), int(u), int(k), tk, td, tp)
            decisions += 1
            if r["priority"] != o_t or r["reasons"] != o_r or \
               r["autonomous"] != (not o_r):
                mismatches += 1
    mono = all(MATRIX[i][j] <= MATRIX[i + 1][j] for i in range(3) for j in range(4)) \
        and all(MATRIX[i][j] <= MATRIX[i][j + 1] for i in range(4) for j in range(3))
    return {"events_per_config": n_events, "configs": len(configs),
            "decisions": decisions, "mismatches": mismatches,
            "matrix_monotone": mono}


# ---------------------------------------------------------------------------
# E3  Policy change: edit ONE line in a scratch copy, hash everything
# ---------------------------------------------------------------------------
def run_policy_change():
    tmp = Path(tempfile.mkdtemp())
    for sub in ("core", "adapters", "test_events"):
        shutil.copytree(ROOT / sub, tmp / sub)
    files = [p.relative_to(tmp) for p in tmp.rglob("*.lp")]
    before = {str(f): sha(tmp / f) for f in files}
    target = tmp / "core/priority_matrix.lp"
    lines = target.read_text().splitlines()
    idx = [i for i, l in enumerate(lines) if l.startswith("#const theta_p")]
    assert len(idx) == 1
    lines[idx[0]] = "#const theta_p = 4."
    target.write_text("\n".join(lines) + "\n")
    after = {str(f): sha(tmp / f) for f in files}
    changed = [f for f in before if before[f] != after[f]]
    orig = (ROOT / "core/priority_matrix.lp").read_text().splitlines()
    new = target.read_text().splitlines()
    lines_changed = sum(1 for a, b in zip(orig, new) if a != b) + abs(len(orig) - len(new))
    res = run_events(root=tmp, pattern=PATTERN_P4, tp_in_force=4)
    shutil.rmtree(tmp)
    return {"files_changed": changed, "lines_changed": lines_changed, "events": res}



# ---------------------------------------------------------------------------
# E5  Fault injection: can the test suites actually detect a broken core?
# ---------------------------------------------------------------------------
MUTANTS = {
    "M1 drop dismissal floor (R2 ignores theta_d)":
        ("priority(E, T), T > theta_d.", "priority(E, T)."),
    "M2 R3 uses > instead of >=":
        ("T >= theta_p.", "T > theta_p."),
    "M3 R4 ignores escalation":
        ("not escalate(E, _).", "not escalate(E, never)."),
    "M4 R2 uses <= instead of <":
        ("K < theta_k,", "K <= theta_k,"),
}


def run_mutants():
    global STRICT
    STRICT = False
    out = {}
    for name, (old, new) in MUTANTS.items():
        tmp = Path(tempfile.mkdtemp())
        for sub in ("core", "adapters", "test_events"):
            shutil.copytree(ROOT / sub, tmp / sub)
        core = tmp / "core/governance_core.lp"
        txt = core.read_text()
        assert txt.count(old) == 1, (f"fault injection {name!r} cannot be applied: core/governance_core.lp "
                                     "no longer contains the expected text, so the core was modified")
        core.write_text(txt.replace(old, new))
        ev = run_events(root=tmp)
        by_events = any(not (r["matches_expected"] and r["matches_oracle"]
                             and r["audit_complete"])
                        for rows in ev.values() for r in rows)
        by_sweep = run_sweep(root=tmp)["mismatches"] > 0
        out[name] = {"detected_by_14_events": by_events,
                     "detected_by_sweep": by_sweep}
        shutil.rmtree(tmp)
    STRICT = True
    return out


# ---------------------------------------------------------------------------
# E7  One matrix fact decides whether a safety-critical event with ample time
#     runs autonomously (backs the paper's remark on the C4/U1 cell)
# ---------------------------------------------------------------------------
def run_matrix_cell():
    facts = ("event(x). task_class(x,safety_critical). "
             "cycle_budget(x,200). detection_certainty(x,90).")
    tmp = Path(tempfile.mkdtemp())
    for sub in ("core", "adapters"):
        shutil.copytree(ROOT / sub, tmp / sub)

    def decide():
        r = records(solve(CORE + ["adapters/cobot_adapter.lp"], tmp, text=facts))["x"]
        return {"tier": r["priority"], "autonomous": r["autonomous"],
                "reasons": sorted(r["reasons"])}

    before = decide()
    target = tmp / "core/priority_matrix.lp"
    old = target.read_text()
    assert old.count("matrix(4,1,2).") == 1, "E7 expects the shipped matrix fact matrix(4,1,2)."
    target.write_text(old.replace("matrix(4,1,2).", "matrix(4,1,3)."))
    after = decide()
    lines_changed = sum(1 for a, b in zip(old.splitlines(), target.read_text().splitlines()) if a != b)
    shutil.rmtree(tmp)
    return {"before": before, "after": after, "lines_changed": lines_changed,
            "as_expected": (before == {"tier": 2, "autonomous": True, "reasons": []}
                            and after == {"tier": 3, "autonomous": False,
                                          "reasons": ["high_priority"]}
                            and lines_changed == 1)}



def write_event_table_rows(e1):
    """LaTeX body of the paper's event table, taken straight from solver output.
    Cobot events on the left, scheduling events on the right (same row = same
    behaviour under test), so the table needs only seven rows."""
    tiers = {1: "R", 2: "E", 3: "P", 4: "X"}

    def label(x):
        if x["autonomous"]:
            return "A"
        r = set(x["reasons"])
        if r == {"low_confidence", "high_priority"}:
            return "E-LC+HP"
        return "E-LC" if r == {"low_confidence"} else "E-HP"

    def cells(x):
        return f"{x['id']} & {x['C']} & {x['U']} & {x['K']} & {tiers[x['tier']]} & {label(x)}"

    head = "\\textbf{Event} & $C$ & $U$ & $K$ & $T$ & \\textbf{Outcome}"
    out = [
        "\\multicolumn{6}{|c||}{\\textit{Cobot Task Reallocation}} & "
        "\\multicolumn{6}{c|}{\\textit{Sustainable Scheduling}} \\\\ \\hline",
        f"{head} & {head} \\\\ \\hline",
    ]
    for left, right in zip(e1["cobot"], e1["scheduling"]):
        out.append(f"{cells(left)} & {cells(right)} \\\\ \\hline")
    (ROOT / "results/events_table_rows.tex").write_text("\n".join(out) + "\n")


# ---------------------------------------------------------------------------
# E6  Decision time (kept out of results.json because it varies from run to run)
# ---------------------------------------------------------------------------
def run_timing(reps=100, warmup=20):
    """Wall-clock time of one complete governance decision, measured through
    the Python API: new solver instance, load core + matrix + adapter text,
    add the event facts, ground, solve. It therefore includes solver start-up
    and grounding of the whole program, and excludes data extraction and
    actuation (Layer 1)."""
    import platform
    import statistics
    import time
    core_txt = "\n".join((ROOT / f).read_text() for f in CORE)
    samples = []
    for dom, (adp, evs, pref, src) in DOMAINS.items():
        base = core_txt + "\n" + (ROOT / adp).read_text()
        lines = [l.strip() for l in (ROOT / evs).read_text().splitlines()
                 if l.strip().startswith("event(")]
        for line in lines:
            for i in range(warmup + reps):
                t0 = time.perf_counter()
                ctl = clingo.Control(["0"], logger=lambda c, m: None)
                ctl.add("base", [], base + "\n" + line)
                ctl.ground([("base", [])])
                ctl.solve(on_model=lambda m: None)
                dt = (time.perf_counter() - t0) * 1000.0
                if i >= warmup:
                    samples.append(dt)
    samples.sort()
    cpu = "unknown"
    try:
        for l in open("/proc/cpuinfo"):
            if l.startswith("model name"):
                cpu = l.split(":", 1)[1].strip()
                break
    except OSError:
        cpu = platform.processor() or "unknown"
    q = lambda f: samples[min(len(samples) - 1, int(f * len(samples)))]
    return {"runs": len(samples), "median_ms": round(statistics.median(samples), 2),
            "p95_ms": round(q(0.95), 2), "max_ms": round(samples[-1], 2),
            "cpu": cpu, "python": platform.python_version(),
            "clingo": clingo.__version__, "os": platform.platform()}


# ---------------------------------------------------------------------------
def main():
    e1 = run_events()
    e2 = run_sweep()
    e3 = run_policy_change()
    e5 = run_mutants()
    e7 = run_matrix_cell()
    core_n = count_statements(CORE)
    core_rules = count_statements(["core/governance_core.lp"])
    adp_n = {d: count_statements([v[0]]) for d, v in DOMAINS.items()}
    sizes = {"core_total": core_n, "core_rules": core_rules, "adapters": adp_n}
    result = {"clingo_version": clingo.__version__, "E1_events": e1,
              "E2_sweep": e2, "E3_policy": e3, "E4_sizes": sizes,
              "E5_fault_injection": e5, "E7_matrix_cell": e7}
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/results.json").write_text(json.dumps(result, indent=2))
    write_event_table_rows(e1)

    # ---- console + markdown report -------------------------------------
    md = [f"# Results (generated by run_experiments.py, clingo {clingo.__version__})\n"]
    ok_all = True
    for dom, rows in e1.items():
        md.append(f"\n## E1 {dom}\n\n| Event | C | U | K | Tier | Outcome | =Expected | =Oracle | Audit |\n|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            oc = "autonomous" if r["autonomous"] else "escalate(" + "+".join(r["reasons"]) + ")"
            md.append(f"| {r['id']} | {r['C']} | {r['U']} | {r['K']} | {r['tier']} | {oc} | "
                      f"{r['matches_expected']} | {r['matches_oracle']} | {r['audit_complete']} |")
            ok_all &= r["matches_expected"] and r["matches_oracle"] and r["audit_complete"]
    md.append(f"\n## E2 exhaustive sweep\n\n{json.dumps(e2)}")
    md.append(f"\n## E3 policy change (theta_p 3 -> 4)\n\nfiles changed: {e3['files_changed']}; "
              f"lines changed: {e3['lines_changed']}\n")
    for dom, rows in e3["events"].items():
        for r in rows:
            oc = "autonomous" if r["autonomous"] else "escalate(" + "+".join(r["reasons"]) + ")"
            md.append(f"- {r['id']}: {oc}  expected={r['matches_expected']} oracle={r['matches_oracle']}")
            ok_all &= r["matches_expected"] and r["matches_oracle"]
    md.append(f"\n## E4 sizes\n\n{json.dumps(sizes)}")
    md.append("\n## E5 fault injection\n\n| Mutant | Caught by 14 events | Caught by sweep |\n|---|---|---|")
    for k_, v_ in e5.items():
        md.append(f"| {k_} | {v_['detected_by_14_events']} | {v_['detected_by_sweep']} |")
    md.append("\n## E7 matrix-cell test (matrix(4,1,2) -> matrix(4,1,3))\n\n" + json.dumps(e7))
    ok_all &= bool(e2["matrix_monotone"]) and all(v["detected_by_sweep"] for v in e5.values()) \
        and e7["as_expected"]
    (ROOT / "results/verification.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    tm = run_timing()
    (ROOT / "results/timing_latest.json").write_text(json.dumps(tm, indent=2))
    print("\n## E6 decision time (machine dependent, see results/timing_latest.json)\n" + json.dumps(tm))
    print("\nALL CHECKS PASSED" if ok_all and e2["mismatches"] == 0 else "\nSOME CHECKS FAILED")


if __name__ == "__main__":
    main()
