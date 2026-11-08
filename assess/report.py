"""Savings report: lines sv-weave would remove, as raw counts and as a share of the
testbench, with charts.

Reads the scan/size/gaps JSON of assess/results (see README there) and the source trees
(to count lines), and writes <out>/report.md, <out>/numbers.json and PNG charts.

Denominators (code lines = non-blank, non-comment):
  dv_lines     every .sv/.svh under the roots that is testbench code: for OpenTitan,
               files with a `dv` directory in their path; for core-v-verif, all files.
  class_lines  code lines inside class bodies (all UVM classes: components, sequences,
               configs, items ...).
  data_lines   code lines inside the data classes (those size.py counts).
  auto_lines   field-automation code: field macros + hand do_* methods (size.py
               macro_src + hand_src).
`saved` is size.py's upper bound (macro_src + hand_src - weave_src).

  python assess/report.py [--results assess/results] [--out assess/results/report]
"""
import argparse
import json
import os
import re
import statistics

TREES = (("ot", "OpenTitan"), ("cv", "core-v-verif"))
_BLOCK = re.compile(r"/\*.*?\*/", re.S)
_LINE = re.compile(r"//.*")


def code_lines(text):
    """Per source line, True if it holds code (not blank, not only comment)."""
    text = _BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return [bool(_LINE.sub("", l).strip()) for l in text.split("\n")]


def is_dv(tree, path):
    return tree != "ot" or "/dv/" in path.replace(os.sep, "/") + "/"


def _files(roots):
    for root in roots:
        for d, _, fs in os.walk(root, followlinks=True):
            for f in fs:
                if f.endswith((".sv", ".svh")):
                    yield os.path.join(d, f)


def tree_numbers(tree, scan, size, gaps):
    code = {}
    for p in _files(scan_roots(scan)):
        if is_dv(tree, p):
            with open(p, errors="replace") as fp:
                code[p] = code_lines(fp.read())

    def span(c):
        mask = code.get(c["file"])
        if mask is None:
            with open(c["file"], errors="replace") as fp:
                mask = code[c["file"]] = code_lines(fp.read())
        return sum(mask[c["line"] - 1:c.get("end_line", c["line"])])

    scan_by = {(c["file"], c["line"]): c for c in scan["classes"]}
    class_lines = sum(span(c) for c in scan["classes"])
    rows = []
    for r in size["classes"]:
        c = scan_by.get((r["file"], r["line"]))
        r = dict(r, lines=span(c) if c else 0)
        rows.append(r)
    data = [r for r in rows if r["category"] == "data"]
    tot = {k: sum(r[k] for r in data) for k in
           ("macro_src", "hand_src", "weave_src", "saved", "macro_exp", "woven_gen", "lines")}
    dv_lines = sum(sum(m) for p, m in code.items() if is_dv(tree, p))

    item_cls = {(f["file"], f["class"]) for f in gaps["findings"] if f["kind"] == "item"}
    rules = {}
    for f in gaps["findings"]:
        if f["kind"] == "item":
            rules[f["rule"]] = rules.get(f["rule"], 0) + 1

    pct_class = sorted(100.0 * r["saved"] / r["lines"] for r in data if r["lines"] > 0)
    # Compiled text of the tb, UVM library excluded: macros expanded vs woven code added.
    before = dv_lines - tot["macro_src"] + tot["macro_exp"]
    after = dv_lines - tot["saved"] + tot["woven_gen"]
    return {
        "dv_files": len(code), "dv_lines": dv_lines, "class_lines": class_lines,
        "data_classes": len(data), "data_lines": tot["lines"],
        "auto_lines": tot["macro_src"] + tot["hand_src"], **tot,
        "pct_dv": 100.0 * tot["saved"] / dv_lines,
        "pct_class": 100.0 * tot["saved"] / class_lines,
        "pct_data": 100.0 * tot["saved"] / tot["lines"],
        "pct_auto": 100.0 * tot["saved"] / (tot["macro_src"] + tot["hand_src"]),
        "per_class_pct_median": statistics.median(pct_class),
        "per_class_pct": pct_class,
        "compiled_before": before, "compiled_after": after,
        "items": gaps["classes_checked"]["item"], "items_with_gaps": len(item_cls),
        "item_rules": rules,
        "groups": top_groups(data),
    }


