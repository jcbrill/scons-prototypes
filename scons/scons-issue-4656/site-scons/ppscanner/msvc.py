# SPDX-FileCopyrightText: Copyright 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

__all__ = [
    "MSVCPreProcessorScanner",
]

import os
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

class _MSVCSystemPaths:

    sysfile_list = [
        "limits.h",
        "stdio.h",
        "windows.h",
        "atlwin.h",
        "afxwin.h",
        "cor.h",
        "limits",
        "iostream",
    ]

    re_syspaths = [
        # re.compile(r'^(?P<prefix>.+[/\\])$', re.IGNORECASE),

        re.compile(r'^(?P<prefix>.+[\\])(?:vc[\\](?:tools|auxiliary)[\\].*)$', re.IGNORECASE),

        re.compile(r'^(?P<prefix>.+[\\]windows kits[\\]netfxsdk[\\][1-9][0-9.]+[\\])(?:include(?:[\\].*)?)$', re.IGNORECASE),
        re.compile(r'^(?P<prefix>.+[\\]windows kits[\\][1-9][0-9.]*[\\])(?:include(?:[\\].*)?)$', re.IGNORECASE),
        re.compile(r'^(?P<prefix>.+[\\]microsoft sdks[\\]windows[\\]v[1-9][0-9.]+[a]?[\\])(?:include(?:[\\].*)?)$', re.IGNORECASE),

        re.compile(r'^(?P<prefix>.+[\\])(?:frameworksdk[\\]include(?:[\\].*)?)$', re.IGNORECASE),
        re.compile(r'^(?P<prefix>.+[\\])(?:VC[0-9]*[\\]include(?:[\\].*)?)$', re.IGNORECASE),
        re.compile(r'^(?P<prefix>.+[\\])(?:VC[0-9]*[\\](?:atl|mfc|atlmfc|platformsdk)[\\]include(?:[\\].*)?)$', re.IGNORECASE),

    ]

    _cache_re_sysprefix = {}

    @classmethod
    def sysprefix_regex(cls, env):

        re_sysprefix = None

        if not env:
            return re_sysprefix

        ENV = env.get("ENV")
        if not ENV:
            return re_sysprefix

        include_path = ENV.get("INCLUDE", "").strip()
        if not include_path:
            return re_sysprefix

        include_paths = include_path.split(os.pathsep)

        incpath_list = []
        incpath_seen = set()

        for incpath in include_paths:
            incpath = incpath.strip()
            if not incpath:
                continue
            abspath_record = file_abspath_normalize(incpath)
            file_abspath = abspath_record.file_abspath
            if not os.path.exists(file_abspath):
                continue
            if file_abspath in incpath_seen:
                continue
            incpath_seen.add(file_abspath)
            incpath_list.append(file_abspath)

        if not incpath_list:
            return re_sysprefix

        cache_key = os.pathsep.join(sorted(incpath_list))
        if cache_key in cls._cache_re_sysprefix:
            re_sysprefix = cls._cache_re_sysprefix[cache_key]
            return re_sysprefix

        sysprefix_list = []
        sysprefix_seen = set()

        for incpath in incpath_list:
            for sysfile in cls.sysfile_list:
                filename = os.path.join(incpath, sysfile)
                if not os.path.exists(filename):
                    continue
                for regex in cls.re_syspaths:
                    m = regex.match(incpath)
                    if not m:
                        continue
                    sysprefix = m.group("prefix")
                    if sysprefix not in sysprefix_seen:
                        sysprefix_seen.add(sysprefix)
                        sysprefix_list.append(sysprefix)

        re_sysprefix = re.compile(
            "^(:?" + "|".join([re.escape(p) for p in sysprefix_list]) + ").*$",
            re.IGNORECASE,
        )

        unmatched = []
        for incpath in incpath_list:
            if not re_sysprefix.match(incpath):
                unmatched.append(f"  unmatched syspath: {incpath!r}")

        if unmatched:
            errmsg = f"{cls.__name__} {len(unmatched)} unmatched syspaths:\n"
            errmsg += "\n".join(unmatched)
            raise ScanError(errmsg)

        if _VERBOSE:
            for sysprefix in sysprefix_list:
                print(f"{cls.__name__} msvc sysprefix: {sysprefix}")

        cls._cache_re_sysprefix[cache_key] = re_sysprefix
        return re_sysprefix

