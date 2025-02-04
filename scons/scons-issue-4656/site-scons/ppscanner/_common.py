# SPDX-FileCopyrightText: Copyright 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

__all__ = [
    "DEFAULT_ENCODING",
    "IS_ENGLISH",
    "IS_WINDOWS",
    "FileAbsPathType",
    "PreProcessorScannerBase",
    "ScanError",
    "ScanWarning",
    "ScanIncludeDepthWarning",
    "env_substr",
    "file_abspath_normalize",
    "platform_join_args",
    "platform_split_args",
    "subprocess_run",
    "warn_message",
]

import os
import shlex
import subprocess
import sys
import warnings

from typing import List, NamedTuple, Type

import mswindev

import SCons.Action
import SCons.Scanner

IS_WINDOWS = bool(sys.platform.startswith("win"))

DEFAULT_ENCODING = "oem" if IS_WINDOWS else "utf-8"

_UNDEFINED = object()

platform_join_args = mswindev.platform_join_args
platform_split_args = mswindev.platform_split_args

class ScanError(Exception):
    pass

class ScanWarning(Warning):
    pass

class ScanIncludeDepthWarning(ScanWarning):
    pass

class PreProcessorScannerBase(SCons.Scanner.ScannerBase):

    def __init__(
        self,
        *,
        name,
        scan_function,
        suffixes="$CPPSUFFIXES",
        path_variable="CPPPATH",
        argument=None
    ) -> None:

        super().__init__(
            name=name,
            function=scan_function,
            path_function=SCons.Scanner.FindPathDirs(path_variable),
            argument=argument,
            skeys=suffixes,
            recursive=False,
        )

    def __call__(self, node, env, path=_UNDEFINED) -> list:
        if path == _UNDEFINED:
            path = self.path_function(env, argument=self.argument)
        rval = super().__call__(node, env, path)
        return rval

class _FileAbsPathComponentsNT(NamedTuple):
    file_abspath: str
    file_dir: str
    file_name: str

class _FileAbsPathComponents(_FileAbsPathComponentsNT):

    _cache_map = {}

    @classmethod
    def normalize(cls, origpath: str) -> "FileAbsPathType":
        if origpath in cls._cache_map:
            return cls._cache_map[origpath]
        normpath = os.path.normpath(origpath)
        if normpath in cls._cache_map:
            return cls._cache_map[normpath]
        file_abspath = os.path.normpath(normpath)
        if file_abspath in cls._cache_map:
            return cls._cache_map[file_abspath]
        file_dir, file_name = os.path.split(file_abspath)
        abspath_record = cls(
            file_abspath=file_abspath,
            file_dir=file_dir,
            file_name=file_name,
        )
        cls._cache_map[origpath] = abspath_record
        cls._cache_map[normpath] = abspath_record
        cls._cache_map[file_abspath] = abspath_record
        return abspath_record

FileAbsPathType = _FileAbsPathComponents

file_abspath_normalize = _FileAbsPathComponents.normalize

def env_subst(env, var):
    if env and var in env:
        rval = env.subst("$" + var)
    else:
        rval = ""
    return rval

def _decode_cmd_output(buffer, encoding):
    if not buffer:
        return ""
    try:
        return buffer.decode(encoding, errors="strict")
    except UnicodeDecodeError as e:
        pass
    except Exception as e:
        raise
    return buffer.decode(encoding, errors="replace")

def subprocess_run(cmd, env=None, encoding=None, check=False, shell=False):

    if encoding is None:
        encoding = DEFAULT_ENCODING

    cp = SCons.Action.scons_subproc_run(
        env,
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
        shell=shell,
    )

    outstr = _decode_cmd_output(cp.stdout, encoding) if cp.stdout else ""
    errstr = _decode_cmd_output(cp.stderr, encoding) if cp.stderr else ""

    return outstr, errstr

def warn_message(message: str, category: Type):
    warnings.warn(message, category)

