"""Scan a SystemVerilog source tree for UVM object classes and their field automation.

For every class the scanner records its data members, its `uvm_field_*`
registrations and its hand-written do_* methods (with the members each one
touches and whether it calls super). Files are parsed one at a time with
pyslang, without preprocessing includes: UVM macros are unknown, so they end up
in trivia and the `uvm_field_*` registrations are found by a lexical scan of the
class text instead.

Usage: python assess/scan.py <root> [<root> ...] [-o out.json]
"""
import argparse
import json
import os
import re
import sys

from pyslang.syntax import SyntaxKind, SyntaxNode, SyntaxTree

# Methods whose bodies implement field automation by hand.
DO_METHODS = ("do_copy", "do_compare", "do_print", "convert2string",
              "do_pack", "do_unpack", "do_record", "do_execute_op")

# Class kinds the assessment cares about: anything that ends in uvm_object
# but not a component (components are not copied/compared/printed by value).
COMPONENT_BASES = {"uvm_component", "uvm_env", "uvm_agent", "uvm_driver",
                   "uvm_monitor", "uvm_scoreboard", "uvm_sequencer", "uvm_test",
                   "uvm_subscriber", "uvm_push_driver", "uvm_sequencer_param_base",
                   "uvm_sequencer_base", "uvm_reg_predictor",
                   "uvm_random_stimulus", "uvm_in_order_comparator",
                   "uvm_algorithmic_comparator", "uvm_in_order_class_comparator",
                   "uvm_in_order_built_in_comparator"}
SEQUENCE_BASES = {"uvm_sequence", "uvm_sequence_base", "uvm_reg_sequence"}

_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
_FIELD_RE = re.compile(r"`uvm_field_(\w+)\s*\(")
_UTILS_RE = re.compile(r"`uvm_(object|component)(_param)?_utils(_begin)?\b")
_IDENT_RE = re.compile(r"\b[A-Za-z_]\w*\b")


def strip_comments(text):
    """Replace comments with spaces, keeping newlines so line numbers hold."""
    return _COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)


def _macro_args(text, pos):
    """Split the parenthesised macro arguments starting at text[pos] == '('."""
    depth, args, cur = 0, [], []
    for i in range(pos, len(text)):
        ch = text[i]
        if ch == "(":
            depth += 1
            if depth == 1:
                continue
        elif ch == ")":
            depth -= 1
            if depth == 0:
                args.append("".join(cur).strip())
                return args, i
        elif ch == "," and depth == 1:
            args.append("".join(cur).strip())
            cur = []
            continue
        cur.append(ch)
    return None, len(text)


def scan_field_macros(text, line0):
    """Find `uvm_field_*(..., member, FLAGS)` in class text (comments stripped).

    The member is always the second-to-last argument and the flags the last
    (`uvm_field_enum(T, member, FLAGS)`, `uvm_field_int(member, FLAGS)`, ...).
    """
    out = []
    for m in _FIELD_RE.finditer(text):
        args, _ = _macro_args(text, m.end() - 1)
        if not args or len(args) < 2:
            continue
        flags = [f.strip() for f in re.split(r"[|+]", args[-1]) if f.strip()]
        out.append({"kind": m.group(1), "member": args[-2], "flags": flags,
                    "line": line0 + text.count("\n", 0, m.start())})
    return out


