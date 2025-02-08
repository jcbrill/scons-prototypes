# SPDX-FileCopyrightText: Copyright (c) 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

__all__ = [
    "scanner_configuration",
    "scanner_dependencies",
]

import ast
import os
from typing import Any, Dict, List, NamedTuple, Optional

import SCons.Script
import SCons.Scanner.C
import SCons.Tool

import ppscanner

_DISPLAY = False
_VERBOSE = False

def display(*args, **kwargs):
    if _DISPLAY:
        print(*args, **kwargs)

def verbose(*args, **kwargs):
    if _VERBOSE:
        print(*args, **kwargs)

_UNDEFINED = object()

SCons.Script.AddOption(
    "--msvc-compiler",
    dest="msvc_compiler",
    action='store_true',
    default=False,
)

SCons.Script.AddOption(
    "--scanner",
    dest="scanner",
    type="string",
    action="store",
    default="CPreProcessorScanner",
)

SCons.Script.AddOption(
    "--expected-map",
    dest="expected_map",
    type="string",
    action="store",
    default=_UNDEFINED,
)

SCons.Script.AddOption(
    "--expected-scanner-map",
    dest="expected_scanner_map",
    type="string",
    action="store",
    default=_UNDEFINED,
)

SCons.Script.AddOption(
    "--scanner-deps",
    dest="scanner_dependencies",
    action='store_true',
    default=False,
)

class _ScannerConfig(NamedTuple):
    tools: List[str]
    scanner: Any
    scanner_label: str
    scanner_name: str
    scanner_kind: str
    scanner_registered: bool
    scanner_expected_map: Optional[Dict[str, List[str]]]
    scanner_dependencies: bool
    is_msvc: bool


def scanner_dependencies(scanner, sourcenode, env, cpppath, recurse=True):
    # TODO(JCB): detect cycle (infinite loop possible)
    result_nodes = []
    result_seen = set()
    nodes = [sourcenode]
    while nodes:
        node = nodes.pop()
        included_nodes = scanner(node, env, cpppath)
        if included_nodes:
            for node in included_nodes:
                abspath_t = ppscanner.file_abspath_normalize(node.get_abspath())
                abspath = abspath_t.file_abspath
                if abspath in result_seen:
                    continue
                result_seen.add(abspath)
                result_nodes.append(node)
            if recurse:
                nodes.extend(scanner.recurse_nodes(included_nodes))
    return result_nodes

class ScannerConfig(_ScannerConfig):

    def _relpath(self, root_abspath, node):
        path_str = str(node)
        node_abspath = node.get_abspath()
        try:
            common_path = os.path.commonpath([root_abspath, node_abspath])
        except ValueError:
            common_path = None
        if common_path:
            rel_root_common = os.path.normpath(os.path.relpath(common_path, root_abspath))
            if rel_root_common != ".":
                node_head, node_tail = os.path.split(node_abspath)
                rel_node_common = os.path.relpath(node_head, common_path)
                path_str = os.path.join(rel_root_common, rel_node_common, node_tail)
        return path_str

    def dependencies(self, sourcefile, env, recurse=True):
        display("dependendencies:beg")
        if self.scanner_expected_map is None or sourcefile not in self.scanner_expected_map:
            print(self.scanner_name)
        else:
            root_abspath = env.Dir(".").get_abspath()
            srcenode = env.File(sourcefile)
            cppdefines = env.subst("$_CPPDEFFLAGS").strip() if "_CPPDEFFLAGS" in env else ""
            cpppath = tuple(env.Dir(env["CPPPATH"])) if "CPPPATH" in env else ()
            result_nodes = scanner_dependencies(self.scanner, srcenode, env, cpppath, recurse=recurse)
            expect_nodes = env.File(self.scanner_expected_map[sourcefile])
            result_abspath = set([ppscanner.file_abspath_normalize(node.get_abspath()).file_abspath for node in result_nodes])
            expect_abspath = set([ppscanner.file_abspath_normalize(node.get_abspath()).file_abspath for node in expect_nodes])
            status = bool(result_abspath == expect_abspath)
            status_msg = {
                False: f"{self.scanner_name} {sourcefile}: !!! DEPENDENCIES DO NOT MATCH !!!",
                True:  f"{self.scanner_name} {sourcefile}: dependencies match",
            }[status]
            if cppdefines:
                print(f"{self.scanner_name} {sourcefile} {cppdefines}")
            # print(f"{self.scanner_name} {sourcefile} result: {[str(node) for node in result_nodes]}")
            # print(f"{self.scanner_name} {sourcefile} expect: {[str(node) for node in expect_nodes]}")
            print(f"{self.scanner_name} {sourcefile} result: {[self._relpath(root_abspath, node) for node in result_nodes]}")
            print(f"{self.scanner_name} {sourcefile} expect: {[self._relpath(root_abspath, node) for node in expect_nodes]}")
            print(status_msg)
        display("dependencies:end")

