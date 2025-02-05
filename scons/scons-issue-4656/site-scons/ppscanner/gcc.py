# SPDX-FileCopyrightText: Copyright (c) 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

# gcc command-line options:
#  -fsyntax-only ?

__all__ = [
    "GCCPreProcessorScanner",
]

import re
from typing import NamedTuple, Optional

from ._common import (
    FileAbsPathType,
    PreProcessorScannerBase,
    ScanError,
    ScanIncludeDepthWarning,
    env_subst,
    file_abspath_normalize,
    platform_join_args,
    platform_split_args,
    subprocess_run,
    warn_message,
)

_COMMAND = True
_DISPLAY = False
_VERBOSE = False
_CROSSCHECK = False

class _GCCPreProcessor:

    PROGRAM_NAME = "gcc"
    LABEL = "GCC"

    # linemarker flags:
    #   1: This indicates the start of a new file.
    #   2: This indicates returning to a file (after having included another file).
    #   3: This indicates that the following text comes from a system header file, so certain warnings should be suppressed.
    #   4: This indicates that the following text should be treated as being wrapped in an implicit extern "C" block.

    FLAG_ENTER_FILE = "1"
    FLAG_EXIT_FILE = "2"
    FLAG_SYSTEM_FILE = "3"

    re_stdout_startswith_octothorpe = re.compile(
        r'^\s*#\s*',
        re.IGNORECASE,
    )

    re_stdout_linemarker = re.compile(
        r'^#\s+(?P<lineno>[0-9]+)\s+(?:"(?P<filespec>([^"\\]|\\.)*)")(?P<flagspec>(?:\s+[0-9])*)$',
        re.IGNORECASE,
    )

    re_stdout_include = re.compile(
        r'^\s*#\s*(?P<directive>import|include|include_next)\s*(?P<inclspec>(?:<[^>]+>)|(?:"[^"]+"))\s*$',
        re.IGNORECASE,
    )

    class LinemarkerRecord(NamedTuple):
        abspath_record: FileAbsPathType
        lineno: int

    class IncludeDirective(NamedTuple):
        directive: str
        file_spec: str
        incl_kind: str

    class IncludeStdOut(NamedTuple):
        srce_linemarker_record: "_GCCPreProcessor.LinemarkerRecord"
        abspath_record: FileAbsPathType
        include_directive: Optional["_GCCPreProcessor.IncludeDirective"]
        depth: int
        is_systemfile: bool

    class IncludeStdErr(NamedTuple):
        abspath_record: FileAbsPathType
        depth: int

    re_stderr_include = re.compile(
        r"^(?P<depth>[.]+)[x!]?\s+(?P<filespec>.+)$",
        re.IGNORECASE,
    )

    @classmethod
    def _preprocessor_stdout(cls, env, srcenode, contents):

        include_records = []

        if contents:

            srce_abspath_record = file_abspath_normalize(srcenode.get_abspath())

            abspath_record_map = {
                srce_abspath_record.file_abspath: srce_abspath_record
            }

            depth = 0
            prev_linemarker_record = None
            prev_include_directive = None

            for line in contents.splitlines():

                # print(line)

                if not cls.re_stdout_startswith_octothorpe.search(line):
                    # skip: not preprocessor record
                    continue

                # print(line)

                m = cls.re_stdout_linemarker.match(line)
                if m:
                    # linemarker:begin

                    lineno = int(m.group("lineno"))
                    filespec = m.group("filespec")
                    flagspec = m.group("flagspec")

                    abspath_record = abspath_record_map.get(filespec)
                    if not abspath_record:
                        abspath_record = file_abspath_normalize(filespec)
                        abspath_record_map[abspath_record.file_abspath] = abspath_record

                    linemarker_record = cls.LinemarkerRecord(
                        abspath_record=abspath_record,
                        lineno=lineno,
                    )

                    flags = set(flagspec.split()) if flagspec else set()

                    if cls.FLAG_ENTER_FILE in flags:

                        depth += 1
                        if prev_include_directive:

                            include_record = cls.IncludeStdOut(
                                srce_linemarker_record=prev_linemarker_record,
                                abspath_record=abspath_record,
                                include_directive=prev_include_directive,
                                depth=depth,
                                is_systemfile=bool(cls.FLAG_SYSTEM_FILE in flags),
                            )
                            include_records.append(include_record)

                            if _DISPLAY:
                                print(f"{cls.LABEL}:stdout:incl {'.' * include_record.depth} {include_record.abspath_record.file_abspath}")

                    elif cls.FLAG_EXIT_FILE in flags:
                        depth -= 1

                    prev_linemarker_record = linemarker_record

                    # linemarker:end
                    continue

                m = cls.re_stdout_include.match(line)
                if m:
                    # include:begin

                    seen_include = True
                    inclspec = m.group("inclspec")

                    include_directive = cls.IncludeDirective(
                        directive=m.group("directive"),
                        file_spec=inclspec[1:-1],
                        incl_kind=inclspec[0]
                    )

                    prev_include_directive = include_directive

                    # include:end
                    continue

            if depth:
                warnmsg = f"Warning: Include visit depth ({depth}) > 0 on exit"
                warn_message(warnmsg, ScanIncludeDepthWarning)

        if _VERBOSE:
            for (indx, include_record) in enumerate(include_records):
                print(f"{cls.__name__} stdout include {indx} {include_record.abspath_record.file_abspath} {include_record.is_systemfile}")

        return include_records

    @classmethod
    def _preprocessor_stderr(cls, env, contents):

        include_records = []

        if contents:

            for line in contents.splitlines():

                m = cls.re_stderr_include.match(line)
                if m:
                    # include:begin

                    if _DISPLAY:
                        print(f"{cls.LABEL}:stderr:line {line}")

                    abspath_record = file_abspath_normalize(m.group("filespec"))
                    depth = len(m.group("depth"))

                    include_record = cls.IncludeStdErr(
                        abspath_record=abspath_record,
                        depth=depth,
                    )
                    include_records.append(include_record)

                    # include:end
                    continue

        if _VERBOSE:
            for indx, include_record in enumerate(include_records):
                print(f"{cls.__name__} stderr include {indx} {include_record.depth} {include_record.abspath_record.file_abspath}")

        return include_records

    @classmethod
    def scan(cls, node, env, path, arg=None):

        node = env.File(node)

        prog_name = cls.PROGRAM_NAME
        prog = env.WhereIs(prog_name)
        if not prog:
            errmsg = f"program {prog_name!r} was not found"
            raise ScanError(errmsg)

        cmd = [prog, "-fsyntax-only", "-E", "-dI", "-w"]
        if _CROSSCHECK:
            cmd.append("-H")
        for scons_key in ("_CPPDEFFLAGS", "_CPPINCFLAGS"):
            if env and scons_key in env:
                subst_val = env_subst(env, scons_key).strip()
                if not subst_val:
                    continue
                subst_args = platform_split_args(subst_val)
                if not subst_args:
                    continue
                cmd.extend(subst_args)
        cmd.append(node.abspath)

        if _COMMAND or _DISPLAY:
            print(f"{node!s} {cls.LABEL} {platform_join_args(cmd)}")

        outstr, errstr = subprocess_run(cmd, env)

        stdout_records = cls._preprocessor_stdout(env, node, outstr)

        if _CROSSCHECK:

            stderr_records = cls._preprocessor_stderr(env, errstr)

            stdout_set = set([
                (stdout_record.depth, stdout_record.abspath_record.file_abspath)
                for stdout_record in stdout_records
            ])

            stderr_set = set([
                (stderr_record.depth, stderr_record.abspath_record.file_abspath)
                for stderr_record in stderr_records
            ])

            if stdout_set != stderr_set:
                errmsg = (
                    f"{cls.__name__} node sets mis-match:\n"
                    f"  stdout set {len(stdout_set)} = {stdout_set!r}\n"
                    f"  stderr set {len(stderr_set)} = {stderr_set!r}\n"
                    f"  difference = {stdout_set - stderr_set}"
                )
                raise ScanError(errmsg)

        file_seen = set()
        node_list = []
        for stdout_record in stdout_records:
            if stdout_record.is_systemfile:
                continue
            file_abspath = stdout_record.abspath_record.file_abspath
            if file_abspath in file_seen:
                continue
            file_seen.add(file_abspath)
            node_list.append(env.File(file_abspath))

        if _DISPLAY:
            print(f"{node!s} {cls.LABEL} {' '.join([str(p) for p in node_list])}")

        return node_list

class _GCCPreProcessorScanner(PreProcessorScannerBase):

    @staticmethod
    def _scan_function(node, env, path, arg=None):
        rval = _GCCPreProcessor.scan(node, env, path, arg)
        return rval

    def __init__(self):

        name = self.__class__.__name__
        if name[0] == "_":
            name = name[1:]

        super().__init__(
            name=name,
            scan_function=self._scan_function,
        )

def GCCPreProcessorScanner():
    return _GCCPreProcessorScanner()

