# sv-weave-uvm status
Milestone: U2 | Next action: 8b do_pack/do_unpack weaver | Blocked on: none (U4 needs core L1/L2) | Last updated: 2026-11-08

## U0 Bootstrap
- [x] Package scaffold: `sv_weave_uvm.binding.UvmBinding`, `share/sv/sv_weave_uvm_pkg.sv`
      moved as-is from sv-weave `examples/uvm/`; entry point `sv_weave.bindings: uvm`.
- [x] ivpm.yaml: sv-weave (git, main), dv-flow-mgr, dv-flow-libhdlsim, pytest-dfm (git),
      pytest, sphinx, edapack `sim.rtl` (Verilator, iverilog).
- [x] `tests/unit/test_binding.py` (9 tests).
- [x] `tests/sim/test_uvm_basic.py`: `binding: uvm`, no plugin-path; adapter via
      `svweave.Runtime`. Passes on Verilator's bundled UVM.
- [x] CI (.github + .forgejo, copied from core): build+wheel test (`-m "not sim and not docs"`),
      `sim` job (ivpm fetches edapack Verilator + dv-flow; unit + `-m sim`), publish needs sim;
      Forgejo docs.yml. Not yet run on a runner (repo not pushed).
- [x] Docs skeleton: Sphinx (index, quickstart, user/features with the feature->hook table
      generated from `UvmBinding.features()`, user/factory: adapter + override order);
      `tests/docs` (marker `docs`, `-W`).
- [-] Core issues not filed (owner): changes in `core-issues.md` are made locally in the
      core clone `packages/sv-weave` when an item needs them.
- [ ] `.envrc`: removed from `.gitignore` so it is tracked; the file itself is not written
      yet (the agent tool refuses it as a sensitive file). Copy core's, then `direnv allow`.

## U1 UVM version (Verilator's bundled 2020.3.2 only, per Q1)
- [x] Survey: `uvm_default_factory::find_override_by_type/name` are virtual and every
      create path calls them; `uvm_coreservice_t::set_factory` exists.
- [x] `tests/sim/test_override_chain.py`: tx -> tx1 -> tx2 chains (instance, type, create
      by name) give the woven last link. The adapter runs on every link; harmless.
- Pitfall seen: a `uvm_factory f = uvm_factory::get();` initializer in an `initial` block
  runs before `sv_weave_init_m` installs the woven factory, so overrides set through `f`
  go to the old factory. Documented in docs/user/factory.rst.

## U2 Complete features
- [x] 8d `tests/sim/test_component.py`: run_test -> test -> env -> agent -> driver
      (`uvm_driver #(tx)`), each woven, names/parents intact; `p_tx#(16)` woven on
      Verilator. Adapter fix: `find_override_by_name` returns the woven class when UVM
      finds no override (run_test used to create the unwoven test).
- [x] 8a `do_print` weaver (`sv_weave_uvm.weavers`, entry point; no core change):
      one `uvm_printer` call per field. `tests/sim/test_print.py` checks table, tree
      and line printers and that `convert2string` (core `print`) still works.
- [ ] 8b do_pack/do_unpack. 8c do_record out (Q4).

## U3 Override + debug story
- [x] Type names (Q2): woven classes use `uvm_object_param_utils` /
      `uvm_component_param_utils` (registered by type only), inherit the user's
      `get_type_name()`; `factory.print()` shows no `Woven_*` (checked in uvm_basic).
      Tests use `CHECK_WOVEN(obj, T, msg)` from tests/sim/sv/check_pkg.sv.
- [ ] Seed stability release vs debug profile.

## Decisions (hand-off §9, 2026-11-08)
- Q1 UVM versions: focus on the UVM bundled with Verilator (2020.3.2). Other versions,
  including 1.1d, are not targeted for now.
- Q2 Woven classes report the original type name (`get_type_name()`, `factory.print()`,
  logs). Weaving is an implementation artifact, not visible to the user.
- Q3 print (no answer; provisional): `do_print(uvm_printer)` primary, keep `convert2string`.
- Q4 do_record (no answer; provisional): out of 0.1.
- Q5 audits (no answer; provisional): same package.
- Q6 VIP header stubs (no answer; provisional): out of 0.1.
