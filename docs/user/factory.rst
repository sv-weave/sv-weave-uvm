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

Override order
--------------

For ``T::type_id::create(name)`` the factory:

1. resolves UVM instance overrides, then type overrides, exactly as plain UVM does;
2. takes the resolved type -- ``T`` itself if nothing overrides it -- and, if a woven
   class is registered for it in the selected profile, creates that instead.

So an override from ``tx`` to ``my_tx`` yields ``Woven_my_tx__<profile>``, and it
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

``get_type_name()`` of a woven object currently returns the woven class name
(``Woven_my_tx__release``). How this should appear in ``factory.print()`` and logs is
an open item.
