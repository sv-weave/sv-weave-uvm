// Benchmark variant 1: the sequence item with `uvm_field_* automation macros.
`include "uvm_macros.svh"
package bm_macros_pkg;
  import uvm_pkg::*;

  typedef enum bit [1:0] {READ, WRITE, IDLE} kind_e;

  class bm_tx extends uvm_sequence_item;
    rand bit [31:0] addr;
    rand bit [31:0] data;
    rand kind_e kind;
    rand bit [3:0] be;
    rand int unsigned delay;
    rand byte payload[8];
    int id;
    string tag;
    `uvm_object_utils_begin(bm_tx)
      `uvm_field_int(addr, UVM_ALL_ON)
      `uvm_field_int(data, UVM_ALL_ON)
      `uvm_field_enum(kind_e, kind, UVM_ALL_ON)
      `uvm_field_int(be, UVM_ALL_ON)
      `uvm_field_int(delay, UVM_ALL_ON)
      `uvm_field_sarray_int(payload, UVM_ALL_ON)
      `uvm_field_int(id, UVM_ALL_ON)
      `uvm_field_string(tag, UVM_ALL_ON)
    `uvm_object_utils_end
    function new(string name = "bm_tx");
      super.new(name);
    endfunction
  endclass
endpackage
