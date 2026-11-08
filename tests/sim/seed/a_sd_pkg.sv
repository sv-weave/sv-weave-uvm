`include "uvm_macros.svh"
package sd_pkg;
  import uvm_pkg::*;

  typedef enum bit [1:0] {READ, WRITE, IDLE} kind_e;

  class sd_sub extends uvm_object;
    `uvm_object_utils(sd_sub)
    rand logic [15:0] id;
    function new(string name = "sd_sub");
      super.new(name);
    endfunction
  endclass

  class sd_tx extends uvm_sequence_item;
    `uvm_object_utils(sd_tx)
    rand bit [7:0] addr;
    rand logic [31:0] data;
    rand kind_e kind;
    rand int unsigned len;
    rand bit [7:0] payload[4];
    (* weave_deep, weave_nocompare *) rand sd_sub sub;
    constraint c_len { len inside {[1:4]}; }
    function new(string name = "sd_tx");
      super.new(name);
      sub = sd_sub::type_id::create("sub");
    endfunction
  endclass
endpackage
