Benchmark: field macros, hand code and sv-weave
===============================================

How much code does a sequence item cost, and how fast does it run, when its
``copy``/``compare``/``print``/``pack`` support comes from ``uvm_field_*`` macros, from
hand-written ``do_*`` methods, or from sv-weave? The scripts are in ``bench/`` of the
repository; ``bench/README.md`` has the same numbers.

The class
---------

One sequence item with eight fields (two 32-bit ints, an enum, a 4-bit int, an
``int unsigned``, a fixed ``byte`` array, an ``int`` and a ``string``), written three
ways in ``bench/fields/``:

- ``macros_pkg.sv``: ```uvm_object_utils_begin`` and one ```uvm_field_*`` per field;
- ``hand_pkg.sv``: ``do_copy``, ``do_compare``, ``do_print``, ``do_pack``,
  ``do_unpack`` and ``convert2string`` by hand;
- ``woven_pkg.sv``: the plain class; ``sv-weave.yaml`` selects the ``copy``,
  ``compare``, ``print``, ``do_print`` and ``pack`` weavers.

It stands in for the 22-line class of Erickson, "Are OVM & UVM Macros Evil? A
Cost-Benefit Analysis" (DVCon 2011), whose macros expanded to 644 lines. That class
is not reproduced; these numbers are for the class above.

Line counts
-----------

``python bench/linecount.py --markdown`` counts the non-blank, non-comment lines from
``class`` to ``endclass``: as written (*source*), and after ``verilator -E -P``
has expanded every UVM macro (*expanded*). For sv-weave the expanded count adds the
generated ``Woven_*`` class. Verilator 5.054, UVM 2020.3.2:

========================  ============  ==============================
Variant                   Source lines  Expanded lines
========================  ============  ==============================
``uvm_field_*`` macros    23            1447
hand-written ``do_*``     66            92
sv-weave                  14            154 (32 user + 122 generated)
========================  ============  ==============================

Runtime
-------

``bench/fields/z_tb.sv`` loops N times over one object: ``randomize()``, ``copy``,
``compare``, ``pack``/``unpack`` and ``compare``, ``sprint()`` and
``convert2string()``. Each compare is checked, so the three variants agree on copy and
pack/unpack. ``bench/test_runtime.py`` builds one image, runs each variant three
times and takes the median of Verilator's walltime, less a run with no loop
(start-up)::

    BM_N=100000 BM_REPEAT=3 pytest -p pytest_dfm -s bench/test_runtime.py

Verilator 5.054, UVM 2020.3.2, AMD Ryzen 9 9950X, N=100000:

========================  =============  ==============  =======
Variant                   Loop time (s)  us / iteration  vs hand
========================  =============  ==============  =======
``uvm_field_*`` macros    2.952          29.5            1.09x
hand-written ``do_*``     2.716          27.2            1.00x
sv-weave                  2.021          20.2            0.74x
========================  =============  ==============  =======

Limits: one simulator, one machine, one class shape, the six operations in one loop
(no per-operation split), no tuning. The printed text differs per variant, since each
formats fields its own way.
