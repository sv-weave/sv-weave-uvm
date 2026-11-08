# Benchmarks

Not run by `pytest`. Needs `verilator` and `sv-weave` on PATH (after `ivpm update`:
`export PATH=$PWD/packages/python/bin:$PWD/packages/verilator/bin:$PATH`).

## Line counts (`linecount.py`)

One sequence item, three ways (`fields/`):

- `macros_pkg.sv`: `` `uvm_object_utils_begin`` with one `` `uvm_field_*`` per field
- `hand_pkg.sv`: `do_copy`, `do_compare`, `do_print`, `do_pack`, `do_unpack` and
  `convert2string` written by hand
- `woven_pkg.sv` + `sv-weave.yaml`: the plain class; sv-weave writes the same methods
  (weavers `copy`, `compare`, `print`, `do_print`, `pack`)

The class has eight fields: two 32-bit ints, an enum, a 4-bit int, an int unsigned,
a fixed byte array, an int and a string. It stands in for the 22-line class of
Erickson, "Are OVM & UVM Macros Evil? A Cost-Benefit Analysis" (DVCon 2011), whose
macros expanded to 644 lines. That exact class is **not** reproduced here (no copy of
the paper was at hand); the numbers below are for this class and UVM 2020.3.2.

Method: *source* counts the non-blank, non-comment lines from `class` to `endclass`
as written. *Expanded* counts the same after `verilator -E -P -I<uvm/src>` has expanded
every UVM macro (including `` `uvm_object_utils``, which all three use). For sv-weave it
adds the generated `Woven_bm_tx__release` class from `bm_woven_pkg_woven.sv`, also
expanded; the package's `__register()` function (8 lines) is not counted.

    python bench/linecount.py --markdown

Verilator 5.054 bundled UVM 2020.3.2 (`packages/verilator/share/uvm/src`), sv-weave 0.1.0:

| Variant | Source lines | Expanded lines |
|---|---:|---:|
| uvm_field_* macros | 23 | 1447 |
| hand-written do_* | 66 | 92 |
| sv-weave | 14 | 154 (32 user + 122 generated) |

The macro class is the shortest to write after the woven one but expands to about 16x
the hand-written code. The woven class is the shortest to write and expands to 1.7x the
hand-written code, because the generated methods spend a few lines per field (for example, `do_compare`
checks each field in its own `if` and reports which field differs).
