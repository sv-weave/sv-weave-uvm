sv-weave-uvm
============

The UVM library for `sv-weave <https://dvkit.org/sv-weave/sv-weave/>`_. It lets
sv-weave generate ``do_copy``, ``do_compare`` and ``convert2string`` for your UVM
transactions at compile time, instead of field macros or hand-written methods, and
works *with* the UVM factory rather than beside it.

It contains:

- **the UVM binding** (``binding: uvm``): root classes, features mapped to UVM's
  virtual hooks, and factory registration;
- **the factory adapter** ``sv_weave_uvm_pkg``: a ``uvm_default_factory`` subclass
  that substitutes woven classes after UVM has resolved its own overrides;
- later: UVM-specific weavers (``do_print``, ``do_pack``/``do_unpack``) and UVM
  audits.

.. toctree::
   :maxdepth: 2

   quickstart
   user/index
