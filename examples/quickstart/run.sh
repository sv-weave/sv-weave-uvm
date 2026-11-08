#!/bin/sh
# Weave tx_pkg, then build and run the testbench with Verilator's bundled UVM.
# UVM defaults to the UVM that ships with Verilator; set UVM to use another.
set -e
cd "$(dirname "$0")"
UVM=${UVM:-$(dirname "$(command -v verilator)")/../share/uvm/src}

sv-weave gen -c sv-weave.yaml -I "$UVM" -o woven "$UVM/uvm_pkg.sv" tx_pkg.sv

verilator --binary -j 0 -Wno-fatal --top-module tb -Mdir obj_dir \
  +define+UVM_NO_DPI +incdir+"$UVM" "$UVM/uvm_pkg.sv" \
  -f woven/sv_weave_rt.f tx_pkg.sv -f woven/sv_weave.f tb.sv
./obj_dir/Vtb
