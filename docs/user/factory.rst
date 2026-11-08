The factory adapter and overrides
=================================

sv-weave does not keep a type registry of its own. Woven classes are created by the
UVM factory, through ``sv_weave_uvm_factory`` in ``sv_weave_uvm_pkg``.

How it works
------------

- ``sv_weave_uvm_factory extends uvm_default_factory``. ``install()`` puts it in the
  core service (``uvm_coreservice_t::get().set_factory``); it is idempotent.
- The generated woven package registers each woven class with
  ``add(User::get_type(), "<profile>", Woven::get_type())``. ``sv_weave_init()``
  (or the ``sv_weave_init_m`` module) runs these registrations.
- ``find_override_by_type`` and ``find_override_by_name`` call the UVM
  implementation first, then substitute the woven class of the type it returned.
  When UVM finds no override by name, it returns null and ``create_*_by_name``
  falls back to the registered type; the adapter returns the woven class instead,
  so ``run_test("my_test")`` creates the woven test.

Override order
--------------

For ``T::type_id::create(name)`` the factory:

1. resolves UVM instance overrides, then type overrides, exactly as plain UVM does;
2. takes the resolved type -- ``T`` itself if nothing overrides it -- and, if a woven
   class is registered for it in the selected profile, creates that instead.

So an override from ``tx`` to ``my_tx`` yields the woven ``my_tx``, and it
does so whether the override was set before or after the woven classes were
registered. This is why the adapter is a factory subclass and not a set of
``set_type_override`` calls, whose result would depend on registration order.

A type that is registered under the same UVM type name by another package, but not
woven, is created unchanged.

Profiles
--------

The profile is chosen at run time with ``+weave_profile=<p>``. Without the plusarg
the config's ``default-profile`` is used. The plusarg is read once, on the first
lookup.

Type names
----------

A woven object reports the user's type name: ``get_type_name()`` and ``type_name()``
of a woven ``my_tx`` return ``"my_tx"``, and ``factory.print()`` and UVM messages show
only the user's names. The woven class is registered with the factory by type only
(`` `uvm_object_param_utils ``), so it has no factory name of its own; overrides by
name keep using the user's names. ``get_object_type()`` does return the woven class's
wrapper, which is how a test can tell that an object was woven.

Get the factory after time 0 starts, not in a variable initializer::

    initial begin
      uvm_factory f = uvm_factory::get();   // too early: the woven factory is not yet installed

An initializer of a static variable runs before ``sv_weave_init_m`` installs the woven
factory, so overrides set through ``f`` go to UVM's default factory and are lost.
Assign ``f = uvm_factory::get();`` as a statement instead.

Components and parameterized classes
------------------------------------

``uvm_component`` classes are woven like objects and registered with
``uvm_component_param_utils``. ``type_id::create(name, this)`` and ``run_test()`` create
the woven class with the given name and parent, so the hierarchy and full names are
the user's (``uvm_test_top.env.agent.drv``). The copy and compare weavers treat a
child-component handle like any other class handle: copied and compared by reference.

A parameterized class registered with ``uvm_object_param_utils(p_tx#(W))`` is woven
per specialization that the code uses (``p_tx#(16)``). UVM 2020 gives such a class no
``type_name()``; ``get_type_name()`` of it and of its woven class is whatever the
base class reports.
