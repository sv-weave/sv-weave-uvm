"""seed: the same seed gives the same randomisation under +weave_profile=release and
+weave_profile=debug (debug adds xcheck after randomize, which uses no random numbers)."""
import os
import re

import pytest

from .conftest import uvm_weave_sim_runs

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.sim


def test_seed(dvflow):
    rs = uvm_weave_sim_runs(dvflow, os.path.join(HERE, "seed"), runs={
        "release": ["weave_profile=release"],
        "debug": ["weave_profile=debug"],
    })
    vals = {}
    for name, r in rs.items():
        r.assert_pass()
        vals[name] = re.findall(r"^(?:VALUES|URANDOM) .*$", r.text, re.M)
    assert "IMPL debug" in rs["debug"].text
    assert "IMPL release" in rs["release"].text
    assert len(vals["release"]) == 5
    assert vals["release"] == vals["debug"]
