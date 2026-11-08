// seed: with the same seed, the release and the debug profile randomise to the same
// values. The debug set (xcheck) runs after randomize() but consumes no random numbers,
// so neither the object's RNG nor the thread's ($urandom after the loop) moves.
`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import sd_pkg::*;

  sv_weave_init_m u_init();

  initial begin
    sd_tx t, c;
    sv_weave_uvm_pkg::sv_weave_uvm_factory wf;

    t = sd_tx::type_id::create("t");
    `CHECK_WOVEN(t, sd_tx, "sd_tx")
    t.srandom(1234);
    for (int i = 0; i < 4; i++) begin
      `CHECK(t.randomize(), "randomize")
      $display("VALUES %0d: %h %h %s %0d %p %h", i, t.addr, t.data, t.kind.name(), t.len,
               t.payload, t.sub.id);
      $cast(c, t.clone());
      `CHECK(c.compare(t), "clone compares equal")
    end
    $display("URANDOM %h", $urandom);
    // The woven class of the selected profile was created (debug and release are
    // different classes: xcheck applies to sd_tx's logic fields).
    $cast(wf, uvm_factory::get());
    `CHECK(t.get_object_type() == wf.woven_of(sd_tx::get_type()), "woven class of the profile")
    $display("IMPL %s", wf.profile());
    check_pkg::pass();
    $finish;
  end
endmodule
