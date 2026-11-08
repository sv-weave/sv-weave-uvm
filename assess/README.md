# assess: field-automation survey of third-party UVM testbenches

Tools to measure how existing UVM environments (OpenTitan, OpenHW core-v-verif)
implement field automation, to find gaps sv-weave-uvm would close and to
estimate the code it would remove. The trees come from the ivpm dep-set
`assess` (`ivpm update -d assess` -> `packages/opentitan`, `packages/core-v-verif`).

- `scan.py <root>... -o out.json`: per class, data members (type, rand/static/
  local/const), `uvm_field_*` registrations (+flags), hand-written
  `do_copy`/`do_compare`/`do_print`/`convert2string`/`do_pack`/`do_unpack`/
  `do_record` methods (in-class or extern bodies), their line counts, the
  members each touches and whether it calls `super`. Each class gets a
  `category` (object, sequence, component, reg, unknown, non_uvm) from its
  `extends` chain, resolved by name within the scanned roots: scan a whole tree
  at once, or base classes outside it show as `unknown`.

Parsing is syntax-only (pyslang, no include/macro preprocessing); UVM macros are
found lexically in the class text. Tests: `pytest -q tests/unit/assess`.
