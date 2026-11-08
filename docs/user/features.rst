Features and UVM hooks
======================

Each feature in the ``weavers:`` list maps to a virtual hook of ``uvm_object``. sv-weave
generates an override of that hook in the woven class; UVM's own entry points reach it
as usual (``copy()`` calls ``do_copy``, ``compare()`` calls ``do_compare``,
``print()`` and ``sprint()`` call ``do_print``).

.. include:: ../_generated/features.rst

Notes
-----

- Only fields declared in your classes are woven. Fields of UVM's own base classes
  (``uvm_sequence_item``, ``uvm_transaction``) are not.
- ``compare`` reports each differing field with ``uvm_report_info`` at ``UVM_HIGH``
  verbosity, under the id ``sv-weave``.
- ``do_print`` is the weaver to use for printing. It is part of this package, not of
  sv-weave's core, and calls one ``uvm_printer`` method per field, so ``print()`` and
  ``sprint()`` work with the table, tree and line printers:

  - integral fields with ``print_field_int`` (``print_field`` above 64 bits; signed
    fields in decimal), enums with their name and type, strings, reals;
  - a ``(* weave_deep *)`` handle to a ``uvm_object`` is printed nested
    (``print_object``); other handles as a reference (``@<inst id>`` or ``<null>``);
  - arrays, queues and unpacked structs with ``%p``;
  - ``(* weave_noprint *)`` leaves a field out, as for ``print``.

- ``print`` produces ``convert2string()`` (one ``name: value`` line per field), for
  ``$display`` and log messages. List both weavers to get both::

    weavers:
    - {name: print}
    - {name: do_print}

- The binding adds `` `uvm_object_param_utils `` (or `` `uvm_component_param_utils ``
  for a component) to each woven class, so it keeps the user's type name, and registers the woven class with the factory
  adapter (see :doc:`factory`).
- A class that is not registered with the factory (no `` `uvm_object_utils ``) is
  still woven, but its woven class is never created; sv-weave warns.
