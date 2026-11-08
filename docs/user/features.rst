Features and UVM hooks
======================

Each feature in the ``weavers:`` list maps to a virtual hook of ``uvm_object``. sv-weave
generates an override of that hook in the woven class; UVM's own entry points reach it
as usual (``copy()`` calls ``do_copy``, ``compare()`` calls ``do_compare``).

.. include:: ../_generated/features.rst

Notes
-----

- Only fields declared in your classes are woven. Fields of UVM's own base classes
  (``uvm_sequence_item``, ``uvm_transaction``) are not.
- ``compare`` reports each differing field with ``uvm_report_info`` at ``UVM_HIGH``
  verbosity, under the id ``sv-weave``.
- ``print`` currently produces ``convert2string()``. A ``do_print`` weaver that goes
  through ``uvm_printer`` (so ``print()`` and ``sprint()`` use the table, tree and line
  printers) is planned.
- The binding adds `` `uvm_object_param_utils `` (or `` `uvm_component_param_utils ``
  for a component) to each woven class, so it keeps the user's type name, and registers the woven class with the factory
  adapter (see :doc:`factory`).
- A class that is not registered with the factory (no `` `uvm_object_utils ``) is
  still woven, but its woven class is never created; sv-weave warns.
