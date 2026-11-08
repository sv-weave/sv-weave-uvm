`include "uvm_macros.svh"
package tx_pkg;
  import uvm_pkg::*;

  // A plain UVM transaction: no field macros, no do_copy/do_compare/do_print.
  class tx extends uvm_sequence_item;
    `uvm_object_utils(tx)
    rand bit [7:0]  addr;
    rand bit [31:0] data;
    byte            payload[$];
    function new(string name = "tx");
      super.new(name);
    endfunction
  endclass
endpackage