class _MSVCPreProcessor:

    PROGRAM_NAME = "cl"
    LABEL = "MSVC"

    re_stdout_startswith_octothorpe = re.compile(
        r'^\s*#\s*',
        re.IGNORECASE,
    )

    re_stdout_linemarker = re.compile(
        r'^(?P<leadws>\s*)#\s*line\s+(?P<lineno>[0-9]+)\s+(?:"(?P<filespec>([^"\\]|\\.)*)")\s*$',
        re.IGNORECASE,
    )

    # TODO(JCB): i18n (language-specific: "Note: including file:")
    re_stderr_include = re.compile(
        r"^Note[:] including file[:](?P<depth>\s+)(?P<filespec>.+)$",
        re.IGNORECASE,
    )

    class LinemarkerRecord(NamedTuple):
        abspath_record: FileAbsPathType
        lineno: int

    class IncludeStdOut(NamedTuple):
        srce_linemarker_record: "_MSVCPreProcessor.LinemarkerRecord"
        abspath_record: FileAbsPathType
        depth: int
        is_systemfile: bool

    class IncludeStdErr(NamedTuple):
        abspath_record: FileAbsPathType
        depth: int

    @classmethod
    def _preprocessor_stdout(cls, env, srcenode, contents):

        include_records = []

        if contents:

            include_stack = []

            srce_abspath_record = file_abspath_normalize(srcenode.get_abspath())

            abspath_record_map = {
                srce_abspath_record.file_abspath: srce_abspath_record
            }

            re_sysprefix = _MSVCSystemPaths.sysprefix_regex(env)
            prev_linemarker_record = None

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

                    abspath_record = abspath_record_map.get(filespec)
                    if not abspath_record:
                        abspath_record = file_abspath_normalize(filespec)
                        abspath_record_map[abspath_record.file_abspath] = abspath_record

                    linemarker_record = cls.LinemarkerRecord(
                        abspath_record=abspath_record,
                        lineno=lineno,
                    )

                    if prev_linemarker_record:

                        if lineno <= 1:
                            # enter file
                            include_stack.append(linemarker_record)

                            if re_sysprefix and re_sysprefix.match(abspath_record.file_abspath):
                                is_systemfile = True
                            else:
                                is_systemfile = False

                            include_record = cls.IncludeStdOut(
                                srce_linemarker_record=prev_linemarker_record,
                                abspath_record=abspath_record,
                                depth=len(include_stack),
                                is_systemfile=is_systemfile,
                            )
                            include_records.append(include_record)

                            if _DISPLAY:
                                print(f"{cls.LABEL}:stdout:incl{' ' * include_record.depth} {include_record.abspath_record.file_abspath}")

                        elif prev_linemarker_record.abspath_record != linemarker_record.abspath_record:
                            # exit file
                            include_stack.pop()

                    prev_linemarker_record = linemarker_record

                    # linemarker:end
                    continue

            if len(include_stack):
                depth = len(include_stack)
                warnmsg = f"Warning: Include visit depth ({depth}) > 0 on exit"
                warn_message(warnmsg, ScanIncludeDepthWarning)

        if _VERBOSE:
            for (indx, inclfile_record) in enumerate(include_records):
                print(f"{cls.__name__} stdout include {indx} {include_record.depth} {include_record.abspath_record.file_abspath} {include_record.is_systemfile}")

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

        cmd = [prog, "/nologo", "/E", "/w"]
        if _CROSSCHECK:
            cmd.append("/showIncludes")
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

            stdout_seen = bool(len(stdout_records))
            stderr_seen = bool(len(stderr_records))

            stdout_set = set([
                (stdout_record.depth, stdout_record.abspath_record.file_abspath)
                for stdout_record in stdout_records
            ])

            stderr_set = set([
                (stderr_record.depth, stderr_record.abspath_record.file_abspath)
                for stderr_record in stderr_records
            ])

            if stdout_set == stderr_set:
                # sets match
                pass
            elif stdout_seen and not stderr_seen:
                # /showIncludes may not be available (need cl version check)
                pass
            else:
                errmsg = (
                    f"{cls.__name__} node sets mis-match:\n"
                    f"  stdout set = {stdout_set!r}\n"
                    f"  stderr set = {stderr_set!r}\n"
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

class _MSVCPreProcessorScanner(PreProcessorScannerBase):

    @staticmethod
    def _scan_function(node, env, path, arg=None):
        rval = _MSVCPreProcessor.scan(node, env, path, arg)
        return rval

    def __init__(self):

        name = self.__class__.__name__
        if name[0] == "_":
            name = name[1:]

        super().__init__(
            name=name,
            scan_function=self._scan_function,
        )

def MSVCPreProcessorScanner():
    return _MSVCPreProcessorScanner()

