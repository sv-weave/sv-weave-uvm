"""print: do_print through uvm_printer (table, tree, line) and convert2string."""
import os

import pytest

from .conftest import uvm_weave_sim

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.sim


def test_print(dvflow):
    uvm_weave_sim(dvflow, os.path.join(HERE, "print")).assert_pass()
