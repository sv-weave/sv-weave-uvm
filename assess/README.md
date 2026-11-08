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
- `gaps.py <root>... | --scan out.json [-o gaps.json] [--text]`: per data
  member of each data class (root `uvm_object` -> kind `object`,
  `uvm_sequence_item`/`uvm_transaction` -> kind `item`), the copy/compare/
  print/pack paths no field macro or hand method covers. Rules G1-G6 are listed
  in the module docstring. Flags use UVM 1.2 semantics (an operation is on
  unless its `UVM_NO*` flag is set). Static/const members and handles that are
  not data (`virtual` interfaces, events, mailboxes, TLM ports) are skipped;
  typedef'd interface handles are not recognised.
- `size.py <root>... | --scan out.json [-o size.json] [--depth N] [--text]`:
  per class with field macros or hand do_* methods, the source lines spent on
  them (`macro_src`, `hand_src`), the sv-weave equivalent (`weave_src`: the
  utils line plus one attribute per field with a UVM_NO*/radix/REFERENCE flag),
  `saved`, the lines the macros expand to (`macro_exp`, per-macro constants
  measured with `verilator -E -P` on UVM 2020.3.2) and an estimate of the woven
  code generated instead (`woven_gen`). Totals per root and per directory
  group under it (`--depth`, default 1), split into data classes and others.
  Hand line counts include blank/comment lines inside the methods; `saved` is
  an upper bound where a hand method does more than field-by-field work.

Parsing is syntax-only (pyslang, no include/macro preprocessing); UVM macros are
found lexically in the class text. Tests: `pytest -q tests/unit/assess`.
