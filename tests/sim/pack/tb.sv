// pack: the pack weaver writes do_pack/do_unpack through uvm_packer, so pack_ints /
// pack_bytes followed by unpack_ints / unpack_bytes round-trip every field: integral,
// >64 bits, enum, packed struct, string, real, queue, dynamic and fixed arrays, and a
// weave_deep object (created on unpack). weave_nopack fields are left out.
`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import pk_pkg::*;

  sv_weave_init_m u_init();

  initial begin
    pk_tx a, b, c;
    int unsigned ints[];
    byte unsigned bytes[];
    int n;

    a = pk_tx::type_id::create("a");
    `CHECK_WOVEN(a, pk_tx, "pk_tx")
    a.addr = 8'h3c;
    a.wide = {4'h9, 96'h1234_5678_9abc_def0_1122_3344};
    a.cnt = -3;
    a.kind = IDLE;
    a.nib = '{hi: 4'ha, lo: 4'h5};
    a.tag = "hello";
    a.ratio = 0.25;
    a.q = '{7, 8, 9};
    a.da = new[2];
    a.da[0] = 8'h11;
    a.da[1] = -8'sd2;
    a.fa = '{4'h1, 4'h2, 4'h3, 4'h4};
    a.sq = '{"x", "yz"};
    a.sub = pk_sub::type_id::create("sub");
    a.sub.id = 16'hcafe;
    a.secret = 42;

    n = a.pack_ints(ints);
    `CHECK(n > 0, "pack_ints packed something")
    b = pk_tx::type_id::create("b");
    b.q = '{1, 2, 3, 4, 5};  // longer than a.q: unpack must shrink it
    void'(b.unpack_ints(ints));
    `CHECK(b.sub != null, "weave_deep object created on unpack")
    `CHECK_EQ(b.sub.id, 16'hcafe, "deep object field")
    `CHECK_EQ(b.wide, a.wide, ">64-bit field")
    `CHECK_EQ(b.kind, IDLE, "enum")
    `CHECK_EQ(b.nib.hi, 4'ha, "packed struct")
    `CHECK_EQ(b.tag, "hello", "string")
    `CHECK(b.ratio == 0.25, "real")
    `CHECK_EQ(b.q.size(), 3, "queue size")
    `CHECK_EQ(b.da[1], 8'hfe, "dynamic array")
    `CHECK_EQ(b.fa[3], 4'h4, "fixed array")
    `CHECK_EQ(b.sq[1], "yz", "string queue")
    `CHECK_EQ(b.secret, 0, "weave_nopack field left out")
    `CHECK(b.compare(a), "round trip through pack_ints/unpack_ints")

    void'(a.pack_bytes(bytes));
    c = pk_tx::type_id::create("c");
    void'(c.unpack_bytes(bytes));
    `CHECK(c.compare(a), "round trip through pack_bytes/unpack_bytes")
    `CHECK_EQ(c.cnt, -3, "signed int")
    check_pkg::pass();
    $finish;
  end
endmodule
