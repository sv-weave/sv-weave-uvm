// Benchmark variant 2: the same sequence item with hand-written do_* methods.
`include "uvm_macros.svh"
package bm_hand_pkg;
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

    virtual function void do_copy(uvm_object rhs);
      bm_tx r;
      super.do_copy(rhs);
      if (!$cast(r, rhs)) `uvm_fatal("COPY", "type mismatch")
      addr = r.addr; data = r.data; kind = r.kind; be = r.be;
      delay = r.delay; payload = r.payload; id = r.id; tag = r.tag;
    endfunction

    virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
      bm_tx r;
      if (!$cast(r, rhs)) return 0;
      return super.do_compare(rhs, comparer)
          && addr == r.addr && data == r.data && kind == r.kind && be == r.be
          && delay == r.delay && payload == r.payload && id == r.id && tag == r.tag;
    endfunction

    virtual function void do_print(uvm_printer printer);
      super.do_print(printer);
      printer.print_field_int("addr", addr, 32, UVM_HEX);
      printer.print_field_int("data", data, 32, UVM_HEX);
      printer.print_string("kind", kind.name());
      printer.print_field_int("be", be, 4, UVM_HEX);
      printer.print_field_int("delay", delay, 32, UVM_DEC);
      foreach (payload[i])
        printer.print_field_int($sformatf("payload[%0d]", i), payload[i], 8, UVM_HEX);
      printer.print_field_int("id", id, 32, UVM_DEC);
      printer.print_string("tag", tag);
    endfunction

    virtual function void do_pack(uvm_packer packer);
      super.do_pack(packer);
      packer.pack_field_int(addr, 32);
      packer.pack_field_int(data, 32);
      packer.pack_field_int(kind, 2);
      packer.pack_field_int(be, 4);
      packer.pack_field_int(delay, 32);
      foreach (payload[i]) packer.pack_field_int(payload[i], 8);
      packer.pack_field_int(id, 32);
      packer.pack_string(tag);
    endfunction

    virtual function void do_unpack(uvm_packer packer);
      super.do_unpack(packer);
      addr = packer.unpack_field_int(32);
      data = packer.unpack_field_int(32);
      kind = kind_e'(packer.unpack_field_int(2));
      be = packer.unpack_field_int(4);
      delay = packer.unpack_field_int(32);
      foreach (payload[i]) payload[i] = packer.unpack_field_int(8);
      id = packer.unpack_field_int(32);
      tag = packer.unpack_string();
    endfunction

    virtual function string convert2string();
      return $sformatf("addr=%0h data=%0h kind=%s be=%0h delay=%0d payload=%p id=%0d tag=%s",
                       addr, data, kind.name(), be, delay, payload, id, tag);
    endfunction
  endclass
endpackage
