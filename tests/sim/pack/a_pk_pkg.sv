`include "uvm_macros.svh"
package pk_pkg;
  import uvm_pkg::*;

  typedef enum bit [1:0] {READ, WRITE, IDLE} kind_e;
  typedef struct packed { bit [3:0] hi; bit [3:0] lo; } nib_s;

  class pk_sub extends uvm_object;
    `uvm_object_utils(pk_sub)
    bit [15:0] id;
    function new(string name = "pk_sub");
      super.new(name);
    endfunction
  endclass

  class pk_tx extends uvm_sequence_item;
    `uvm_object_utils(pk_tx)
    bit [7:0] addr;
    logic [99:0] wide;
    int cnt;
    kind_e kind;
    nib_s nib;
    string tag;
    real ratio;
    int q[$];
    byte da[];
    bit [3:0] fa[4];
    string sq[$];
    // weave_nocompare: core deep compare calls do_compare(rhs) without the comparer.
    (* weave_deep, weave_nocompare *) pk_sub sub;
    (* weave_nopack, weave_nocompare *) int secret;
    function new(string name = "pk_tx");
      super.new(name);
    endfunction
  endclass
endpackage
