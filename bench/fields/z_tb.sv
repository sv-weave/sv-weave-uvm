// Runtime benchmark: +bm_variant=macros|hand|woven|none, +bm_n=<iterations>.
// Each iteration: randomize, copy, compare, pack/unpack + compare, sprint, convert2string.
// The compares check that the three variants behave alike; `none` runs no loop (UVM
// start-up cost, subtracted by the driver).
`include "uvm_macros.svh"

`define BM_LOOP(PKG, T) \
  begin \
    PKG::T a, b, c; \
    bit bits[]; \
    string s; \
    int chars; \
    a = PKG::T::type_id::create("a"); \
    b = PKG::T::type_id::create("b"); \
    c = PKG::T::type_id::create("c"); \
    a.srandom(1); \
    for (int i = 0; i < n; i++) begin \
      `CHECK(a.randomize() == 1, "randomize") \
      a.id = i; \
      a.tag = i[0] ? "odd" : "even"; \
      b.copy(a); \
      `CHECK(b.compare(a), "copy compares equal") \
      void'(a.pack(bits)); \
      void'(c.unpack(bits)); \
      `CHECK(c.compare(a), "unpack compares equal") \
      s = a.sprint(); \
      chars += s.len(); \
      s = a.convert2string(); \
      chars += s.len(); \
    end \
    $display("BM %s n=%0d bits=%0d chars=%0d", `"PKG`", n, bits.size(), chars); \
  end

module tb;
  import uvm_pkg::*;

  sv_weave_init_m u_init();

  initial begin
    string variant = "none";
    int n = 1000;
    void'($value$plusargs("bm_variant=%s", variant));
    void'($value$plusargs("bm_n=%d", n));
    case (variant)
      "macros": `BM_LOOP(bm_macros_pkg, bm_macros_tx)
      "hand": `BM_LOOP(bm_hand_pkg, bm_hand_tx)
      "woven": begin
        bm_woven_pkg::bm_woven_tx t;
        t = bm_woven_pkg::bm_woven_tx::type_id::create("t");
        `CHECK_WOVEN(t, bm_woven_pkg::bm_woven_tx, "bm_woven_tx")
        `BM_LOOP(bm_woven_pkg, bm_woven_tx)
      end
      "none": $display("BM none");
      default: `CHECK(0, {"unknown +bm_variant=", variant})
    endcase
    check_pkg::pass();
    $finish;
  end
endmodule
