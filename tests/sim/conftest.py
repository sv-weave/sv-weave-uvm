"""Helpers for sim tests: build a dv-flow graph and run it on Verilator.

Every sim case is a directory of SV files with a ``tb`` module that follows the
check_pkg convention (prints ``SV_WEAVE_TEST: PASS``, ``$fatal`` on failure). The UVM
library comes from ``hdlsim.<sim>.SimLibUVM``; the adapter package reaches the build
through ``svweave.Runtime`` (the binding's ``sv_runtime_files``).
"""
import dataclasses as dc
import os
import shutil
from typing import Optional, Sequence

import pytest

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
CHECK_SV_DIR = os.path.join(SIM_DIR, "sv")

PASS_TOKEN = "SV_WEAVE_TEST: PASS"
FAIL_TOKEN = "SV_WEAVE_TEST: FAIL"


def _has_dfm() -> bool:
    try:
        import pytest_dfm  # noqa: F401
        import dv_flow.libhdlsim  # noqa: F401
        return True
    except ImportError:
        return False


def pytest_collection_modifyitems(config, items):
    no_vlt = shutil.which("verilator") is None
    no_xzm = shutil.which("xezim") is None
    no_dfm = not _has_dfm()
    for item in items:
        if "sim" not in item.keywords and "xezim" not in item.keywords:
            continue
        if no_dfm:
            item.add_marker(pytest.mark.skip(reason="pytest-dfm / dv-flow-libhdlsim not installed"))
        elif "xezim" in item.keywords:
            if no_xzm:
                item.add_marker(pytest.mark.skip(reason="xezim is not on PATH"))
        elif no_vlt:
            item.add_marker(pytest.mark.skip(reason="verilator is not on PATH"))


@dc.dataclass
class SimResult:
    status: int
    rundir: Optional[str]
    log: Optional[str]
    text: str = ""

    def assert_pass(self):
        where = "log: %s" % self.log if self.log else "no sim.log (build failed?)"
        assert self.status == 0, "flow failed (status %d); %s" % (self.status, where)
        bad = [l for l in self.text.splitlines() if FAIL_TOKEN in l or "%Error" in l]
        assert not bad, "%s\n%s" % (where, "\n".join(bad[:20]))
        assert PASS_TOKEN in self.text, "%s not seen; %s" % (PASS_TOKEN, where)


def _find_run_dir(out) -> Optional[str]:
    outs = out if isinstance(out, list) else [out]
    for o in outs:
        if o is None:
            continue
        for fs in o.output:
            if getattr(fs, "filetype", None) == "simRunDir":
                return fs.basedir
    return None


def run_sim(dvflow, srcs: Sequence, top="tb", plusargs: Sequence[str] = (),
            sim: str = "vlt") -> SimResult:
    """Build srcs into a simulation image with the given top(s) and run it.
    ``sim`` is an hdlsim backend: ``vlt`` (Verilator, the default) or ``xzm`` (xezim)."""
    tops = [top] if isinstance(top, str) else list(top)
    img = dvflow.mkTask("hdlsim.%s.SimImage" % sim, name="img", top=tops, needs=list(srcs))
    run = dvflow.mkTask("hdlsim.%s.SimRun" % sim, name="run", needs=[img],
                        plusargs=list(plusargs))
    status, out = dvflow.runTask(run)
    rundir = _find_run_dir(out)
    if rundir is None:
        # A failed run emits no simRunDir output; the task's directory is still there.
        rundir = os.path.join(str(dvflow.tmpdir), "run")
    log, text = None, ""
    if os.path.isfile(os.path.join(rundir, "sim.log")):
        log = os.path.join(rundir, "sim.log")
        with open(log) as fp:
            text = fp.read()
    return SimResult(status, rundir, log, text)


def uvm_weave_task(dvflow, case_dir: str, config: str = "sv-weave.yaml",
                   name: str = "woven", sim: str = "vlt", **params):
    """UVM library -> adapter (svweave.Runtime, binding uvm) -> check_pkg -> the case's
    sources -> svweave.Weave, in compile order."""
    uvm = dvflow.mkTask("hdlsim.%s.SimLibUVM" % sim, name="uvm")
    rt = dvflow.mkTask("svweave.Runtime", name="rt", binding=["uvm"], needs=[uvm])
    chk = dvflow.mkTask("std.FileSet", name="check_sv", type="systemVerilogSource",
                        base=CHECK_SV_DIR, include="check_pkg.sv")
    src = dvflow.mkTask("std.FileSet", name="src", type="systemVerilogSource",
                        base=case_dir, include="*.sv")
    cfg = os.path.join(case_dir, config)
    if os.path.isfile(cfg):
        params["config"] = cfg
    return dvflow.mkTask("svweave.Weave", name=name, needs=[rt, chk, src], **params)


def uvm_weave_sim(dvflow, case_dir: str, top="tb", plusargs: Sequence[str] = (),
                  config: str = "sv-weave.yaml", sim: str = "vlt", **params) -> SimResult:
    """Weave the case's sources against UVM, then build and run them."""
    woven = uvm_weave_task(dvflow, case_dir, config, sim=sim, **params)
    return run_sim(dvflow, [woven], top=top, plusargs=plusargs, sim=sim)


def uvm_weave_sim_runs(dvflow, case_dir: str, runs, top="tb", config: str = "sv-weave.yaml",
                       sim: str = "vlt", **params):
    """Weave and build once, then run the image once per entry of ``runs``
    ({name: plusargs}). Returns {name: SimResult}."""
    woven = uvm_weave_task(dvflow, case_dir, config, sim=sim, **params)
    tops = [top] if isinstance(top, str) else list(top)
    img = dvflow.mkTask("hdlsim.%s.SimImage" % sim, name="img", top=tops, needs=[woven])
    tasks = [dvflow.mkTask("hdlsim.%s.SimRun" % sim, name="run_" + n, needs=[img],
                           plusargs=list(p)) for n, p in runs.items()]
    status, _ = dvflow.runTask(tasks)
    out = {}
    for n in runs:
        rundir = os.path.join(str(dvflow.tmpdir), "run_" + n)
        log, text = os.path.join(rundir, "sim.log"), ""
        if os.path.isfile(log):
            with open(log) as fp:
                text = fp.read()
        else:
            log = None
        out[n] = SimResult(0 if log and status == 0 else status, rundir, log, text)
    return out
