"""component: woven uvm_component classes in a test -> env -> agent -> driver hierarchy
built by run_test() and type_id::create(name, this); a parameterized class."""
import os

import pytest

from .conftest import uvm_weave_sim

HERE = os.path.dirname(os.path.abspath(__file__))

pytestmark = pytest.mark.sim


def test_component(dvflow):
    uvm_weave_sim(dvflow, os.path.join(HERE, "component")).assert_pass()