def scan_roots(scan):
    r = scan["roots"]
    return r if isinstance(r, list) else json.loads(r.replace("'", '"'))


def top_groups(data, n=10):
    g = {}
    for r in data:
        k = "%s/%s" % (os.path.basename(r["root"].rstrip("/")), r["group"])
        e = g.setdefault(k, {"saved": 0, "lines": 0})
        e["saved"] += r["saved"]
        e["lines"] += r["lines"]
    return sorted(g.items(), key=lambda kv: -kv[1]["saved"])[:n]


def charts(nums, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    names = [label for t, label in TREES]
    colors = ("#1f77b4", "#ff7f0e")

    # 1. Share of code removed, by denominator.
    fig, ax = plt.subplots(figsize=(8, 4))
    cats = [("pct_dv", "all DV code"), ("pct_class", "UVM class code"),
            ("pct_data", "data classes"), ("pct_auto", "field automation")]
    w = 0.38
    for i, (t, label) in enumerate(TREES):
        vals = [nums[t][k] for k, _ in cats]
        xs = [j + (i - 0.5) * w for j in range(len(cats))]
        bars = ax.bar(xs, vals, w, label=label, color=colors[i])
        ax.bar_label(bars, fmt="%.1f%%", fontsize=8)
    ax.set_xticks(range(len(cats)), [c for _, c in cats])
    ax.set_ylabel("% of lines removed")
    ax.set_ylim(0, 100)
    ax.set_title("Lines sv-weave removes, as a share of ...")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "pct_removed.png"), dpi=120)
    plt.close(fig)

    # 2. Where the DV lines are: removed vs kept.
    fig, ax = plt.subplots(figsize=(8, 2.8))
    for i, (t, label) in enumerate(TREES):
        n = nums[t]
        parts = [(n["saved"], "removed by sv-weave", "#d62728"),
                 (n["data_lines"] - n["saved"], "rest of data classes", "#ff9896"),
                 (n["class_lines"] - n["data_lines"], "other UVM classes", "#aec7e8"),
                 (n["dv_lines"] - n["class_lines"], "outside classes (modules, ifs, SVA)",
                  "#c7c7c7")]
        left = 0
        for v, lab, c in parts:
            ax.barh(i, 100.0 * v / n["dv_lines"], left=left, color=c,
                    label=lab if i == 0 else None)
            left += 100.0 * v / n["dv_lines"]
    ax.set_yticks(range(len(TREES)), names)
    ax.set_xlabel("% of DV code lines")
    ax.set_xlim(0, 100)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, fontsize=8)
    ax.set_title("Where the DV code is")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "dv_breakdown.png"), dpi=120)
    plt.close(fig)

    # 3. Per data class: % of the class's lines removed.
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.hist([nums[t]["per_class_pct"] for t, _ in TREES], bins=range(0, 105, 10),
            label=names, color=colors)
    ax.set_xlabel("% of the class's code lines removed")
    ax.set_ylabel("data classes")
    ax.set_title("Per data class (items, transactions, configs with field automation)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "per_class.png"), dpi=120)
    plt.close(fig)

    # 4. Top groups by lines removed.
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for ax, (t, label), c in zip(axs, TREES, colors):
        g = list(reversed(nums[t]["groups"]))
        bars = ax.barh([k for k, _ in g], [v["saved"] for _, v in g], color=c)
        ax.bar_label(bars, labels=["%d%%" % (100.0 * v["saved"] / v["lines"]) if v["lines"]
                                   else "" for _, v in g], fontsize=8, padding=2)
        ax.set_title("%s: lines removed (%% of the group's data-class lines)" % label,
                     fontsize=9)
        ax.tick_params(axis="y", labelsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "top_groups.png"), dpi=120)
    plt.close(fig)

    # 5. Compiled text (UVM library excluded).
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for i, (t, label) in enumerate(TREES):
        n = nums[t]
        b = ax.bar([i - 0.2, i + 0.2], [n["compiled_before"] / 1000, n["compiled_after"] / 1000],
                   0.38, color=["#7f7f7f", "#2ca02c"],
                   label=["field macros", "sv-weave"] if i == 0 else None)
        ax.bar_label(b, fmt="%.0fk", fontsize=8)
    ax.set_xticks(range(len(TREES)), names)
    ax.set_ylabel("k lines the compiler sees")
    ax.set_title("Testbench code after macro expansion / weaving")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(out, "compiled.png"), dpi=120)
    plt.close(fig)

    # 6. Item classes with gaps.
    fig, ax = plt.subplots(figsize=(6, 2.6))
    for i, (t, label) in enumerate(TREES):
        n = nums[t]
        ax.barh(i, n["items_with_gaps"], color="#d62728",
                label="with a reported gap" if i == 0 else None)
        ax.barh(i, n["items"] - n["items_with_gaps"], left=n["items_with_gaps"],
                color="#98df8a", label="none reported" if i == 0 else None)
        ax.text(n["items"] + 0.5, i, "%d / %d" % (n["items_with_gaps"], n["items"]),
                va="center", fontsize=8)
    ax.set_yticks(range(len(TREES)), names)
    ax.set_xlabel("sequence-item classes")
    ax.set_xlim(0, max(nums[t]["items"] for t, _ in TREES) * 1.2)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(out, "item_gaps.png"), dpi=120)
    plt.close(fig)


