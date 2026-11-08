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
adds the generated `Woven_bm_woven_tx__release` class from `bm_woven_pkg_woven.sv`, also
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

## Runtime (`test_runtime.py`)

`fields/z_tb.sv` loops N times over one object of the selected variant
(`+bm_variant=macros|hand|woven`, `+bm_n=N`): `randomize()`, `copy`, `compare`,
`pack`/`unpack` + `compare`, `sprint()` (table printer) and `convert2string()`. Every
compare is checked, so the variants are known to agree on copy and on pack/unpack (all
pack 298 bits). The image is built once; each variant runs REPEAT times and the median of
Verilator's reported walltime is taken, less the median of a `none` run (start-up only).
The printed text differs per variant (the macros, the hand code and the weavers format
fields differently), so `chars` is not equal.

    BM_N=100000 BM_REPEAT=3 BM_RESULTS=/tmp/bm.md pytest -p pytest_dfm -s bench/test_runtime.py

Verilator 5.054, UVM 2020.3.2, AMD Ryzen 9 9950X, N=100000, median of 3 runs
(start-up 0.001 s subtracted):

| Variant | Loop time (s) | us / iteration | vs hand |
|---|---:|---:|---:|
| uvm_field_* macros | 2.952 | 29.5 | 1.09x |
| hand-written do_* | 2.716 | 27.2 | 1.00x |
| sv-weave | 2.021 | 20.2 | 0.74x |

One machine, one class shape, all six operations in one loop, no per-operation split
and no tuning. In UVM 2020 the field macros run through `do_execute_op`, which is close to
hand-written code here; the gap Erickson measured on OVM/UVM 1.0 macros is not seen.
Why the woven loop beats the hand-written one was not investigated (the hand `do_print`
formats a name per payload element with `$sformatf`; the woven code may avoid such work).
