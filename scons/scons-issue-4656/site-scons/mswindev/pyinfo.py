# SPDX-FileCopyrightText: Copyright (c) 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

# minimal shim for pyargs

from typing import List, NamedTuple

__all__: List[str] = [
    "pyplatform_cfg",
]

import os
import sys


class PyPlatformConfig(NamedTuple):
    IS_WINDOWS: bool
    IS_POSIX: bool

pyplatform_cfg = PyPlatformConfig(
    IS_WINDOWS=bool(sys.platform.startswith("win")),
    IS_POSIX=bool(os.name == "posix"),
)
