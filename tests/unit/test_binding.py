"""UvmBinding without a simulator: discovery, the API gate, features and generated text."""
import os
from types import SimpleNamespace as NS

from sv_weave import plugin

from sv_weave_uvm.binding import UvmBinding


def _cls(registered=True, qname="tx_pkg::my_tx", type_expr="tx_pkg::my_tx"):
    methods = [NS(name="get_type", static=True)] if registered else []
    return NS(methods=methods, qname=qname, type_expr=type_expr)


def test_entry_point_discovery():
    assert plugin.find(plugin.BINDING_GROUP, "uvm") is UvmBinding


def test_api_gate():
    plugin.check_api("binding", UvmBinding)


def test_features_map_to_uvm_hooks():
    f = UvmBinding().features()
    assert {k: v.method for k, v in f.items()} == {
        "copy": "do_copy", "compare": "do_compare", "print": "convert2string"}
    assert f["compare"].ret == "bit"
    assert f["compare"].arg_names == ("rhs", "comparer")
    assert f["copy"].rhs == "rhs"


def test_runtime_file_is_shipped():
    files = UvmBinding().sv_runtime_files()
    assert [os.path.basename(p) for p in files] == ["sv_weave_uvm_pkg.sv"]
    assert os.path.isfile(files[0])


def test_preamble_and_imports():
    b = UvmBinding()
    assert b.preamble() == ['`include "uvm_macros.svh"']
    assert b.imports() == ["uvm_pkg"]


def test_create_expr_uses_factory_only_when_registered():
    b = UvmBinding()
    assert b.create_expr(_cls(), "inst") == "tx_pkg::my_tx::type_id::create(inst)"
    assert b.create_expr(_cls(), "") == 'tx_pkg::my_tx::type_id::create("")'
    assert b.create_expr(_cls(registered=False)) is None


def test_miscompare_reports_at_uvm_high():
    s = UvmBinding().miscompare_stmt(_cls(), "addr")
    assert "tx_pkg::my_tx.addr" in s and "UVM_HIGH" in s


def test_package_items_register_each_profile():
    wc = NS(concrete=True, target=NS(binding="uvm"), cls=_cls(),
            profiles=["release", "debug"], name="Woven_my_tx")
    other = NS(concrete=True, target=NS(binding="reflib"), cls=_cls(), profiles=["release"],
               name="Woven_x")
    out = UvmBinding().package_items(NS(classes=[wc, other]), NS(default_profile="release"))
    assert out[0] == "begin" and out[-1] == "end"
    assert '  f.set_config_default("release");' in out
    assert '  f.add(tx_pkg::my_tx::get_type(), "debug", Woven_my_tx::get_type());' in out
    assert not any("Woven_x" in s for s in out)


def test_package_items_empty_without_registered_classes():
    wc = NS(concrete=True, target=NS(binding="uvm"), cls=_cls(registered=False),
            profiles=["release"], name="Woven_my_tx")
    assert UvmBinding().package_items(NS(classes=[wc]), NS(default_profile="release")) == []
