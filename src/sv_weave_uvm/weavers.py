"""UVM-specific weavers (entry-point group ``sv_weave.weavers``).

``do_print``: one ``uvm_printer`` call per field, through the binding's ``do_print``
feature, so ``print()`` and ``sprint()`` show the fields with the table, tree and line
printers. The core ``print`` weaver (``convert2string``) is independent of it; a config
lists either or both.

``pack``: ``do_pack`` and ``do_unpack`` through ``uvm_packer``, so ``pack()``,
``pack_bytes()``, ``pack_ints()`` and the ``unpack*()`` calls round-trip the fields.
"""
from sv_weave.frontend.types import ArrayKind, TypeCat
from sv_weave.match import extends_root, has_attr
from sv_weave.plugin import Weaver
from sv_weave.weavers.copy import copyable

from .__version__ import __version__


def _q(s: str) -> str:
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def _type_name(t) -> str:
    return t.spelling or t.text or t.cat.value


def print_stmt(w, f, printer: str):
    """The ``uvm_printer`` call that prints field ``f``, or "" for none."""
    t = f.type
    a = "this.%s" % f.name
    name = _q(f.name)
    if t.cat == TypeCat.ENUM and t.nameable:
        return "%s.print_generic(%s, %s, $bits(%s), %s.name());" % (
            printer, name, _q(_type_name(t)), a, a)
    if t.cat in (TypeCat.INTEGRAL, TypeCat.ENUM) or \
            (t.cat in (TypeCat.STRUCT, TypeCat.UNION) and t.packed):
        radix = "uvm_pkg::UVM_DEC" if t.signed else "uvm_pkg::UVM_NORADIX"
        fn = "print_field_int" if 0 < t.width <= 64 else "print_field"
        return "%s.%s(%s, %s, $bits(%s), %s);" % (printer, fn, name, a, a, radix)
    if t.cat == TypeCat.STRING:
        return "%s.print_string(%s, %s);" % (printer, name, a)
    if t.cat == TypeCat.REAL:
        return "%s.print_real(%s, %s);" % (printer, name, a)
    if t.cat == TypeCat.CLASS:
        cls = w.model.find_class(t.class_qname) if t.class_qname else None
        if cls is not None and cls.is_a("uvm_pkg::uvm_object"):
            if "weave_deep" in f.attrs:
                return "%s.print_object(%s, %s);" % (printer, name, a)
            # A reference, as UVM_REFERENCE fields print: type and instance id.
            return ('%s.print_generic(%s, %s, 0, (%s == null) ? "<null>" : '
                    '$sformatf("@%%0d", %s.get_inst_id()));'
                    % (printer, name, _q(_type_name(t)), a, a))
        return ('%s.print_generic(%s, %s, 0, (%s == null) ? "<null>" : "<object>");'
                % (printer, name, _q(_type_name(t)), a))
    if t.cat in (TypeCat.EVENT, TypeCat.CHANDLE):
        return ""
    if t.cat == TypeCat.ARRAY:
        size = "$size(%s)" % a if t.array_kind == ArrayKind.FIXED else "%s.size()" % a
    else:
        size = "0"
    return '%s.print_generic(%s, %s, %s, $sformatf("%%p", %s));' % (
        printer, name, _q(_type_name(t)), size, a)


class DoPrintWeaver(Weaver):
    name = "do_print"
    version = __version__

    def subscribe(self, bus):
        bus.on(extends_root() & ~has_attr("weave_noprint"), self.weave)

    def weave(self, w):
        slot = w.feature("do_print")
        printer = slot.sig.arg_names[0] if slot.sig.arg_names else "printer"
        for f in w.fields():
            if not copyable(w, f, "weave_noprint"):
                continue
            text = print_stmt(w, f, printer)
            if text:
                slot.body.add(text)


def _scalar(t) -> bool:
    return t.cat in (TypeCat.INTEGRAL, TypeCat.STRING, TypeCat.REAL) or \
        (t.cat == TypeCat.ENUM and t.nameable) or \
        (t.cat in (TypeCat.STRUCT, TypeCat.UNION) and t.packed)


def _pack_one(t, a: str, packer: str) -> str:
    if t.cat == TypeCat.STRING:
        return "%s.pack_string(%s);" % (packer, a)
    if t.cat == TypeCat.REAL:
        return "%s.pack_real(%s);" % (packer, a)
    fn = "pack_field_int" if 0 < t.width <= 64 else "pack_field"
    return "%s.%s(%s, $bits(%s));" % (packer, fn, a, a)


