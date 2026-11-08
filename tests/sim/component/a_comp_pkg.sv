`include "uvm_macros.svh"
package comp_pkg;
  import uvm_pkg::*;

  class tx extends uvm_sequence_item;
    `uvm_object_utils(tx)
    rand bit [7:0] addr;
    function new(string name = "tx");
      super.new(name);
    endfunction
  endclass

  // A parameterized class, registered with *_param_utils (no factory name).
  class p_tx #(int W = 8) extends uvm_sequence_item;
    `uvm_object_param_utils(p_tx#(W))
    bit [W-1:0] data;
    function new(string name = "p_tx");
      super.new(name);
    endfunction
  endclass

  class my_driver extends uvm_driver #(tx);
    `uvm_component_utils(my_driver)
    int n_items;
    function new(string name, uvm_component parent);
      super.new(name, parent);
    endfunction
  endclass

  class my_agent extends uvm_agent;
    `uvm_component_utils(my_agent)
    my_driver drv;
    function new(string name, uvm_component parent);
      super.new(name, parent);
    endfunction
    function void build_phase(uvm_phase phase);
      drv = my_driver::type_id::create("drv", this);
    endfunction
  endclass

  class my_env extends uvm_env;
    `uvm_component_utils(my_env)
    my_agent agent;
    function new(string name, uvm_component parent);
      super.new(name, parent);
    endfunction
    function void build_phase(uvm_phase phase);
      agent = my_agent::type_id::create("agent", this);
    endfunction
  endclass

  class my_test extends uvm_test;
    `uvm_component_utils(my_test)
    my_env env;
    function new(string name, uvm_component parent);
      super.new(name, parent);
    endfunction
    function void build_phase(uvm_phase phase);
      env = my_env::type_id::create("env", this);
    endfunction
  endclass
endpackage
