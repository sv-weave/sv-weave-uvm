# Changes needed in core sv-weave (drafts, hand-off §7)

Drafted for filing in github.com/sv-weave/sv-weave. Not worked around here.
State: **not filed yet**.

## 1. Auditor plugin kind (launch L1)
`Auditor` plugin kind, `AuditCtx`, the model additions and a `sv-weave audit`
command, as in `docs/design/audit-design.md`. sv-weave-uvm's audits (UVM-CFG-001..004,
UVM-MAC-001/002, UVM-REG-001) are written against it. Blocks sv-weave-uvm U4.

## 2. Binding hooks for generic audits (launch L2)
Add `audit_fields`, `factory_only` and `hook_field_access` to `Binding`, so generic
audits can be configured by a binding. Blocks sv-weave-uvm U4.

## 3. Move `uvm_pkg` out of `ALWAYS_EXCLUDED`
`src/sv_weave/select.py:22` hard-codes `"uvm_pkg"`. Library knowledge belongs in the
binding: add a hook such as `Binding.library_packages()` (default `()`) whose packages
are never woven; sv-weave-uvm returns `("uvm_pkg",)`. Works today; fix soon.

## 4. `Binding.features()` return type -- already fixed
The hand-off says the default returns `[]` while typed `Dict`; core `main` (checked
2026-11-08) already returns `{}`. Nothing to file.

## 5. Stale design docs
- `initial-design.md` §8.3 still names `weave_uvm_factory`, `uvm_factory::set()`,
  `create_object_by_*` and `weave_registry`; the code uses `sv_weave_uvm_factory`
  (a `uvm_default_factory` subclass installed with
  `uvm_coreservice_t::get().set_factory()`, overriding `find_override_by_type/name`).
- §10: `create_signature` is now `create_expr`.
- `implementation-plan.md` :89-93: stale `replace=0` note.

## 6. Remove `examples/uvm/` from core
sv-weave-uvm U0 passes (`tests/sim/test_uvm_basic.py`). Remove `examples/uvm/` and
`tests/sim/test_uvm_example.py` from core, or keep a minimal copy that points to
sv-weave-uvm.
