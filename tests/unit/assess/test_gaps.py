import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "assess"))

import gaps  # noqa: E402
import scan  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "items.sv")


def _findings():
    res = gaps.find_gaps(scan.scan_tree([FIXTURE]))
    return {(f["class"], f["rule"], f["member"]) for f in res["findings"]}, res


def test_macro_item_clean():
    fs, _ = _findings()
    # data is UVM_NOCOMPARE: copied but not compared on purpose
    assert not [f for f in fs if f[0] == "macro_item"]


def test_hand_item_gaps():
    fs, _ = _findings()
    got = {f for f in fs if f[0] == "hand_item"}
    assert got == {("hand_item", "G1", "flag"), ("hand_item", "G2", "flag"),
                   ("hand_item", "G3", "len"), ("hand_item", "G4", None)}


def test_print_only_pack_and_bare():
    fs, res = _findings()
    assert ("cfg_obj", "G1", "depth") in fs
    assert ("cfg_obj", "G4", None) not in fs  # base is uvm_object
    assert ("pack_item", "G6", "b") in fs
    assert ("pack_item", "G6", "a") not in fs
    assert ("bare_cfg", "G5", None) in fs  # vif is not a data member
    g5 = [f for f in res["findings"] if f["class"] == "bare_cfg"]
    assert len(g5) == 1 and g5[0]["msg"].startswith("1 data members")
    assert not [f for f in fs if f[0] == "my_drv"]  # components are skipped
    assert "hand_item.flag: not copied" in gaps.text_report(res)
