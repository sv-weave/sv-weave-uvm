"""Find field-automation gaps in scanned UVM object classes.

Reads the JSON written by scan.py (or scans the roots itself) and reports, per
data member, the operations (copy, compare, print, pack) that no `uvm_field_*`
registration and no hand-written do_* method covers. These are the gaps
sv-weave-uvm closes by construction: every member gets every operation unless
an attribute says otherwise.

Rules:
  G1  member not covered by any copy path (class has some automation)
  G2  covered by copy but not compare, or by compare but not copy, with no
      UVM_NOCOMPARE / UVM_NOCOPY flag saying it is meant
  G3  covered by copy but not printed (do_print, convert2string or a field
      macro), with no UVM_NOPRINT flag
  G4  hand-written do_* override without a super call, base class not a uvm_ class
  G5  class has data members but no automation at all (one finding per class)
  G6  pack/unpack asymmetry: do_pack without do_unpack (or the reverse), or a
      member touched by only one of them

Flags follow UVM 1.2 semantics (what OpenTitan and core-v-verif run): an
operation is on unless the field's flags carry its UVM_NO* flag. Flag tokens
that are not UVM_* names (a local parameter, say) are treated as all-on.

Usage: python assess/gaps.py (--scan out.json | <root> ...) [-o gaps.json] [--text]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan  # noqa: E402

OPS = ("copy", "compare", "print", "pack")
# Hand methods that cover each operation.
OP_METHODS = {"copy": ("do_copy",), "compare": ("do_compare",),
              "print": ("do_print", "convert2string"),
              "pack": ("do_pack", "do_unpack")}
NO_FLAGS = {"UVM_NOCOPY": "copy", "UVM_NOCOMPARE": "compare",
            "UVM_NOPRINT": "print", "UVM_NOPACK": "pack", "UVM_NOUNPACK": "pack"}
# Member types that are not data: never copied/compared by value.
SKIP_TYPE_PREFIXES = ("virtual", "event", "semaphore", "mailbox", "process",
                      "uvm_event", "uvm_barrier", "uvm_analysis", "uvm_tlm",
                      "uvm_blocking", "uvm_nonblocking", "uvm_seq_item_pull",
                      "uvm_sequencer", "uvm_reg_block", "uvm_reg_map")
# Data classes only: utility objects (report servers, catchers, sequence
# libraries) also end in uvm_object but are never copied or compared.
DATA_ROOTS = {"uvm_object": "object", "uvm_sequence_item": "item",
              "uvm_transaction": "item"}


def data_members(cls):
    return [m for m in cls["members"]
            if not m["static"] and not m["const"]
            and not m["type"].startswith(SKIP_TYPE_PREFIXES)]


def field_ops(field):
    """Operations a `uvm_field_*` registration turns on (UVM 1.2 semantics)."""
    return {op for op in OPS
            if not any(NO_FLAGS.get(f) == op for f in field["flags"])}


def coverage(cls):
    """{member: {op: how}} where how is 'macro' or a method name; plus no-flags."""
    cov, nos = {}, {}
    for f in cls["fields"]:
        name = f["member"].split("[")[0].strip()
        for op in field_ops(f):
            cov.setdefault(name, {}).setdefault(op, "macro")
        nos.setdefault(name, set()).update(
            NO_FLAGS[x] for x in f["flags"] if x in NO_FLAGS)
    for m in cls["methods"]:
        for op, names in OP_METHODS.items():
            if m["name"] in names:
                for mb in m.get("members", []):
                    cov.setdefault(mb, {}).setdefault(op, m["name"])
    return cov, nos


def _finding(cls, rule, member, line, msg):
    return {"rule": rule, "file": cls["file"], "line": line, "class": cls["name"],
            "member": member, "kind": DATA_ROOTS[cls["uvm_root"]], "msg": msg}


def class_gaps(cls):
    out = []
    members = data_members(cls)
    methods = {m["name"]: m for m in cls["methods"]}
    automated = bool(cls["fields"]) or any(n in methods for n in scan.DO_METHODS)
    if members and not automated:
        out.append(_finding(cls, "G5", None, cls["line"],
                            "%d data members, no field macros or do_* methods"
                            % len(members)))
    if automated:
        cov, nos = coverage(cls)
        for mb in members:
            c, no = cov.get(mb["name"], {}), nos.get(mb["name"], set())
            if "copy" not in c and "copy" not in no:
                out.append(_finding(cls, "G1", mb["name"], mb["line"],
                                    "not copied"))
            if "copy" in c and "compare" not in c and "compare" not in no:
                out.append(_finding(cls, "G2", mb["name"], mb["line"],
                                    "copied (%s) but not compared" % c["copy"]))
            elif "compare" in c and "copy" not in c and "copy" not in no:
                out.append(_finding(cls, "G2", mb["name"], mb["line"],
                                    "compared (%s) but not copied" % c["compare"]))
            if "copy" in c and "print" not in c and "print" not in no:
                out.append(_finding(cls, "G3", mb["name"], mb["line"],
                                    "copied (%s) but not printed" % c["copy"]))
    base = scan._base(cls["extends"])
    if base and not base.startswith("uvm_"):
        for m in cls["methods"]:
            if "super_call" in m and not m["super_call"]:
                out.append(_finding(cls, "G4", None, m["line"],
                                    "%s does not call super.%s (base %s)"
                                    % (m["name"], m["name"], base)))
    pk, up = methods.get("do_pack"), methods.get("do_unpack")
    if bool(pk) != bool(up):
        have = pk or up
        out.append(_finding(cls, "G6", None, have.get("line", cls["line"]),
                            "%s without %s" % (have["name"], "do_unpack" if pk
                                               else "do_pack")))
    elif pk and up and "members" in pk and "members" in up:
        for name in sorted(set(pk["members"]) ^ set(up["members"])):
            only = "do_pack" if name in pk["members"] else "do_unpack"
            out.append(_finding(cls, "G6", name, pk["line"],
                                "touched only by %s" % only))
    return out


def find_gaps(scan_res):
    findings, n = [], {"item": 0, "object": 0}
    for cls in scan_res["classes"]:
        if cls["category"] != "object" or cls["uvm_root"] not in DATA_ROOTS:
            continue
        n[DATA_ROOTS[cls["uvm_root"]]] += 1
        findings.extend(class_gaps(cls))
    counts = {"item": {}, "object": {}}
    for f in findings:
        c = counts[f["kind"]]
        c[f["rule"]] = c.get(f["rule"], 0) + 1
    return {"roots": scan_res["roots"], "classes_checked": n,
            "counts": {k: dict(sorted(v.items())) for k, v in counts.items()},
            "findings": findings}


def text_report(res, rel=None):
    lines = []
    for f in res["findings"]:
        path = os.path.relpath(f["file"], rel) if rel else f["file"]
        lines.append("%s:%s: %s %s %s%s: %s" % (
            path, f["line"], f["rule"], f["kind"], f["class"],
            "." + f["member"] if f["member"] else "", f["msg"]))
    lines.append("classes checked %s; findings %s"
                 % (res["classes_checked"], res["counts"]))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("roots", nargs="*")
    ap.add_argument("--scan", help="read scan.py JSON instead of scanning roots")
    ap.add_argument("-o", "--out", help="write findings JSON here")
    ap.add_argument("--text", action="store_true", help="print one line per finding")
    ap.add_argument("--rel", help="print paths relative to this directory")
    args = ap.parse_args(argv)
    if args.scan:
        with open(args.scan) as fp:
            sres = json.load(fp)
    elif args.roots:
        sres = scan.scan_tree(args.roots)
    else:
        ap.error("give roots or --scan")
    res = find_gaps(sres)
    if args.out:
        with open(args.out, "w") as fp:
            json.dump(res, fp, indent=1)
    if args.text or not args.out:
        print(text_report(res, args.rel))
    else:
        print("classes checked %s; findings %s -> %s" % (res["classes_checked"],
                                                 res["counts"], args.out))


if __name__ == "__main__":
    main()
