"""pack: do_pack/do_unpack round-trip through uvm_packer."""
import os

import pytest

from .conftest import uvm_weave_sim

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.sim


def test_pack(dvflow):
    uvm_weave_sim(dvflow, os.path.join(HERE, "pack")).assert_pass()
