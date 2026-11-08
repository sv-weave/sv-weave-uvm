// Typedefs memory_txn needs, copied from core-v-verif b137fd2
// lib/cv_dv_utils/uvm/memory_rsp_model/memory_response_model_pkg.sv (Apache-2.0, CEA).
package mrm_types_pkg;
    typedef enum logic [1:0] {
        MEM_WRITE    = 2'b00,
        MEM_READ     = 2'b01,
        MEM_ATOMIC   = 2'b10,
        RESERVED     = 2'b11
    } mem_command_t;

    typedef enum logic [3:0] {
        MEM_ATOMIC_ADD  = 4'b0000,
        MEM_ATOMIC_CLR  = 4'b0001,
        MEM_ATOMIC_SET  = 4'b0010,
        MEM_ATOMIC_EOR  = 4'b0011,
        MEM_ATOMIC_SMAX = 4'b0100,
        MEM_ATOMIC_SMIN = 4'b0101,
        MEM_ATOMIC_UMAX = 4'b0110,
        MEM_ATOMIC_UMIN = 4'b0111,
        MEM_ATOMIC_SWAP = 4'b1000,
        MEM_ATOMIC_CMP  = 4'b1001,
        MEM_ATOMIC_LDEX = 4'b1100,
        MEM_ATOMIC_STEX = 4'b1101
    } mem_atomic_t;
endpackage

// memory_txn as in core-v-verif b137fd2
// lib/cv_dv_utils/uvm/memory_rsp_model/memory_response_model.svh (Apache-2.0, CEA),
// unchanged but for the package. Not woven: the reference behaviour.
`include "uvm_macros.svh"
package mrm_orig_pkg;
  import uvm_pkg::*;
  import mrm_types_pkg::*;

class memory_txn #(int w_addr = 64, int w_data = 512, int w_id = 16) extends uvm_object;


    bit [w_id -1: 0]      id;
    bit [w_addr -1: 0]    addr;
    bit [w_data -1: 0]    data;
    bit [w_data/8 -1: 0]  strb;
    bit                   err;
    bit                   ex_fail; //exclusive_fail

    mem_command_t         cmd;
    mem_atomic_t          atop;
    //////////////////////////////////////////////////////
    //Configuration Parameters
    //To be driven by the driver
    /////////////////////////////////////////////////////
    int                    req_arrival_time;;
    int                    global_transmit_time; //delay in clock cycle

    int                    req_ts, resp_ts;

     // ------------------------------------------------------------------------
     // Utilities for the variables
     // ------------------------------------------------------------------------
    `uvm_object_param_utils_begin( memory_txn#(w_addr, w_data, w_id) )
        `uvm_field_int( req_arrival_time,                 UVM_DEFAULT )
        `uvm_field_int( global_transmit_time,             UVM_DEFAULT )
    `uvm_object_utils_end


    function new( string name ="" );
        super.new( name );
    endfunction

   // ===========================================================================
   // convert2string()
   // ===========================================================================
   virtual function string convert2string( );
      string s ;
      string prefix;

      prefix = { get_full_name(), " :: MEM TXN " } ;

      s = { s, $sformatf("ID         = %0x(x)",  id      ),  " " };
      s = { s, $sformatf("ADDR       = %0x(x)",  addr    ),  " " };
      s = { s, $sformatf("DATA       = %0x(x)",  data    ),  " " };
      s = { s, $sformatf("ERR        = %0x(x)",  err     ),  " " };
      s = { s, $sformatf("EX ERR     = %0x(x)",  ex_fail  ),  " " };
      return s;
   endfunction
endclass : memory_txn
endpackage

// memory_txn ported to sv-weave: the field macros are gone, only the param utils macro
// is left; copy, compare and do_print are woven for every field. Renamed memory_txn_sw
// as Verilator 5.054 cannot build two factory-registered classes of the same name in one image.
package mrm_port_pkg;
  import uvm_pkg::*;
  import mrm_types_pkg::*;

class memory_txn_sw #(int w_addr = 64, int w_data = 512, int w_id = 16) extends uvm_object;


    bit [w_id -1: 0]      id;
    bit [w_addr -1: 0]    addr;
    bit [w_data -1: 0]    data;
    bit [w_data/8 -1: 0]  strb;
    bit                   err;
    bit                   ex_fail; //exclusive_fail

    mem_command_t         cmd;
    mem_atomic_t          atop;
    //////////////////////////////////////////////////////
    //Configuration Parameters
    //To be driven by the driver
    /////////////////////////////////////////////////////
    int                    req_arrival_time;;
    int                    global_transmit_time; //delay in clock cycle

    int                    req_ts, resp_ts;

    `uvm_object_param_utils( memory_txn_sw#(w_addr, w_data, w_id) )


    function new( string name ="" );
        super.new( name );
    endfunction

   // ===========================================================================
   // convert2string()
   // ===========================================================================
   virtual function string convert2string( );
      string s ;
      string prefix;

      prefix = { get_full_name(), " :: MEM TXN " } ;

      s = { s, $sformatf("ID         = %0x(x)",  id      ),  " " };
      s = { s, $sformatf("ADDR       = %0x(x)",  addr    ),  " " };
      s = { s, $sformatf("DATA       = %0x(x)",  data    ),  " " };
      s = { s, $sformatf("ERR        = %0x(x)",  err     ),  " " };
      s = { s, $sformatf("EX ERR     = %0x(x)",  ex_fail  ),  " " };
      return s;
   endfunction
endclass : memory_txn_sw
endpackage
