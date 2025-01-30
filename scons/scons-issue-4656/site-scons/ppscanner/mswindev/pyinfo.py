__copyright__ = "Copyright (C) 2025 Joseph C. Brill"
__license__ = "MIT License"

# minimal mswindev pyinfo shim

import os
import sys

from typing import NamedTuple

_IS_WINDOWS = bool(sys.platform.startswith("win"))
_IS_POSIX = bool(os.name == "posix")

class PyPlatformConfig(NamedTuple):
    IS_WINDOWS: bool
    IS_POSIX: bool

pyplatform_cfg = PyPlatformConfig(
    IS_WINDOWS=_IS_WINDOWS,
    IS_POSIX=_IS_POSIX,
)