def _setup_scanner_symbols():

    scanner_defs = {
        "CPreProcessorScanner": ["CPreProcessorScanner", "CPreProcessor", "CPP"],
        "CConditionalModScanner": ["CConditionalModScanner", "CCondModScanner", "CCMod"],
        "CConditionalScanner": ["CConditionalScanner", "CCondScanner", "CCond"],
        "CScanner": ["Default", "CScanner", "C"],
    }

    scanner_seen = set()
    scanner_symbols = []

    scanner_map = {}
    for key, val in scanner_defs.items():
        for sym in val + [key]:
            scanner_map[sym] = key
            scanner_map[sym.lower()] = key
            scanner_map[sym.upper()] = key
            if sym not in scanner_seen:
                scanner_seen.add(sym)
                scanner_symbols.append(sym)

    scanner_validstr = ', '.join([repr(sym) for sym in scanner_symbols])

    return scanner_map, scanner_validstr

_scanner_map, _scanner_validstr = _setup_scanner_symbols()

def scanner_configuration(suffixes=_UNDEFINED):

    if suffixes == _UNDEFINED:
        suffixes = SCons.Tool.CSuffixes
    elif suffixes is None:
        suffixes = []

    is_msvc = False

    if ppscanner.IS_WINDOWS:
        if SCons.Script.GetOption("msvc_compiler"):
            tools = ["msvc", "mslink"]
            cpp_scanner = ppscanner.MSVCPreProcessorScanner
            cpp_scanner_kind = "MSVC"
            is_msvc = True
        else:
            tools = ["mingw"]
            cpp_scanner = ppscanner.GCCPreProcessorScanner
            cpp_scanner_kind = "GCC"
    else:
        tools = ["gcc", "gnulink"]
        cpp_scanner = ppscanner.GCCPreProcessorScanner
        cpp_scanner_kind = "GCC"

    user_scanner = SCons.Script.GetOption("scanner")
    scanner_str = _scanner_map.get(user_scanner)
    if scanner_str is None:
        errmsg = f"Unsupported c scanner specification: {user_scanner!r}\n  Valid values are: {_scanner_validstr}"
        raise RuntimeError(errmsg)

    register_scanner = True if suffixes else False

    if scanner_str == "CPreProcessorScanner":
        c_scanner = cpp_scanner()
        c_scanner_kind = cpp_scanner_kind
    elif scanner_str == "CConditionalModScanner":
        c_scanner = ppscanner.CConditionalModScanner()
        c_scanner_kind = "CCMod"
    elif scanner_str == "CConditionalScanner":
        c_scanner = SCons.Scanner.C.CConditionalScanner()
        c_scanner_kind = "CCond"
    elif scanner_str == "CScanner":
        c_scanner = SCons.Scanner.C.CScanner()
        c_scanner_kind = "C"
    else:
        raise RuntimeError("InternalError")

    if register_scanner:
        for suffix in suffixes:
            verbose("register suffix", suffix, c_scanner)
            SCons.Script.SourceFileScanner.add_scanner(suffix, c_scanner)

    expected_scanner_str = SCons.Script.GetOption("expected_scanner_map")
    expected_scanner = ast.literal_eval(expected_scanner_str) if expected_scanner_str != _UNDEFINED else None

    expected_scanner_dict = {}
    if expected_scanner:
        for keys, val in expected_scanner:
                for key in keys:
                    expected_scanner_dict[key] = val

    expected_str = SCons.Script.GetOption("expected_map")
    expected_dict = ast.literal_eval(expected_str) if expected_str != _UNDEFINED else None

    if expected_scanner_dict and c_scanner_kind in expected_scanner_dict:
        expected_map = expected_scanner_dict[c_scanner_kind]
    else:
        expected_map = expected_dict

    scanner_cfg = ScannerConfig(
        tools=tools,
        scanner=c_scanner,
        scanner_label=scanner_str,
        scanner_name=c_scanner.name,
        scanner_kind=c_scanner_kind,
        scanner_registered=register_scanner,
        scanner_expected_map=expected_map,
        scanner_dependencies=SCons.Script.GetOption("scanner_dependencies"),
        is_msvc=is_msvc,
    )

    return scanner_cfg
