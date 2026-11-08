"""Runtime benchmark: the bench/fields sequence item as uvm_field_* macros, hand-written
do_* methods and woven by sv-weave, on Verilator.

Builds one image (all three packages + fields/z_tb.sv), then runs it per variant
REPEAT times with +bm_n=N and takes the median of Verilator's reported walltime. The
`none` run (no loop) is UVM start-up, subtracted from the others. Not part of `tests/`:

    BM_N=20000 BM_REPEAT=3 BM_RESULTS=/tmp/bm.md pytest -p pytest_dfm -s bench/test_runtime.py
"""
import os
import re
import statistics
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from tests.sim.conftest import uvm_weave_sim_runs  # noqa: E402

VARIANTS = ["none", "macros", "hand", "woven"]
WALLTIME = re.compile(r"walltime\s+([0-9.]+)\s*s;")


def test_runtime(dvflow):
    n = int(os.environ.get("BM_N", "20000"))
    repeat = int(os.environ.get("BM_REPEAT", "3"))
    runs = {"%s_%d" % (v, i): ["bm_variant=" + v, "bm_n=%d" % n]
            for v in VARIANTS for i in range(repeat)}
    rs = uvm_weave_sim_runs(dvflow, os.path.join(HERE, "fields"), runs=runs)
    times, lines = {}, {}
    for name, r in rs.items():
        r.assert_pass()
        m = WALLTIME.search(r.text)
        assert m, "no walltime in %s" % r.log
        v = name.rsplit("_", 1)[0]
        times.setdefault(v, []).append(float(m.group(1)))
        bm = re.search(r"^BM .*$", r.text, re.M)
        lines[v] = bm.group(0) if bm else ""
    # The variants must do the same work: same packed size and printed length.
    out = {v: re.sub(r"^BM \S+ ", "", lines[v]) for v in ("macros", "hand", "woven")}
    base = statistics.median(times["none"])
    rows = ["N=%d iterations, median of %d runs, Verilator walltime; start-up (none) "
            "= %.3f s subtracted" % (n, repeat, base), "",
            "| Variant | Loop time (s) | us / iteration | vs hand | Output |",
            "|---|---:|---:|---:|---|"]
    hand = statistics.median(times["hand"]) - base
    for v in ("macros", "hand", "woven"):
        t = statistics.median(times[v]) - base
        rows.append("| %s | %.3f | %.1f | %.2fx | %s |" % (
            v, t, 1e6 * t / n, t / hand if hand > 0 else 0.0, out[v]))
    text = "\n".join(rows)
    print("\n" + text)
    dest = os.environ.get("BM_RESULTS")
    if dest:
        with open(dest, "w") as fp:
            fp.write(text + "\n")
    assert out["macros"].split()[:2] == out["hand"].split()[:2] == out["woven"].split()[:2]
