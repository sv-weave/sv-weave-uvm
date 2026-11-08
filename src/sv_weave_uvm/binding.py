"""The UVM binding for sv-weave (``binding: uvm``). It works *with* the library:

- **Features are uvm_object's own virtual hooks:** ``copy`` -> ``do_copy``,
  ``compare`` -> ``do_compare``, ``print`` -> ``convert2string``. UVM's
  ``copy()``, ``compare()`` and ``sprint``-style calls reach them as usual.
- **The library's factory decides what gets created.** Each woven class carries
  `` `uvm_object_utils `` and is registered with ``sv_weave_uvm_factory``
  (``share/sv/sv_weave_uvm_pkg.sv``), a ``uvm_default_factory`` subclass installed in
  the core service. UVM resolves the requested type through its own type and
  instance overrides first; the factory then substitutes the woven class of the
  *resolved* type for the profile chosen with ``+weave_profile=<p>`` (default: the
  config's ``default-profile``). The result does not depend on registration order,
  unlike plain ``set_type_override``.

The user class must be registered with the factory (`` `uvm_object_utils ``); a woven
class of an unregistered class is generated but not registered (a warning).
"""
import os
from typing import Dict

from sv_weave.plugin import Binding, FeatureSpec

from . import SV_DIR
from .__version__ import __version__


def _q(s: str) -> str:
    return '"%s"' % s.replace('"', '\\"')


def _registered(cls) -> bool:
    """The class itself declares get_type(), i.e. it uses `uvm_object_utils."""
    return any(m.name == "get_type" and m.static for m in cls.methods)


class UvmBinding(Binding):
    name = "uvm"
    version = __version__
    roots = ("uvm_pkg::uvm_object",)

    def features(self) -> Dict[str, FeatureSpec]:
        return {
            "copy": FeatureSpec("copy", "do_copy", args=("uvm_object rhs",),
                                arg_names=("rhs",), rhs="rhs"),
            "compare": FeatureSpec("compare", "do_compare",
                                   args=("uvm_object rhs", "uvm_comparer comparer"),
                                   arg_names=("rhs", "comparer"), ret="bit", rhs="rhs"),
            "print": FeatureSpec("print", "convert2string", ret="string"),
        }

    def sv_runtime_files(self):
        return [os.path.join(SV_DIR, "sv_weave_uvm_pkg.sv")]

    def preamble(self):
        return ['`include "uvm_macros.svh"']

    def imports(self):
        return ["uvm_pkg"]

    def create_expr(self, cls, inst: str = ""):
        if _registered(cls) and cls.type_expr:
            return "%s::type_id::create(%s)" % (cls.type_expr, inst or '""')
        return None

    def miscompare_stmt(self, cls, field: str) -> str:
        return ('uvm_pkg::uvm_report_info("sv-weave", "compare: %s.%s differs", '
                'uvm_pkg::UVM_HIGH);' % (cls.qname, field))

    def finalize(self, w) -> None:
        if not _registered(w.cls):
            w.warning("%s is not registered with the UVM factory (no `uvm_object_utils); "
                      "its woven class will not be used" % w.cls.qname, w.cls.loc)
        # The *_param_utils form registers the woven class by type only: it gets no
        # factory name of its own and inherits get_type_name()/type_name() from the
        # user's class, so logs and factory.print() show the original name.
        macro = "uvm_component_param_utils" if w.cls.is_a("uvm_pkg::uvm_component") else \
            "uvm_object_param_utils"
        w.add_item("`%s(%s)" % (macro, w.woven.name))

    def package_items(self, wpkg, cfg):
        regs = [wc for wc in wpkg.classes
                if wc.concrete and wc.target.binding == self.name and _registered(wc.cls)]
        if not regs:
            return []
        stmts = ["begin",
                 "  sv_weave_uvm_pkg::sv_weave_uvm_factory f = "
                 "sv_weave_uvm_pkg::sv_weave_uvm_factory::install();",
                 "  f.set_config_default(%s);" % _q(cfg.default_profile)]
        for wc in regs:
            for prof in wc.profiles:
                stmts.append("  f.add(%s::get_type(), %s, %s::get_type());"
                             % (wc.cls.type_expr, _q(prof), wc.name))
        stmts.append("end")
        return stmts
