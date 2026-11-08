import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "assess"))

import scan  # noqa: E402
import size  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "items.sv")


def _rows(roots):
    res = size.size_report(scan.scan_tree(roots))
    return {r["class"]: r for r in res["classes"]}, res


def test_macro_and_hand_rows():
    rows, _ = _rows([FIXTURE])
    assert set(rows) == {"macro_item", "hand_item", "cfg_obj", "pack_item"}
    m = rows["macro_item"]
    # utils_begin/end + 3 field lines; sv-weave keeps the utils line and one
    # attribute for the UVM_NOCOMPARE field
    assert (m["macro_src"], m["hand_src"], m["weave_src"], m["saved"]) == (5, 0, 2, 3)
    assert m["macro_exp"] == (size.UTILS_BEGIN_END_EXP + size.MACRO_EXP["int"]
                              + size.MACRO_EXP["sarray_int"] + size.MACRO_EXP["enum"])
    assert m["woven_gen"] == 3 * size.WOVEN_PER_MEMBER  # static count is skipped
    h = rows["hand_item"]
    # in-class do_copy (6 lines) + extern do_compare body (5 lines)
    assert (h["macro_src"], h["hand_src"], h["weave_src"]) == (0, 11, 0)
    assert all(r["category"] == "data" for r in rows.values())


def test_groups(tmp_path):
    for agent in ("a_agent", "b_agent"):
        os.makedirs(tmp_path / agent / "seq_lib")
    shutil.copy(FIXTURE, tmp_path / "a_agent" / "items.sv")
    shutil.copy(FIXTURE, tmp_path / "b_agent" / "seq_lib" / "items.sv")
    rows, res = _rows([str(tmp_path)])
    root = str(tmp_path)
    assert set(res["groups"]) == {root + ":a_agent", root + ":b_agent"}
    a = res["groups"][root + ":a_agent"]["data"]
    assert (a["classes"], a["saved"]) == (4, 24)
    assert res["totals"][root]["all"]["saved"] == 48
    text = size.text_report(res)
    assert "test_groups0/b_agent " in text and "TOTAL test_groups0 " in text
    assert size.macro_exp("queue_enum") == size.MACRO_EXP["queue_int"]
