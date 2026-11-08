// Fixtures for assess/scan.py: no UVM includes, macros stay unexpanded.
class macro_item extends uvm_sequence_item;
  rand bit [7:0] addr;
  rand bit [31:0] data[4];
  my_kind_e kind;
  static int count;
  `uvm_object_utils_begin(macro_item)
    `uvm_field_int(addr, UVM_DEFAULT)
    `uvm_field_sarray_int(data, UVM_DEFAULT | UVM_NOCOMPARE)
    `uvm_field_enum(my_kind_e, kind, UVM_ALL_ON)
  `uvm_object_utils_end
  function new(string name = "macro_item");
    super.new(name);
  endfunction
endclass

class hand_item extends macro_item;
  rand int unsigned len;
  bit flag;
  `uvm_object_utils(hand_item)
  function new(string name = "hand_item");
    super.new(name);
  endfunction
  // copies len but forgets flag
  virtual function void do_copy(uvm_object rhs);
    hand_item rhs_;
    super.do_copy(rhs);
    $cast(rhs_, rhs);
    len = rhs_.len;
  endfunction
  extern virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
endclass

function bit hand_item::do_compare(uvm_object rhs, uvm_comparer comparer);
  hand_item rhs_;
  $cast(rhs_, rhs);
  return len == rhs_.len && flag == rhs_.flag;
endfunction

class cfg_obj #(int W = 8) extends uvm_object;
  local int unsigned depth;
  `uvm_object_param_utils(cfg_obj#(W))
  function void do_print(uvm_printer printer);
    printer.print_field_int("depth", depth, 32);
  endfunction
endclass

class my_drv extends uvm_driver #(hand_item);
  `uvm_component_utils(my_drv)
endclass

class pack_item extends uvm_sequence_item;
  int a;
  int b;
  `uvm_object_utils(pack_item)
  function void do_pack(uvm_packer packer);
    packer.pack_field_int(a, 32);
    packer.pack_field_int(b, 32);
  endfunction
  function void do_unpack(uvm_packer packer);
    a = packer.unpack_field_int(32);
  endfunction
endclass

class bare_cfg extends uvm_object;
  int unsigned timeout;
  virtual foo_if vif;
  `uvm_object_utils(bare_cfg)
endclass
