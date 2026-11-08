"""Shared pytest configuration for sv-weave-uvm."""
import importlib.util

# pytest-dfm has no pytest11 entry point; load its dvflow fixture explicitly. Without it
# (as in a plain CI venv) the sim tests are skipped; see tests/sim/conftest.py.
pytest_plugins = ["pytest_dfm"] if importlib.util.find_spec("pytest_dfm") else []
