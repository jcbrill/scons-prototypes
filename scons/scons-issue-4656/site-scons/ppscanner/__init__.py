__copyright__ = "Copyright (C) 2025 Joseph C. Brill"
__license__ = "MIT License"

__all__ = [
    "IS_WINDOWS",
    "CConditionalModScanner",
    "GCCPreProcessorScanner",
    "FileAbsPathType",
    "MSVCPreProcessorScanner",
    "ScanError",
    "ScanIncludeDepthWarning",
    "ScanWarning",
    "file_abspath_normalize",
    "platform_join_args",
    "platform_split_args",
]

from ._common import (
    FileAbsPathType,
    IS_WINDOWS,
    ScanError,
    ScanIncludeDepthWarning,
    ScanWarning,
    file_abspath_normalize,
    platform_join_args,
    platform_split_args,
)

from .gcc import(
    GCCPreProcessorScanner,
)

from .msvc import(
    MSVCPreProcessorScanner,
)

from .scons import(
    CConditionalModScanner,
)
