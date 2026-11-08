"""override_chain: tx -> tx1 -> tx2 overrides (instance and type) resolve to the woven
last link; the adapter's find_override_* runs on every link of the chain."""
import os

import pytest

from .conftest import uvm_weave_sim

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.sim


def test_override_chain(dvflow):
    uvm_weave_sim(dvflow, os.path.join(HERE, "override_chain")).assert_pass()
