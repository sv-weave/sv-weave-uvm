import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "assess"))

import scan  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "items.sv")


def _classes():
    res = scan.scan_tree([FIXTURE])
    assert res["errors"] == []
    return {c["name"]: c for c in res["classes"]}


def test_members_and_field_macros():
    c = _classes()["macro_item"]
    assert c["line"] == 2 and c["category"] == "object"
    mb = {m["name"]: m for m in c["members"]}
    assert set(mb) == {"addr", "data", "kind", "count"}
    assert mb["addr"]["rand"] and not mb["kind"]["rand"]
    assert mb["count"]["static"] and mb["data"]["dims"] == "[4]"
    f = {x["member"]: x for x in c["fields"]}
    assert set(f) == {"addr", "data", "kind"}
    assert f["data"]["kind"] == "sarray_int"
    assert f["data"]["flags"] == ["UVM_DEFAULT", "UVM_NOCOMPARE"]
    assert f["kind"]["kind"] == "enum" and f["addr"]["line"] == 8
    assert c["utils"] == "uvm_object_utils_begin"
    assert c["field_macro_lines"] == 5


def test_hand_methods_inline_and_extern():
    c = _classes()["hand_item"]
    assert c["uvm_root"] == "uvm_sequence_item" and c["fields"] == []
    m = {x["name"]: x for x in c["methods"]}
    assert m["do_copy"]["super_call"] and m["do_copy"]["members"] == ["len"]
    assert m["do_copy"]["lines"] == 6
    # extern body is attached to its class and replaces the prototype
    assert m["do_compare"]["line"] == 34 and not m["do_compare"]["super_call"]
    assert m["do_compare"]["members"] == ["flag", "len"]


def test_categories_and_params():
    cs = _classes()
    assert cs["cfg_obj"]["parameterized"]
    assert cs["cfg_obj"]["members"][0]["local"]
    assert cs["cfg_obj"]["methods"][0]["members"] == ["depth"]
    assert cs["cfg_obj"]["utils"] == "uvm_object_param_utils"
    assert cs["my_drv"]["category"] == "component"