def _unpack_one(t, a: str, packer: str) -> str:
    if t.cat == TypeCat.STRING:
        return "%s = %s.unpack_string();" % (a, packer)
    if t.cat == TypeCat.REAL:
        return "%s = %s.unpack_real();" % (a, packer)
    fn = "unpack_field_int" if 0 < t.width <= 64 else "unpack_field"
    rhs = "%s.%s($bits(%s))" % (packer, fn, a)
    if t.cat == TypeCat.ENUM:
        rhs = "%s'(%s)" % (t.spelling, rhs)
    return "%s = %s;" % (a, rhs)


def pack_stmts(w, f, packer: str):
    """The (pack, unpack) statements for field ``f``; None when it is not packed,
    a str when it cannot be packed (the reason)."""
    t = f.type
    a = "this.%s" % f.name
    if _scalar(t):
        return _pack_one(t, a, packer), _unpack_one(t, a, packer)
    if t.cat == TypeCat.CLASS:
        cls = w.model.find_class(t.class_qname) if t.class_qname else None
        if "weave_deep" not in f.attrs:
            return None  # a reference: not packed, as UVM_REFERENCE fields
        if cls is None or not cls.is_a("uvm_pkg::uvm_object"):
            return "a weave_deep handle that is not a uvm_object"
        # unpack_object_with_meta creates the object from the packed type name; for a
        # woven class it does not (it shares the user's name) and a null handle stays
        # null. Create it through the factory first, as a deep copy does.
        made = w.binding.create_expr(cls, _q(f.name))
        create = "  if (%s == null) %s = %s;\n" % (a, a, made) if made else ""
        unpack = ("begin\n"
                  "  uvm_pkg::uvm_object ref__;\n%(c)s"
                  "  ref__ = %(a)s;\n"
                  "  %(p)s.unpack_object_with_meta(ref__);\n"
                  "  if (ref__ != %(a)s && !$cast(%(a)s, ref__))\n"
                  "    uvm_pkg::uvm_report_error(\"sv-weave\", {\"do_unpack: cannot cast \",\n"
                  "      ref__.get_type_name(), \" to %(f)s\"});\n"
                  "end" % {"a": a, "p": packer, "f": f.name, "c": create})
        return "%s.pack_object_with_meta(%s);" % (packer, a), unpack
    if t.cat in (TypeCat.EVENT, TypeCat.CHANDLE, TypeCat.VIRTUAL_IF):
        return None
    if t.cat == TypeCat.ARRAY and t.elem is not None and _scalar(t.elem) and \
            t.array_kind != ArrayKind.ASSOC:
        e = "%s[i__]" % a
        pe, ue = _pack_one(t.elem, e, packer), _unpack_one(t.elem, e, packer)
        if t.array_kind == ArrayKind.FIXED:
            return ("foreach (%s[i__]) %s" % (a, pe), "foreach (%s[i__]) %s" % (a, ue))
        pack = ("begin\n  %s.pack_field_int(%s.size(), 32);\n"
                "  foreach (%s[i__]) %s\nend" % (packer, a, a, pe))
        if t.array_kind == ArrayKind.DYNAMIC:
            resize = "  %s = new[sz__];\n" % a
        else:
            resize = "  while (%s.size() > sz__) void'(%s.pop_back());\n" % (a, a)
        unpack = ("begin\n  int sz__;\n  sz__ = %s.unpack_field_int(32);\n%s"
                  "  for (int i__ = 0; i__ < sz__; i__++) %s\nend"
                  % (packer, resize, ue))
        return pack, unpack
    return "type %s" % _type_name(t)


class PackWeaver(Weaver):
    """``do_pack`` and ``do_unpack`` through ``uvm_packer``, field by field in
    declaration order; arrays other than fixed-size ones carry their size (32 bits)
    first, as `` `uvm_pack_array``. Opt out with ``weave_nopack``."""
    name = "pack"
    version = __version__

    def subscribe(self, bus):
        bus.on(extends_root() & ~has_attr("weave_nopack"), self.weave)

    def weave(self, w):
        ps, us = w.feature("do_pack"), w.feature("do_unpack")
        pp = ps.sig.arg_names[0] if ps.sig.arg_names else "packer"
        up = us.sig.arg_names[0] if us.sig.arg_names else "packer"
        for f in w.fields():
            if not copyable(w, f, "weave_nopack"):
                continue
            r = pack_stmts(w, f, pp)
            if r is None:
                continue
            if isinstance(r, str):
                w.warning("pack: field '%s' (%s) is not packed" % (f.name, r))
                continue
            ps.body.add(r[0])
            us.body.add(pack_stmts(w, f, up)[1])
