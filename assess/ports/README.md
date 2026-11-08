# Ports: real transaction classes on sv-weave

Each directory holds a class from a scanned tree, unchanged, next to its sv-weave port, and a
testbench that runs both on Verilator. It shows that a gap `assess/gaps.py` reports is real
and that weaving closes it. Run (repo root, PATH per the main README):

```sh
pytest -m sim tests/sim/test_assess_ports.py
```

## memory_txn (core-v-verif b137fd2, lib/cv_dv_utils/uvm/memory_rsp_model)

`mrm_pkgs.sv`: `mrm_types_pkg` (the two enums it uses), `mrm_orig_pkg::memory_txn`
(as written, not woven) and `mrm_port_pkg::memory_txn_sw` (the port, woven with
`copy`, `compare`, `do_print`). The port is renamed because Verilator 5.054 cannot build
two factory-registered classes of the same name in one image.

| | original | port |
|---|---|---|
| field code in the class | 4 lines (`uvm_object_param_utils_begin`, 2 `uvm_field_int`, `_end`) | 1 line (`uvm_object_param_utils`) |
| fields copied / compared / printed | 2 of 12 (`req_arrival_time`, `global_transmit_time`) | 12 of 12 |
| generated code | 2 field macros expanded in the class | 124-line woven package (one subclass) |

What `tb.sv` checks:

- original: `copy()` leaves `addr`, `data`, `cmd` at their defaults, and `compare()` says
  two transactions that differ in `addr`/`data`/`cmd` are equal -- the 8 G1 findings.
- port: the factory returns the woven class; `copy()` copies all 12 fields; `compare()`
  catches a `data` and an `atop` mismatch; `sprint()` prints every field, enums by name;
  the hand-written `convert2string()` is kept.

The port took one edit (drop the field macros) and no attributes. One Verilator pitfall met on the
way: a `//` comment whose first word is "Verilator" is read as a pragma (BADVLTPRAGMA), and
macros inside it are expanded.
