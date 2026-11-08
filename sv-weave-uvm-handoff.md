# Hand-off: bootstrapping sv-weave-uvm

Status: 2026-11-08. Written in the sv-weave repo (`docs/handoff/`). Copy this file
into the new repo as its first commit, then keep a short status note there (see
"Status note" at the end).

## 1. What sv-weave-uvm is

The UVM library for sv-weave. It contains:
- **the UVM binding**: root classes, features mapped to UVM hooks, and factory
  registration;
- **the factory adapter**: `sv_weave_uvm_pkg`, a `uvm_default_factory` subclass;
- **the UVM weavers** where the generic core weavers aren't enough: `do_print` through
  `uvm_printer`, `do_pack`/`do_unpack`, `do_record`;
- **the UVM audits**: config_db, field macros, registration.

It is the product that the launch ("SystemVerilog Finally Gets Compile-Time
Reflection") is demonstrated with. Core sv-weave stays library-neutral.

**Decisions (from sv-weave):**
- **D10:** a separate repo from the start; core is never released together with it.
- **D7:** fw-hdl support ships in fw-hdl, not here.
- **No parallel type registry:** sv-weave works *with* `uvm_factory` (design §6.7,
  revised after P7).
- **Factory subclass, not `set_type_override`:** UVM's own overrides resolve
  first, and the woven class is substituted after that. This avoids depending on
  registration order (design §8.3, handoff).
- **D2:** registration is explicit by default (`sv_weave_init()` and the
  `sv_weave_init_m` module); `registration: static` is opt-in.

## 2. Read first (in sv-weave)

| Doc | Why |
|---|---|
| `docs/pitch/launch-plan.md` | Steps L3, L4, L7 and L8 are this repo's work |
| `docs/design/audit-design.md` | The `Auditor` plugin kind and the UVM audit ids |
| `docs/pitch/market-survey.md` | Who it's for, the pain points to target, the must-haves |
| `docs/design/initial-design.md` §6–§8, §10, §12 | Weaving model, rand-safety, factory adapter, plugin contract, decisions. **§8.3 is stale** (see §9 below). |
| `docs/authoring/bindings.rst`, `docs/authoring/weavers.rst` | The plugin API as documented |
| `docs/design/notes/registration-trigger.md` | Evidence behind D2 |
| `docs/plan/implementation-plan.md` (P9 to-do, :709-715; xezim bug, :116-117) | Known UVM to-dos and blockers |

## 3. Starting point: `examples/uvm/` in sv-weave

**`uvm_binding.py` (93 lines): `UvmBinding(Binding)`**
- `name="uvm"`, `version="0.1"`, `roots=("uvm_pkg::uvm_object",)`.
- **Features:**
  - `copy` → `do_copy(uvm_object rhs)`;
  - `compare` → `bit do_compare(uvm_object rhs, uvm_comparer comparer)`;
  - `print` → `string convert2string()`.
- **`create_expr`** returns `T::type_id::create(inst)` when the class has a static
  `get_type()` (it uses `` `uvm_object_utils ``); otherwise it returns `None`, which
  means `new()`.
- **`miscompare_stmt`** emits `uvm_report_info(..., UVM_HIGH)`.
- **`preamble`** includes `uvm_macros.svh`, and **`imports`** adds `uvm_pkg`.
- **`finalize`** warns about unregistered classes, then adds
  `` `uvm_object_utils ``/`` `uvm_component_utils `` to the woven class.
- **`package_items`** emits `sv_weave_uvm_factory::install()`,
  `set_config_default(...)` and, for each concrete registered class and profile,
  `add(User::get_type(), "<profile>", Woven::get_type())`.

**`sv_weave_uvm_pkg.sv` (82 lines): `sv_weave_uvm_factory extends uvm_default_factory`**
- The map is `m_woven[uvm_object_wrapper][string]`, keyed by wrapper.
- **`install()`** sets the factory through `uvm_coreservice_t::get().set_factory(wf)`.
  It is idempotent.
- **Profile selection:** `+weave_profile=<p>` is read lazily, once. If it isn't set,
  the config default is used.
- **`find_override_by_type` and `find_override_by_name`** return
  `woven_of(super.…)`, so UVM resolves overrides first and the woven class is
  substituted second.
- It must compile after `uvm_pkg` and before the woven packages.

**Tests:** `tests/sim/test_uvm_example.py::test_uvm_basic` (marker `sim`), with the
case directory `tests/sim/uvm_basic/` (`a_tx_pkg.sv`, `tb.sv`, `sv-weave.yaml`).
- The flow is `hdlsim.vlt.SimLibUVM` → the adapter fileset → the case sources →
  `svweave.Weave`.
- `tb.sv` checks an instance override and a type override that are set after
  registration, and expects `Woven_my_tx__release`.

## 4. Contract with core sv-weave

**Discovery.** Declare an entry point, so users can write `binding: uvm` instead of
`module:Class` and `plugin-path`:
- `[project.entry-points."sv_weave.bindings"] uvm = "sv_weave_uvm.binding:UvmBinding"`;
- UVM-specific weavers go in the `sv_weave.weavers` group.

**API gate.** Core has `API_VERSION = (0, 1)`. A plugin's `api` defaults to
`">=0.1,<0.2"`, and `check_api` refuses a mismatch at load time. Pin
`sv-weave>=0.1,<0.2`, and raise both together.

**Binding API** (`src/sv_weave/plugin.py:65-114`):
- attributes `name`, `api`, `version`, `roots`;
- `features()` → `FeatureSpec(name, method, args, arg_names, ret, task, rhs,
  super_policy)`;
- `create_expr`, `miscompare_stmt`, `preamble`, `imports`, `sv_runtime_files`;
- `prepare` and `finalize`;
- `package_items`, which returns the registration statements for `__register()`;
- `init_files`.

**Weaver API:**
- `w.fields()`, `w.feature(name)`, `w.override(method)`, `w.add_method`,
  `w.add_field`, `w.add_item`, `w.add_registration`;
- the `w.sv` helpers: `cast_rhs`, `copy_field`, `compare_field`, `print_field`,
  `accessible`, `type_of`;
- slots: `body.add` and `prepend`, `set_result`, `replace_super`.

**Core weavers** `copy`, `compare`, `print` and `xcheck` don't depend on the binding.
They reach it only through `w.feature(...)`, `miscompare_stmt` and `create_expr`.
Reuse them, and add UVM weavers only where UVM's hooks need more (printer, packer,
recorder).

**dv-flow.** `svweave.Runtime` already emits the binding's `sv_runtime_files`, so the
adapter `.sv` reaches the flow through the binding with no extra fileset task. Ship
the `.sv` as package data.

## 5. Proposed layout

```
pyproject.toml            # name: sv-weave-uvm; deps: sv-weave>=0.1,<0.2
ivpm.yaml                 # use: sv-weave; dev: pytest, pytest-dfm, sim-rtl-tools (edapack)
src/sv_weave_uvm/
  __init__.py  __version__.py
  binding.py              # UvmBinding (from examples/uvm/uvm_binding.py)
  weavers/                # print (uvm_printer), pack/unpack, record
  audits/                 # UVM-CFG-*, UVM-MAC-*, UVM-REG-001 (after core L1/L2)
  share/sv/sv_weave_uvm_pkg.sv
tests/unit/               # binding and weaver unit tests (UVM stub, as core's UVM_STUB)
tests/sim/                # uvm_basic (ported) + one case per feature, per UVM version
tests/audit/              # seeded-bug fixtures, one per audit id
examples/quickstart/      # the 5-minute L8 quickstart
docs/                     # Sphinx; user guide for UVM users, feature → hook table
.github/workflows/ .forgejo/workflows/   # copy core's, adapted (see §8)
```

## 6. Milestones

| # | Content | Exit | Launch step |
|---|---|---|---|
| **U0 Bootstrap** | Create the repo and copy the packaging and CI from core. Move `uvm_binding.py` and `sv_weave_uvm_pkg.sv` across as they are. Add the entry point. Port `uvm_basic`. | `pytest -m sim` passes, using `binding: uvm` with no `plugin-path` | L3 |
| **U1 UVM-version matrix** | Check the factory hooks against `uvm_factory.svh` in each supported UVM version (risk 4, see below). Adapt the adapter, or document what isn't supported. | Sim tests pass on each supported version | L3 |
| **U2 Complete features** | `print` through `do_print(uvm_printer)` as well as `convert2string`; `do_pack`/`do_unpack`; optional `do_record`. Components, not only objects. Parameterized classes. | One sim case per feature; a 3-level hierarchy; `uvm_component` classes | L3 |
| **U3 Override and debug story** | Document how overrides and weaving interact. Make `factory.print()` and `get_type_name()` show something sensible for woven classes. Run the seed-stability check for debug profiles on UVM. | Docs plus sim tests; the same seed gives the same randomization in release and debug | L3 |
| **U4 Audits** | `UVM-CFG-001…004`, `UVM-MAC-001/002`, `UVM-REG-001` (`audit-design.md`). Needs core L1/L2. | A seeded-bug fixture for each id; nothing reported on clean fixtures | L4 |
| **U5 Benchmark** | Reproduce Erickson's 22- vs 644-line comparison. Measure run time for `uvm_field_*`, hand-written and woven code on Verilator (and on xezim once it's unblocked). | Published method, scripts and numbers | L7 |
| **U6 Quickstart and release** | `pip install sv-weave sv-weave-uvm`, an audit, then weaving one class with UVM 2020 on Verilator. Docs. 0.1.0 on PyPI. | A fresh user finishes in under 10 minutes | L8 |

### Risk 4: which UVM versions

The adapter relies on three things that may not exist in every UVM version:
- `uvm_default_factory`;
- `uvm_coreservice_t::get().set_factory()`;
- `find_override_by_type` and `find_override_by_name` being virtual.

They are confirmed for IEEE 1800.2-2020 (plan notes). Market data: about 50% of
teams are on UVM 1.2, about 40% on 1.1d, and under 5% on 1800.2 (DVCon 2021 poll;
`market-survey.md`). **1.1d may not have `uvm_coreservice_t` or a separate
`uvm_default_factory`.** This is not verified. U1 decides whether 1.1d needs a
second adapter, or whether it stays out of scope with a documented reason. Decide
deliberately, because 1.1d is a large share of the market.

## 7. Changes needed in core sv-weave

File these as issues in sv-weave. Don't work around them here.

| Change | Why | Blocks |
|---|---|---|
| `Auditor` plugin kind, `AuditCtx`, model additions, `sv-weave audit` (L1) | UVM audits | U4 |
| Binding additions `audit_fields`, `factory_only`, `hook_field_access` (L2) | Generic audits that this binding configures | U4 |
| Move the hard-coded `"uvm_pkg"` out of `ALWAYS_EXCLUDED` (`src/sv_weave/select.py:22`) into a binding hook such as `library_packages()` | Library knowledge leaking into core | U0 (works as is; fix soon) |
| `Binding.features()` default returns `[]` but is typed `Dict` (`plugin.py:75-76`) | Small bug | — |
| Update `initial-design.md` §8.3 (still says `weave_uvm_factory`, `uvm_factory::set()`, `create_object_by_*`, `weave_registry`) and §10 (`create_signature` should be `create_expr`); plan :89-93 (stale `replace=0` note) | The docs no longer match the code | — |
| Once U0 passes, remove `examples/uvm/` and `test_uvm_example.py` from core, or keep a minimal copy that points here | Avoid two copies | after U0 |

## 8. Testing and infrastructure

- **Simulators:**
  - Verilator 5.054, with UVM sources from `hdlsim.vlt.SimLibUVM`. It uses
    `$UVM_HOME`, otherwise the UVM that ships with Verilator, and `UVM_NO_DPI` when
    there is no DPI layer.
  - xezim: `hdlsim.xzm.SimLibUVM` exists, but xezim 0.11.3 has a bug with
    specializations of parameterized classes (repro in core,
    `docs/design/notes/repro/xezim_param_spec.sv`). Keep xezim cases as strict
    xfails until it's fixed.
- **Multiple UVM versions (U1):** point `$UVM_HOME` at each version's sources in a
  parametrized test.
- **CI must run the sims.** Core's CI only installs pytest, so its sim tests are
  skipped. For this repo, sims are the point, so install Verilator in CI (e.g. via
  the edapack `sim-rtl-tools` dep-set) and run `-m sim`.
- **Release, sync and docs:** follow core's setup:
  - a GitHub/Forgejo `ci.yml` with the release-authority gate, PyPI on `v*` tags;
  - a Forgejo `docs.yml` for dvkit.org.

  Use the `dvkit-infra` skill for onboarding the repo, sync policy and publishing.
- **Names:** claim `sv-weave-uvm` on PyPI early. The hosting org is still handoff Q2.

## 9. Open questions

1. Which UVM versions are supported: is 1.1d in or out (U1)?
2. Should woven classes report the original type name in `get_type_name()` and in
   logs, or `Woven_*`? This affects overrides by string name.
3. Is `convert2string` or `do_print` the primary target of `print`, or both?
4. Is `do_record` in scope for 0.1, given the recording concerns in the random-
   stability analysis (`docs/design/value-pitch.md`)?
5. Do audits ship in the same package or in an extra (`sv-weave-uvm[audit]`)?
   Suggestion: the same package.
6. Encrypted UVM VIP base classes: should the binding supply header stubs
   (`audit-design.md` open points)?

## 10. First-session checklist

1. Create the repo (org per Q2) and copy this file in.
2. Copy `pyproject.toml`, `ivpm.yaml`, `.github/` and `.forgejo/` from core, rename
   them, and set the dependency to `sv-weave>=0.1,<0.2`.
3. Move `examples/uvm/*` into `src/sv_weave_uvm/` and add the `sv_weave.bindings`
   entry point.
4. Port `tests/sim/uvm_basic/` and `test_uvm_example.py`, switching the config to
   `binding: uvm`.
5. `ivpm update`, an editable install, `pytest -m sim > sim.log 2>&1`, and check that
   it passes.
6. Start `docs/plan/status.md` (below) and file the core issues from §7.

## Status note (to keep in the new repo)

```
# sv-weave-uvm status
Milestone: U0 | Next action: ... | Blocked on: ... | Last updated: YYYY-MM-DD
```
