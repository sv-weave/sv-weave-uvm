Quickstart
==========

This page weaves ``copy``, ``compare`` and ``print`` into one UVM transaction and runs
it on Verilator with the UVM that ships with Verilator (1800.2-2020.3.2). The files
are ``examples/quickstart/`` in the repository; the test suite runs that directory
(``tests/sim/test_quickstart.py``), so what is shown here is what is tested.

It takes about a minute once Verilator is installed: the weave takes under a second,
the Verilator build of UVM about 20 seconds.

Install
-------

.. code-block:: bash

   pip install sv-weave-uvm

This installs sv-weave as well. sv-weave finds the binding through the
``sv_weave.bindings`` entry point: no ``plugin-path`` is needed. You also need
Verilator on ``PATH`` (tested with 5.054).

A transaction
-------------

Write the class with ``uvm_object_utils`` and no field macros
(``examples/quickstart/tx_pkg.sv``):

.. literalinclude:: ../examples/quickstart/tx_pkg.sv
   :language: systemverilog

Configure
---------

``examples/quickstart/sv-weave.yaml`` names the package to weave and the weavers:
``copy``, ``compare`` and ``print`` (``convert2string``) come from sv-weave,
``do_print`` from this package.

.. literalinclude:: ../examples/quickstart/sv-weave.yaml
   :language: yaml

A testbench
-----------

Instantiate ``sv_weave_init_m`` in the top module (or call ``sv_weave_init()`` before
the first ``create``). After that, ``tx::type_id::create()`` returns the woven class,
and UVM's ``copy()``, ``compare()``, ``print()`` and ``convert2string()`` reach the
woven methods (``examples/quickstart/tb.sv``):

.. literalinclude:: ../examples/quickstart/tb.sv
   :language: systemverilog

The testbench must not name the woven classes or the woven package: sv-weave reads
it before they exist. Use the user's class names; the factory does the rest.

Weave, build and run
--------------------

``examples/quickstart/run.sh``:

.. literalinclude:: ../examples/quickstart/run.sh
   :language: bash

``sv-weave gen`` reads ``uvm_pkg.sv`` and your sources and writes ``woven/``:

- ``sv_weave_rt.f``: the factory adapter, ``sv_weave_uvm_pkg.sv``;
- ``sv_weave.f``: the woven package ``tx_pkg_woven.sv`` and ``sv_weave_init.sv``;
- ``weave-report.md``: what was woven, and why other classes were not.

The compile order is: ``uvm_pkg``, ``sv_weave_rt.f``, your sources, ``sv_weave.f``,
the testbench. ``UVM_NO_DPI`` builds UVM without its C code, which Verilator would
otherwise need to compile and link.

Run it:

.. code-block:: bash

   ./examples/quickstart/run.sh

The end of the output:

.. code-block:: text

   -------------------------------------------
   Name       Type      Size  Value
   -------------------------------------------
   a          tx        -     @149
     addr     integral  8     'h44
     data     integral  32    'h9bd6c7ac
     payload  byte      3     '{'h1, 'h2, 'h3}
   -------------------------------------------
   addr: 'h44
   data: 'h9bd6c7ac
   payload: '{'h1, 'h2, 'h3}

   QUICKSTART: PASS

The ``[MISCMP]`` message before the table is from the second ``compare()``, which is
meant to fail. Verilator warns ``WIDTHEXPAND`` on the woven ``do_print``;
``-Wno-fatal`` lets the build go on.

With dv-flow
------------

The dv-flow tasks do the same: ``svweave.Weave`` weaves, and ``svweave.Runtime``
provides the adapter as a fileset. The sim tests in ``tests/sim/`` use them; see
``tests/sim/conftest.py``.
