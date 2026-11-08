# Sphinx configuration for the sv-weave-uvm documentation.
#
# Plan notes under plan/ are Markdown working documents, kept outside the Sphinx build.
import os
import sys

# Use the installed sv_weave_uvm when there is one (CI installs it); fall back to the
# source tree.
try:
    import sv_weave_uvm  # noqa: F401
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sv_weave_uvm.__version__ import __version__  # noqa: E402

project = "sv-weave-uvm"
author = "Matthew Ballance"
copyright = "2026, Matthew Ballance"
version = __version__
release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

# The feature -> hook table is generated from UvmBinding.features(), so it cannot drift.
from sv_weave_uvm.binding import UvmBinding  # noqa: E402

_GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_generated")
os.makedirs(_GEN, exist_ok=True)


def _features_table():
    rows = [("Feature (``weavers: - name:``)", "UVM hook overridden", "Signature")]
    for name, spec in UvmBinding().features().items():
        sig = "%s %s(%s)" % (spec.ret or "void", spec.method, ", ".join(spec.args))
        rows.append(("``%s``" % name, "``%s``" % spec.method, "``%s``" % sig))
    out = [".. list-table::", "   :header-rows: 1", ""]
    for r in rows:
        out.append("   * - " + r[0])
        out.extend("     - " + c for c in r[1:])
    return "\n".join(out) + "\n"


_text = _features_table()
_path = os.path.join(_GEN, "features.rst")
if not os.path.isfile(_path) or open(_path).read() != _text:
    with open(_path, "w") as _fp:
        _fp.write(_text)

exclude_patterns = ["_build", "_generated", "plan", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
