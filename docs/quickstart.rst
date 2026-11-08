Quickstart
==========

Install
-------

.. code-block:: bash

   pip install sv-weave-uvm

This installs sv-weave as well. sv-weave finds the binding through the
``sv_weave.bindings`` entry point: no ``plugin-path`` is needed.

A transaction
-------------

Write the class with ``uvm_object_utils`` and no field macros:

.. code-block:: systemverilog

   `include "uvm_macros.svh"
   package tx_pkg;
     import uvm_pkg::*;
     class tx extends uvm_sequence_item;
       `uvm_object_utils(tx)
       rand bit [7:0]  addr;
       rand bit [31:0] data;
       byte            payload[$];
       function new(string name = "tx");
         super.new(name);
       endfunction
     endclass
   endpackage

Configure
---------

``sv-weave.yaml``:

.. code-block:: yaml

   sv-weave:
     binding: uvm
     packages: {include: [tx_pkg]}
     weavers:
     - {name: copy}
     - {name: compare}
     - {name: print}

Compile order
-------------

1. ``uvm_pkg``
2. the factory adapter, ``sv_weave_uvm_pkg.sv`` (``UvmBinding().sv_runtime_files()``;
   the dv-flow task ``svweave.Runtime`` provides it as a fileset)
3. your sources
4. the woven package sv-weave generated (dv-flow: ``svweave.Weave``)

Instantiate ``sv_weave_init_m`` in the testbench top (or call ``sv_weave_init()``
before the first ``create``). After that, ``tx::type_id::create("t")`` returns the
woven class, and ``t.copy()``, ``t.compare()`` and ``t.convert2string()`` work with
no further code.

The complete example, run with Verilator's bundled UVM, is
``tests/sim/uvm_basic/`` in the repository.
