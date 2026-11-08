// component: woven uvm_component classes. run_test() creates the test by name, and each
// level's build_phase creates the next with type_id::create(name, this):
// test -> env -> agent -> driver, each the woven form of its class, in the right place
// in the hierarchy. Also a parameterized class (`uvm_object_param_utils).
`include "uvm_macros.svh"
module tb;
  import uvm_pkg::*;
  import comp_pkg::*;

  sv_weave_init_m u_init();

  initial begin
    uvm_root top;
    my_test t;
    tx a, b;
    p_tx #(16) p, q;

    p = p_tx#(16)::type_id::create("p");
    // A *_param_utils class has no type_name (UVM 2020), so no CHECK_WOVEN here.
    `CHECK(p.get_object_type() != p_tx#(16)::get_type(), "parameterized class: woven")
    p.data = 16'hbeef;
    q = p_tx#(16)::type_id::create("q");
    q.copy(p);
    `CHECK_EQ(q.data, 16'hbeef, "parameterized class: do_copy")
    `CHECK(q.compare(p), "parameterized class: do_compare")

    // Keep run_test from calling $finish, so the checks below run after the phases.
    top = uvm_root::get();
    top.finish_on_completion = 0;
    run_test("my_test");

    `CHECK($cast(t, top.find("uvm_test_top")), "run_test created my_test")
    `CHECK_WOVEN(t, my_test, "test")
    `CHECK_WOVEN(t.env, my_env, "env")
    `CHECK_WOVEN(t.env.agent, my_agent, "agent")
    `CHECK_WOVEN(t.env.agent.drv, my_driver, "driver")
    `CHECK_EQ(t.env.agent.drv.get_full_name(), "uvm_test_top.env.agent.drv", "driver path")
    `CHECK(t.env.agent.drv.get_parent() == t.env.agent, "driver parent")

    // Objects still work next to components.
    a = tx::type_id::create("a");
    `CHECK_WOVEN(a, tx, "sequence item")
    a.addr = 8'h3c;
    b = tx::type_id::create("b");
    b.copy(a);
    `CHECK(b.compare(a), "sequence item: do_copy/do_compare")
    check_pkg::pass();
    $finish;
  end
endmodule