class FileScanner:
    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8", errors="replace") as fp:
            self.text = fp.read()
        self.tree = SyntaxTree.fromText(self.text, path)
        self.sm = self.tree.sourceManager
        self.buffer = None

    def _offset(self, loc):
        loc = self.sm.getFullyOriginalLoc(loc)
        if self.buffer is None:
            self.buffer = loc.buffer
        if loc.buffer != self.buffer:
            return None
        return loc.offset

    def _span(self, node):
        """(start, end) offsets of a node's own tokens (no leading trivia)."""
        s = self._offset(node.getFirstToken().location)
        last = node.getLastToken()
        e = self._offset(last.location)
        if s is None or e is None:
            return None
        return s, e + len(last.rawText)

    def _line(self, off):
        return self.text.count("\n", 0, off) + 1

    def scan(self):
        classes, methods = [], []
        self._walk(self.tree.root, classes, methods)
        return classes, methods

    def _walk(self, node, classes, methods):
        if node.kind == SyntaxKind.ClassDeclaration:
            classes.append(self._class(node))
            return
        if node.kind == SyntaxKind.FunctionDeclaration:
            m = self._method(node)
            if m is not None and m.get("scope"):
                methods.append(m)
            return
        for c in node:
            if isinstance(c, SyntaxNode):
                self._walk(c, classes, methods)

    def _class(self, node):
        span = self._span(node)
        ext = None
        if node.extendsClause is not None:
            bn = node.extendsClause.baseName
            ext = (bn.identifier.valueText if hasattr(bn, "identifier")
                   else str(bn).strip().split("#")[0].strip())
        cls = {"name": node.name.valueText, "extends": ext, "file": self.path,
               "line": self._line(span[0]) if span else None,
               "end_line": self._line(span[1]) if span else None,
               "parameterized": node.parameters is not None,
               "members": [], "fields": [], "methods": [], "utils": None}
        for item in node.items:
            if item.kind == SyntaxKind.ClassPropertyDeclaration:
                cls["members"].extend(self._members(item))
            elif item.kind == SyntaxKind.ClassMethodDeclaration:
                m = self._method(item.declaration)
                if m is not None:
                    cls["methods"].append(m)
            elif item.kind == SyntaxKind.ClassMethodPrototype:
                name = str(item.prototype.name).strip()
                if name in DO_METHODS:
                    cls["methods"].append({"name": name, "extern": True})
        if span:
            body = strip_comments(self.text[span[0]:span[1]])
            line0 = self._line(span[0])
            cls["fields"] = scan_field_macros(body, line0)
            u = _UTILS_RE.search(body)
            if u:
                cls["utils"] = u.group(0).lstrip("`")
            cls["field_macro_lines"] = sum(
                1 for ln in body.splitlines()
                if re.search(r"`uvm_(field_\w+|object(_param)?_utils_(begin|end)"
                             r"|component(_param)?_utils_(begin|end))\b", ln))
        return cls

    def _members(self, item):
        decl = item.declaration
        if decl.kind != SyntaxKind.DataDeclaration:
            return []
        quals = [q.valueText for q in item.qualifiers]
        quals += [q.valueText for q in decl.modifiers]
        typ = str(decl.type).strip()
        span = self._span(item)
        out = []
        for d in decl.declarators:
            if not isinstance(d, SyntaxNode):
                continue
            dims = "".join(str(x).strip() for x in d.dimensions)
            out.append({"name": d.name.valueText, "type": typ, "dims": dims,
                        "rand": "rand" in quals or "randc" in quals,
                        "static": "static" in quals, "const": "const" in quals,
                        "local": "local" in quals, "protected": "protected" in quals,
                        "line": self._line(span[0]) if span else None})
        return out

    def _method(self, fd):
        name = str(fd.prototype.name).strip()
        scope = None
        if "::" in name:
            scope, name = [x.strip() for x in name.rsplit("::", 1)]
        if name not in DO_METHODS:
            return None
        span = self._span(fd)
        if span is None:
            return None
        body = strip_comments(self.text[span[0]:span[1]])
        start, end = self._line(span[0]), self._line(span[1])
        return {"name": name, "scope": scope, "file": self.path, "line": start,
                "lines": end - start + 1,
                "super_call": bool(re.search(r"\bsuper\s*\.\s*%s\s*\(" % name, body)),
                "idents": sorted(set(_IDENT_RE.findall(body)))}


def _base(name):
    return name.split("#")[0].strip() if name else None


def classify(classes):
    """Mark each class with its UVM root (by name, transitively within the tree)."""
    by_name = {}
    for c in classes:
        by_name.setdefault(c["name"], c)

    def root(c, seen):
        ext = _base(c["extends"])
        if ext is None:
            return None
        if ext.startswith("uvm_"):
            return ext
        if ext in seen or ext not in by_name:
            return "?" + ext
        seen.add(ext)
        return root(by_name[ext], seen)

    for c in classes:
        r = root(c, {c["name"]})
        c["uvm_root"] = r
        if r is None or r.startswith("?"):
            c["category"] = "unknown" if r else "non_uvm"
        elif r in COMPONENT_BASES:
            c["category"] = "component"
        elif r in SEQUENCE_BASES:
            c["category"] = "sequence"
        elif r.startswith("uvm_reg") or r.startswith("uvm_mem") or r.startswith("uvm_vreg"):
            c["category"] = "reg"
        else:
            c["category"] = "object"


def scan_tree(roots):
    classes, methods, errors, nfiles = [], [], [], 0
    for root in roots:
        files = [root] if os.path.isfile(root) else sorted(
            os.path.join(d, f) for d, _, fs in os.walk(root, followlinks=True)
            for f in fs if f.endswith((".sv", ".svh")))
        for path in files:
            nfiles += 1
            try:
                cs, ms = FileScanner(path).scan()
            except Exception as e:  # keep going: one bad file must not stop a tree
                errors.append({"file": path, "error": repr(e)})
                continue
            classes.extend(cs)
            methods.extend(ms)
    # Attach out-of-class (extern) method bodies to their class by name.
    by_name = {}
    for c in classes:
        by_name.setdefault(c["name"], c)
    for m in methods:
        c = by_name.get(m["scope"])
        if c is None:
            continue
        c["methods"] = [x for x in c["methods"]
                        if not (x.get("extern") and x["name"] == m["name"])]
        c["methods"].append(m)
    for c in classes:
        names = {mb["name"] for mb in c["members"]}
        for m in c["methods"]:
            if "idents" in m:
                m["members"] = sorted(names & set(m.pop("idents")))
    classify(classes)
    return {"roots": roots, "files": nfiles, "errors": errors, "classes": classes}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("roots", nargs="+")
    ap.add_argument("-o", "--out", help="write JSON here (default: stdout)")
    args = ap.parse_args(argv)
    res = scan_tree(args.roots)
    out = open(args.out, "w") if args.out else sys.stdout
    json.dump(res, out, indent=1)
    if args.out:
        out.close()
        cats = {}
        for c in res["classes"]:
            cats[c["category"]] = cats.get(c["category"], 0) + 1
        print("%d files, %d classes %s, %d errors -> %s" % (
            res["files"], len(res["classes"]), cats, len(res["errors"]), args.out))


if __name__ == "__main__":
    main()
