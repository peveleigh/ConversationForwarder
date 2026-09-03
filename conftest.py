"""Root pytest config: expose the integration as `custom_components.conversation_forwarder`."""

from __future__ import annotations

import pathlib
import sys
import types

_root = pathlib.Path(__file__).parent
_pkg = types.ModuleType("custom_components")
_pkg.__path__ = [str(_root)]
sys.modules.setdefault("custom_components", _pkg)