def markdown(nums):
    o, c = nums["ot"], nums["cv"]

    def row(label, key, fmt="{:,}"):
        return "| %s | %s | %s |" % (label, fmt.format(o[key]), fmt.format(c[key]))
    pct = "{:.1f}%"
    lines = [
        "| | OpenTitan | core-v-verif |", "|---|---|---|",
        row("DV source files", "dv_files"),
        row("DV code lines (non-blank, non-comment)", "dv_lines"),
        row("... inside UVM classes", "class_lines"),
        row("data classes (with field automation or hand do_*)", "data_classes"),
        row("... their code lines", "data_lines"),
        row("field-automation lines (field macros + hand do_*)", "auto_lines"),
        row("**lines removed by sv-weave** (upper bound)", "saved"),
        row("sv-weave attribute lines added back", "weave_src"),
        row("**% of all DV code**", "pct_dv", pct),
        row("% of UVM class code", "pct_class", pct),
        row("% of data-class code", "pct_data", pct),
        row("% of field-automation code", "pct_auto", pct),
        row("median % per data class", "per_class_pct_median", pct),
        row("compiled tb lines, field macros (est.)", "compiled_before"),
        row("compiled tb lines, sv-weave (est.)", "compiled_after"),
        row("item classes", "items"),
        row("item classes with a reported gap", "items_with_gaps"),
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--results", default=os.path.join(here, "results"))
    ap.add_argument("--out", default=os.path.join(here, "results", "report"))
    ap.add_argument("--no-charts", action="store_true")
    a = ap.parse_args(argv)
    nums = {}
    for t, _ in TREES:
        load = lambda k: json.load(open(os.path.join(a.results, "%s_%s.json" % (t, k))))
        nums[t] = tree_numbers(t, load("scan"), load("size"), load("gaps"))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "numbers.json"), "w") as fp:
        json.dump(nums, fp, indent=1)
    with open(os.path.join(a.out, "table.md"), "w") as fp:
        fp.write(markdown(nums) + "\n")
    if not a.no_charts:
        charts(nums, a.out)
    print(markdown(nums))


if __name__ == "__main__":
    main()
