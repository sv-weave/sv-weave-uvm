#!/usr/bin/env python3
"""Count source and macro-expanded lines of the benchmark sequence item.

Three variants of one class (bench/fields/): `uvm_field_* macros, hand-written
do_* methods, and a plain class woven by sv-weave. For each, prints:

- source:   non-blank, non-comment lines of the class as the user writes it
- expanded: the same after `verilator -E -P` (all UVM macros expanded); for the
            woven variant, the user's class plus the generated Woven_* class

Needs `verilator` and `sv-weave` on PATH. Usage:
    python bench/linecount.py [--uvm DIR] [--markdown]
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = os.path.join(HERE, "fields")
ROOT = os.path.dirname(HERE)
DEFAULT_UVM = os.path.join(ROOT, "packages", "verilator", "share", "uvm", "src")
VARIANTS = [("macros", "uvm_field_* macros"), ("hand", "hand-written do_*"),
            ("woven", "sv-weave")]


def class_lines(text: str, name: str):
    """Lines from `class <name>` to its `endclass`, without blanks or // comments."""
    out, inside = [], False
    for line in text.splitlines():
        if not inside and re.match(r"\s*class\s+%s\b" % re.escape(name), line):
            inside = True
        if inside:
            s = line.strip()
            if s and not s.startswith("//"):
                out.append(s)
            if re.match(r"endclass\b", s):
                break
    if not out:
        raise RuntimeError("class %s not found" % name)
    return out


def expand(path: str, uvm: str) -> str:
    return subprocess.run(["verilator", "-E", "-P", "-I" + uvm, path], check=True,
                          capture_output=True, text=True).stdout


def weave(uvm: str, out_dir: str) -> str:
    subprocess.run(["sv-weave", "gen", "-c", os.path.join(FIELDS, "sv-weave.yaml"),
                    "-I", uvm, "-o", out_dir, os.path.join(uvm, "uvm_pkg.sv"),
                    os.path.join(FIELDS, "woven_pkg.sv")],
                   check=True, capture_output=True, text=True)
    return os.path.join(out_dir, "bm_woven_pkg_woven.sv")


def count(uvm: str):
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        woven_sv = weave(uvm, tmp)
        for key, label in VARIANTS:
            path = os.path.join(FIELDS, key + "_pkg.sv")
            with open(path) as fp:
                src = len(class_lines(fp.read(), "bm_tx"))
            exp = len(class_lines(expand(path, uvm), "bm_tx"))
            gen = None
            if key == "woven":
                gen_text = expand(woven_sv, uvm)
                gen = len(class_lines(gen_text, "Woven_bm_tx__release"))
                exp += gen
            rows.append((label, src, exp, gen))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--uvm", default=DEFAULT_UVM, help="UVM src dir (has uvm_macros.svh)")
    ap.add_argument("--markdown", action="store_true", help="print a Markdown table")
    args = ap.parse_args(argv)
    rows = count(args.uvm)
    if args.markdown:
        print("| Variant | Source lines | Expanded lines |")
        print("|---|---:|---:|")
        for label, src, exp, gen in rows:
            note = " (%d user + %d generated)" % (exp - gen, gen) if gen else ""
            print("| %s | %d | %d%s |" % (label, src, exp, note))
    else:
        for label, src, exp, gen in rows:
            print("%-20s source %4d  expanded %5d%s" % (
                label, src, exp, "  (generated %d)" % gen if gen else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
