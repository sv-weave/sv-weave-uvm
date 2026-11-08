"""sv-weave-uvm: the UVM library for sv-weave (binding, factory adapter, UVM weavers)."""
import os

from .__version__ import __version__

#: Directory of the SystemVerilog sources shipped with the package.
SV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "share", "sv")
