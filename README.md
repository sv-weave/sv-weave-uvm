# sv-weave-uvm

The UVM library for [sv-weave](https://github.com/sv-weave/sv-weave): the `uvm`
binding, the factory adapter (`sv_weave_uvm_pkg`), UVM-specific weavers and, later,
UVM audits. Core sv-weave stays library-neutral; everything UVM-specific lives here.

## Use

```
pip install sv-weave sv-weave-uvm
```

```yaml
# sv-weave.yaml
sv-weave:
  binding: uvm            # found through the sv_weave.bindings entry point
  packages: {include: [my_tx_pkg]}
  weavers: [{name: copy}, {name: compare}, {name: print}]
```

The binding maps features to `uvm_object` hooks (`copy` -> `do_copy`, `compare` ->
`do_compare`, `print` -> `convert2string`) and registers each woven class with
`sv_weave_uvm_factory`, a `uvm_default_factory` subclass. UVM resolves its own type and
instance overrides first; the woven class of the resolved type is substituted after
that, for the profile chosen with `+weave_profile=<p>`.

## Develop

```
ivpm update                 # sv-weave (source), dv-flow, pytest, Verilator
source packages/packages.envrc   # or direnv with the tracked .envrc
uv pip install --python packages/python/bin/python --no-deps -e .
pytest tests/unit
pytest -m sim               # weave + Verilator runs
```

Status: `docs/plan/status.md`. Background: `sv-weave-uvm-handoff.md`.
