"""uvm_basic (ported from sv-weave tests/sim/test_uvm_example.py): copy, compare and
print woven for a `uvm_object_utils class, with `binding: uvm` found through the
entry point (no plugin-path), on Verilator's UVM."""
import os

import pytest

from .conftest import uvm_weave_sim

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.sim


def test_uvm_basic(dvflow):
    r = uvm_weave_sim(dvflow, os.path.join(HERE, "uvm_basic"))
    r.assert_pass()
    text = r.text.split("STRING ", 1)[1].split("SV_WEAVE_TEST", 1)[0]
    assert text.splitlines()[:3] == ["addr: 'h12", "data: 'hcafe", "payload: '{'h1, 'h2, 'h3}"]
    assert "begin_event" not in text      # UVM's own fields are not woven
    assert "Woven_" not in r.text         # woven classes show the user's type names
