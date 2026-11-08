"""assess/ports: real transaction classes ported to sv-weave, simulated next to the
original to show the gaps assess/gaps.py reports are closed."""
import os

import pytest

from .conftest import uvm_weave_sim

PORTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "assess", "ports")

pytestmark = pytest.mark.sim


def test_memory_txn(dvflow):
    uvm_weave_sim(dvflow, os.path.join(PORTS, "memory_txn")).assert_pass()
