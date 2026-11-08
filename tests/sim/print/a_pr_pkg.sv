`include "uvm_macros.svh"
package pr_pkg;
  import uvm_pkg::*;

  typedef enum bit [1:0] {READ, WRITE, IDLE} kind_e;

  class pr_sub extends uvm_object;
    `uvm_object_utils(pr_sub)
    bit [15:0] id;
    function new(string name = "pr_sub");
      super.new(name);
    endfunction
  endclass

  class pr_tx extends uvm_sequence_item;
    `uvm_object_utils(pr_tx)
    bit [7:0] addr;
    logic [99:0] wide;
    int cnt;
    kind_e kind;
    string tag;
    real ratio;
    int q[$];
    (* weave_deep *) pr_sub sub;
    pr_sub ref_h;
    (* weave_noprint *) int secret;
    function new(string name = "pr_tx");
      super.new(name);
    endfunction
  endclass
endpackage
