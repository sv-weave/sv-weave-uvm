"""quickstart: runs examples/quickstart/run.sh (the commands docs/quickstart.rst shows)
in a copy of the example, so the example and the docs cannot drift from what works."""
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXAMPLE = os.path.join(ROOT, "examples", "quickstart")

pytestmark = pytest.mark.sim


def test_quickstart(tmp_path):
    if shutil.which("sv-weave") is None:
        pytest.skip("sv-weave is not on PATH")
    work = tmp_path / "quickstart"
    shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("woven", "obj_dir"))
    r = subprocess.run([str(work / "run.sh")], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    log = tmp_path / "run.log"
    log.write_text(r.stdout)
    assert r.returncode == 0, "run.sh failed; log: %s" % log
    assert "QUICKSTART: PASS" in r.stdout, "log: %s" % log
    assert "UVM_FATAL @" not in r.stdout, "log: %s" % log
    assert "payload: '{'h1, 'h2, 'h3}" in r.stdout      # woven convert2string
    assert "  payload  byte" in r.stdout                  # woven do_print (table)
    # the docs include the example's files, and show run.sh's commands
    rst = open(os.path.join(ROOT, "docs", "quickstart.rst")).read()
    for name in ("tx_pkg.sv", "tb.sv", "sv-weave.yaml", "run.sh"):
        assert "examples/quickstart/" + name in rst, name
