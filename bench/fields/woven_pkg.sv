// Benchmark variant 3: the same sequence item with no field code; sv-weave writes
// do_copy/do_compare/do_print/do_pack/do_unpack/convert2string (see sv-weave.yaml).
`include "uvm_macros.svh"
package bm_woven_pkg;
  import uvm_pkg::*;

  typedef enum bit [1:0] {READ, WRITE, IDLE} kind_e;

  class bm_tx extends uvm_sequence_item;
    `uvm_object_utils(bm_tx)
    rand bit [31:0] addr;
    rand bit [31:0] data;
    rand kind_e kind;
    rand bit [3:0] be;
    rand int unsigned delay;
    rand byte payload[8];
    int id;
    string tag;
    function new(string name = "bm_tx");
      super.new(name);
    endfunction
  endclass
endpackage
