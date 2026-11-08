import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "assess"))

import gaps  # noqa: E402
import report  # noqa: E402
import scan  # noqa: E402
import size  # noqa: E402


def test_code_lines_comments_and_blanks():
    text = "\n".join([
        "class a;      // trailing comment",
        "",
        "  // whole-line comment",
        "  /* block",
        "     still block */",
        "  int x; /* inline */",
        "   ",
        "endclass",
    ])
    assert report.code_lines(text) == [True, False, False, False, False, True, False, True]


def test_code_lines_code_after_block_comment():
    assert report.code_lines("/* a\n b */ int x;\n") == [False, True, False]


ITEM = """\
class ext_item extends uvm_sequence_item;
  rand bit [7:0] a;
  rand bit [7:0] b;
  `uvm_object_utils(ext_item)
  extern function void do_copy(uvm_object rhs);
endclass

// out-of-class body
function void ext_item::do_copy(uvm_object rhs);
  ext_item rhs_;
  super.do_copy(rhs);
  $cast(rhs_, rhs);

  a = rhs_.a;
  b = rhs_.b;
endfunction
"""


def test_extern_body_counts_in_class_lines(tmp_path):
    p = tmp_path / "ext_item.sv"
    p.write_text(ITEM)
    sc = scan.scan_tree([str(tmp_path)])
    sz = size.size_report(sc)
    g = gaps.find_gaps(sc)
    n = report.tree_numbers("cv", sc, sz, g)
    assert n["data_classes"] == 1
    # 6 class lines (all code) + 7 code lines of the extern body (blank excluded).
    assert n["data_lines"] == 13
    # The hand body is counted in code lines too, so saved never exceeds the class.
    assert n["hand_src"] == 7
    assert n["saved"] <= n["data_lines"]
