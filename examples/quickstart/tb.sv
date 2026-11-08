`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import tx_pkg::*;

  sv_weave_init_m u_init();   // installs the woven factory at time 0

  initial begin
    tx a, b;
    a = tx::type_id::create("a");
    void'(a.randomize());
    a.payload = '{1, 2, 3};
    b = tx::type_id::create("b");
    b.copy(a);                 // woven do_copy
    if (!b.compare(a)) `uvm_fatal("QS", "copy/compare failed")
    b.data++;
    if (b.compare(a)) `uvm_fatal("QS", "compare missed a difference")
    a.print();                 // woven do_print
    $display("%s", a.convert2string());
    $display("QUICKSTART: PASS");
    $finish;
  end
endmodule
