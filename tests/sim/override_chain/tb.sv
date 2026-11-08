// override_chain: a 2-link override chain (tx -> tx1 -> tx2). UVM's factory resolves a
// chain by recursing through the virtual find_override_by_type/name, so the adapter's
// override runs on every link; the result must still be the woven form of the last link.
`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import tx_pkg::*;

  sv_weave_init_m u_init();

  initial begin
    tx a, b;
    uvm_object o;
    uvm_factory f;
    // Not an initializer: that runs before sv_weave_init_m installs the woven factory.
    f = uvm_factory::get();

    // Instance chain by type, scoped to "i".
    f.set_inst_override_by_type(tx::get_type(), tx1::get_type(), "i");
    f.set_inst_override_by_type(tx1::get_type(), tx2::get_type(), "i");
    a = tx::type_id::create("i");
    `CHECK_WOVEN(a, tx2, "instance chain by type, then woven")
    a = tx::type_id::create("j");
    `CHECK_WOVEN(a, tx, "other instances unaffected")

    // Type chain by type.
    f.set_type_override_by_type(tx::get_type(), tx1::get_type());
    f.set_type_override_by_type(tx1::get_type(), tx2::get_type());
    a = tx::type_id::create("a");
    `CHECK_WOVEN(a, tx2, "type chain by type, then woven")
    b = tx::type_id::create("b");
    a.addr = 8'h5a;
    b.copy(a);
    `CHECK(b.compare(a), "woven do_copy/do_compare on the chain's result")

    // Creating by name walks the same chain.
    o = f.create_object_by_name("tx", "", "o");
    `CHECK_WOVEN(o, tx2, "create by name follows the chain")
    check_pkg::pass();
    $finish;
  end
endmodule
