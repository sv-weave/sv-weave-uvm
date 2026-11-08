`include "uvm_macros.svh"
package tx_pkg;
  import uvm_pkg::*;

  class tx extends uvm_sequence_item;
    `uvm_object_utils(tx)
    rand bit [7:0] addr;
    function new(string name = "tx");
      super.new(name);
    endfunction
  endclass

  class tx1 extends tx;
    `uvm_object_utils(tx1)
    int one;
    function new(string name = "tx1");
      super.new(name);
    endfunction
  endclass

  class tx2 extends tx1;
    `uvm_object_utils(tx2)
    int two;
    function new(string name = "tx2");
      super.new(name);
    endfunction
  endclass
endpackage
