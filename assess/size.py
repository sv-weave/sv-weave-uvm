"""Estimate the field-automation code sv-weave-uvm would remove.

Reads the JSON written by scan.py (or scans the roots itself). For each class
that has `uvm_field_*` registrations or hand-written do_* methods, counts:

  macro_src   source lines of `uvm_field_*` and `uvm_*_utils_begin/end`
  hand_src    source lines of hand do_copy/do_compare/do_print/convert2string/
              do_pack/do_unpack/do_record bodies (declaration to endfunction,
              blank and comment lines included; extern bodies included)
  weave_src   the sv-weave equivalent: one `uvm_object_utils` line where the
              class used utils_begin/end, plus one attribute line per field
              whose flags turn an operation off (UVM_NO*), set a non-default
              radix or UVM_REFERENCE (a guess: one `(* ... *)` line each)
  saved       macro_src + hand_src - weave_src (an upper bound: hand methods
              that do more than field-by-field work would partly stay)
  macro_exp   lines the field macros expand to (`verilator -E -P`, UVM
              2020.3.2), from per-macro constants measured once (MACRO_EXP)
  woven_gen   estimate of the generated woven code for the class's data
              members (WOVEN_PER_MEMBER lines each; bench/linecount.py measured
              122 generated lines for 8 fields)

Totals are given per root and per group: the first --depth (default 1) directories of
the class's file under its root (hw/dv/sv/<agent>, lib/uvm_agents/<agent>).
Classes are split into `data` (object/item classes, as gaps.py checks) and
`other` (components, sequences, utility objects, unknown bases).

Usage: python assess/size.py (--scan out.json | <root> ...) [-o size.json]
       [--depth N] [--text]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gaps  # noqa: E402
import scan  # noqa: E402

# Expanded lines per `uvm_field_<kind>` (one field, UVM_DEFAULT), measured with
# verilator -E -P on UVM 2020.3.2: lines of the class minus the 73 of an empty
# utils_begin/end pair. UTILS_BEGIN_END_EXP is that pair minus plain utils (21).
MACRO_EXP = {"int": 152, "string": 95, "object": 237, "enum": 202, "real": 148,
             "sarray_int": 313, "sarray_enum": 341, "array_int": 391,
             "queue_int": 385, "array_object": 409, "aa_int_string": 199}
# Kinds not measured: nearest measured kind by prefix, else int.
MACRO_EXP_PREFIX = (("sarray", 313), ("array", 391), ("queue", 385), ("aa", 199))
UTILS_BEGIN_END_EXP = 52
WOVEN_PER_MEMBER = 15
# Flags that need an sv-weave attribute (UVM_HEX is the default radix).
ATTR_FLAGS = {"UVM_NOCOPY", "UVM_NOCOMPARE", "UVM_NOPRINT", "UVM_NOPACK",
              "UVM_NOUNPACK", "UVM_NORECORD", "UVM_REFERENCE", "UVM_DEC",
              "UVM_BIN", "UVM_OCT", "UVM_UNSIGNED", "UVM_STRING", "UVM_TIME",
              "UVM_REAL", "UVM_REAL_DEC", "UVM_REAL_EXP"}
DEFAULT_DEPTH = 1
KEYS = ("classes", "fields", "macro_src", "hand_src", "weave_src", "saved",
        "macro_exp", "woven_gen")


def macro_exp(kind):
    if kind in MACRO_EXP:
        return MACRO_EXP[kind]
    for prefix, n in MACRO_EXP_PREFIX:
        if kind.startswith(prefix):
            return n
    return MACRO_EXP["int"]


def class_size(cls):
    """Size row for one class, or None if it has no field automation."""
    hand = [m for m in cls["methods"] if "lines" in m]
    macro_src = cls.get("field_macro_lines", 0)
    if not macro_src and not hand:
        return None
    begin = bool(cls["utils"] and cls["utils"].endswith("_begin"))
    attrs = sum(1 for f in cls["fields"] if ATTR_FLAGS & set(f["flags"]))
    weave_src = (1 if begin else 0) + attrs
    hand_src = sum(m["lines"] for m in hand)
    data = cls["category"] == "object" and cls["uvm_root"] in gaps.DATA_ROOTS
    return {"class": cls["name"], "file": cls["file"], "line": cls["line"],
            "category": "data" if data else "other", "fields": len(cls["fields"]),
            "macro_src": macro_src, "hand_src": hand_src, "weave_src": weave_src,
            "saved": macro_src + hand_src - weave_src,
            "macro_exp": (UTILS_BEGIN_END_EXP if begin else 0)
            + sum(macro_exp(f["kind"]) for f in cls["fields"]),
            "woven_gen": WOVEN_PER_MEMBER * len(gaps.data_members(cls))}


def group_of(path, roots, depth):
    """(root, group): group is the first `depth` dirs of path under its root."""
    for root in roots:
        rel = os.path.relpath(path, root)
        if not rel.startswith(".."):
            parts = rel.split(os.sep)[:-1][:depth]
            return root, "/".join(parts) if parts else "."
    return "?", "?"


def _add(tot, row):
    tot["classes"] += 1
    for k in KEYS[1:]:
        tot[k] += row[k]


def size_report(scan_res, depth=DEFAULT_DEPTH):
    rows, totals, groups = [], {}, {}
    for cls in scan_res["classes"]:
        row = class_size(cls)
        if row is None:
            continue
        row["root"], row["group"] = group_of(cls["file"], scan_res["roots"], depth)
        rows.append(row)
        for tot in (totals.setdefault(row["root"], {}),
                    groups.setdefault(row["root"] + ":" + row["group"], {})):
            _add(tot.setdefault(row["category"], dict.fromkeys(KEYS, 0)), row)
            _add(tot.setdefault("all", dict.fromkeys(KEYS, 0)), row)
    return {"roots": scan_res["roots"], "depth": depth, "totals": totals,
            "groups": dict(sorted(groups.items())), "classes": rows}


def text_report(res):
    hdr = "%-50s %5s %6s %6s %6s %6s %6s %7s %6s" % (
        "group (data classes)", "cls", "fields", "macro", "hand", "weave", "saved",
        "exp", "gen")
    lines = [hdr]
    def label(root):  # last two dirs: cv32e40p/env and cv32e40s/env stay apart
        return "/".join(root.rstrip("/").split("/")[-2:])
    def short(key):  # "<root>:<group>" -> "<label>/<group>"
        root, _, grp = key.rpartition(":")
        return label(root) + "/" + grp
    for name, tot in [(short(k), t) for k, t in res["groups"].items()] + [
            ("TOTAL " + label(r), t)
            for r, t in res["totals"].items()]:
        t = tot.get("data")
        if t:
            lines.append("%-50s %5d %6d %6d %6d %6d %6d %7d %6d" % (
                name[-50:], t["classes"], t["fields"], t["macro_src"], t["hand_src"],
                t["weave_src"], t["saved"], t["macro_exp"], t["woven_gen"]))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("roots", nargs="*")
    ap.add_argument("--scan", help="read scan.py JSON instead of scanning roots")
    ap.add_argument("-o", "--out", help="write JSON here")
    ap.add_argument("--depth", type=int, default=DEFAULT_DEPTH,
                    help="group by this many directories under the root")
    ap.add_argument("--text", action="store_true", help="print the group table")
    args = ap.parse_args(argv)
    if args.scan:
        with open(args.scan) as fp:
            sres = json.load(fp)
    elif args.roots:
        sres = scan.scan_tree(args.roots)
    else:
        ap.error("give roots or --scan")
    res = size_report(sres, args.depth)
    if args.out:
        with open(args.out, "w") as fp:
            json.dump(res, fp, indent=1)
    if args.text or not args.out:
        print(text_report(res))
    else:
        print("%d classes -> %s" % (len(res["classes"]), args.out))


if __name__ == "__main__":
    main()
