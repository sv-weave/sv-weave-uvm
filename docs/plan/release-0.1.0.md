# sv-weave-uvm 0.1.0 release checklist

Hand-off §6 U6: "`pip install sv-weave sv-weave-uvm`, an audit, then weaving one class
with UVM 2020 on Verilator. Docs. 0.1.0 on PyPI. A fresh user finishes in under 10
minutes." The owner tags and publishes; nothing here is done by an agent.

## Ready
- [x] Version 0.1.0 (`src/sv_weave_uvm/__version__.py`, `version_info`); depends on
      `sv-weave>=0.1,<0.2` (0.1.0 is on PyPI).
- [x] Quickstart: `examples/quickstart/run.sh` (sv-weave gen + `verilator --binary`),
      docs/quickstart.rst includes its files; `tests/sim/test_quickstart.py` runs it.
- [x] Timing (2026-11-08, this machine, Verilator 5.054): weave <1 s, Verilator build
      ~20 s, run <1 s. Reading the page and copying the files is the rest of the
      10 minutes.
- [x] Unit, docs, sim suites pass locally (sim 7 cases).

## Not ready / not checked
- [-] "an audit": 0.1.0 ships without audits (owner decision, 2026-11-08). The UVM
      audits (U4, item 10) wait for core L1/L2 and move past 0.1.
- [ ] `pip install sv-weave-uvm` from PyPI on a clean machine: not possible before
      publishing. Check after: a fresh venv, `pip install sv-weave-uvm`, Verilator on
      PATH, `./examples/quickstart/run.sh` from a checkout of the tag.
- [ ] CI has not run on a runner (the repo is not pushed). The tag push runs build,
      sim and publish (`.github/workflows/ci.yml`; publish needs sim).
- [ ] The woven `do_print` gets Verilator `WIDTHEXPAND` warnings (print_field_int
      with narrow fields); harmless with `-Wno-fatal`, documented in the quickstart.

## Steps for the owner
1. Merge `dev` to `main`; push.
2. Wait for CI green on `main`.
3. `git tag v0.1.0 && git push --tags` (CI checks the tag against `version_info`).
4. After publish: the clean-machine check above.
