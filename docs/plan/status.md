# sv-weave-uvm status
Milestone: U0 | Next action: owner answers (envrc, file core issues, §9 Q1-Q6); U1 UVM-version survey | Blocked on: none (U4 needs core L1/L2) | Last updated: 2026-11-08

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
- [ ] Core issues filed (drafts: `core-issues.md`).
