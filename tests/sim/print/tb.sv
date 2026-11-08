// print: the do_print weaver prints every field through uvm_printer, so print() and
// sprint() show them with the table, tree and line printers; convert2string (the core
// print weaver) still works next to it.
`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import pr_pkg::*;

  sv_weave_init_m u_init();

  initial begin
    pr_tx t;
    string s;

    t = pr_tx::type_id::create("t");
    `CHECK_WOVEN(t, pr_tx, "pr_tx")
    t.addr = 8'h3c;
    t.wide = 100'h1;
    t.cnt = -3;
    t.kind = WRITE;
    t.tag = "hello";
    t.ratio = 0.5;
    t.q = '{7, 8};
    t.sub = pr_sub::type_id::create("sub");
    t.sub.id = 16'hcafe;
    t.secret = 42;

    s = t.sprint();  // default: table printer
    $display("%s", s);
    `CHECK_HAS(s, "pr_tx", "table: type name")
    `CHECK_HAS(s, "addr", "table: addr")
    `CHECK_HAS(s, "'h3c", "table: addr value")
    `CHECK_HAS(s, "wide", "table: >64-bit field")
    `CHECK_HAS(s, "-3", "table: signed int in decimal")
    `CHECK_HAS(s, "WRITE", "table: enum name")
    `CHECK_HAS(s, "kind_e", "table: enum type")
    `CHECK_HAS(s, "hello", "table: string")
    `CHECK_HAS(s, "0.5", "table: real")
    `CHECK_HAS(s, $sformatf("%p", t.q), "table: queue")
    `CHECK_HAS(s, "'hcafe", "table: deep object printed nested")
    `CHECK_HAS(s, "ref_h", "table: reference field")
    `CHECK_HAS(s, "<null>", "table: null reference")
    `CHECK(!check_pkg::has(s, "secret"), "table: weave_noprint field left out")

    s = t.sprint(uvm_tree_printer::get_default());
    $display("%s", s);
    `CHECK_HAS(s, "addr: 'h3c", "tree printer")

    s = t.sprint(uvm_line_printer::get_default());
    $display("%s", s);
    `CHECK_HAS(s, "tag: hello", "line printer")

    s = t.convert2string();
    `CHECK_HAS(s, "addr: 'h3c", "convert2string kept")
    check_pkg::pass();
    $finish;
  end
endmodule
