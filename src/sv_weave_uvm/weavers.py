"""UVM-specific weavers (entry-point group ``sv_weave.weavers``).

``do_print``: one ``uvm_printer`` call per field, through the binding's ``do_print``
feature, so ``print()`` and ``sprint()`` show the fields with the table, tree and line
printers. The core ``print`` weaver (``convert2string``) is independent of it; a config
lists either or both.
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
