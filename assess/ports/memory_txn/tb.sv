// memory_txn (core-v-verif) as written vs ported to sv-weave. The original registers only
// the two timing fields, so copy() drops id/addr/data/strb/err/ex_fail/cmd/atop and
// compare() cannot see a data mismatch. The port, with no field code at all, gets both.
`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import mrm_types_pkg::*;

  typedef mrm_orig_pkg::memory_txn #(32, 64, 4)    orig_t;
  typedef mrm_port_pkg::memory_txn_sw #(32, 64, 4) port_t;

  sv_weave_init_m u_init();

  initial begin
    orig_t oa, ob;
    port_t pa, pb;
    string s;

    // The original: the gaps assess/gaps.py reports (G1 x8) are real.
    oa = orig_t::type_id::create("oa");
    oa.id = 4'h3; oa.addr = 32'h1000; oa.data = 64'hdead_beef; oa.strb = 8'hff;
    oa.err = 1; oa.cmd = MEM_ATOMIC; oa.atop = MEM_ATOMIC_SWAP;
    oa.req_arrival_time = 7; oa.global_transmit_time = 9;
    ob = orig_t::type_id::create("ob");
    ob.copy(oa);
    `CHECK_EQ(ob.req_arrival_time, 7, "orig copy: registered field copied")
    `CHECK_EQ(ob.addr, 32'h0, "orig copy: addr dropped")
    `CHECK_EQ(ob.data, 64'h0, "orig copy: data dropped")
    `CHECK(ob.cmd == MEM_WRITE, "orig copy: cmd dropped")
    `CHECK(ob.compare(oa), "orig compare: misses addr/data/cmd differences")

    // The port: woven copy/compare/print cover every field.
    pa = port_t::type_id::create("pa");
    `CHECK(pa.get_object_type() != port_t::get_type(), "port: factory returns woven class")
    pa.id = 4'h3; pa.addr = 32'h1000; pa.data = 64'hdead_beef; pa.strb = 8'hff;
    pa.err = 1; pa.ex_fail = 1; pa.cmd = MEM_ATOMIC; pa.atop = MEM_ATOMIC_SWAP;
    pa.req_arrival_time = 7; pa.global_transmit_time = 9; pa.req_ts = 11; pa.resp_ts = 12;
    pb = port_t::type_id::create("pb");
    pb.copy(pa);
    `CHECK_EQ(pb.id, 4'h3, "port copy: id")
    `CHECK_EQ(pb.addr, 32'h1000, "port copy: addr")
    `CHECK_EQ(pb.data, 64'hdead_beef, "port copy: data")
    `CHECK_EQ(pb.strb, 8'hff, "port copy: strb")
    `CHECK_EQ(pb.err, 1'b1, "port copy: err")
    `CHECK_EQ(pb.ex_fail, 1'b1, "port copy: ex_fail")
    `CHECK(pb.cmd == MEM_ATOMIC, "port copy: cmd")
    `CHECK(pb.atop == MEM_ATOMIC_SWAP, "port copy: atop")
    `CHECK_EQ(pb.req_arrival_time, 7, "port copy: req_arrival_time")
    `CHECK_EQ(pb.resp_ts, 12, "port copy: resp_ts")
    `CHECK(pb.compare(pa), "port compare: equal after copy")
    pb.data = 0;
    `CHECK(!pb.compare(pa), "port compare: data difference detected")
    pb.data = pa.data; pb.atop = MEM_ATOMIC_ADD;
    `CHECK(!pb.compare(pa), "port compare: atop difference detected")
    s = pa.sprint();
    `CHECK_HAS(s, "addr", "port print: addr")
    `CHECK_HAS(s, "atop", "port print: atop")
    $display("%s", s);
    `CHECK_HAS(pa.convert2string(), "ADDR", "port: hand convert2string kept")
    check_pkg::pass();
  end
endmodule
