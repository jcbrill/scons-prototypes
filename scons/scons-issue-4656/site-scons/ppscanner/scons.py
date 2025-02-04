# SPDX-FileCopyrightText: Copyright 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

__all__ = [
    "CConditionalModScanner",
]

import SCons.Node.FS

from SCons.Scanner.C import (
    SConsCPPConditionalScanner,
    SConsCPPConditionalScannerWrapper,
    dictify_CPPDEFINES,
)

from ._preprocess import preprocess_text

class SConsCPPConditionalModScanner(SConsCPPConditionalScanner):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.cpppath = tuple(kwargs["cpppath"])

    def read_file(self, file) -> str:
        text = file.rfile().get_text_contents()
        text = preprocess_text(text)
        return text

    def find_include_file(self, t):
        keyword, quote, fname = t
        if quote == '"':
            paths = (self.current_file.dir,) + self.cpppath
        else:
            paths = self.cpppath
        result = SCons.Node.FS.find_file(fname, paths)
        if not result:
            self.missing.append((fname, self.current_file))
        return result

class SConsCPPConditionalModScannerWrapper(SConsCPPConditionalScannerWrapper):

    def __call__(self, node, env, path=(), depth=-1):
        cpp = SConsCPPConditionalModScanner(
            current=node.get_dir(),
            cpppath=path,
            dict=dictify_CPPDEFINES(env),
            depth=depth,
        )
        result = cpp(node)
        for included, includer in cpp.missing:
            fmt = "No dependency generated for file: %s (included from: %s) -- file not found"
            SCons.Warnings.warn(
                SCons.Warnings.DependencyWarning, fmt % (included, includer)
            )
        return result

    def recurse_nodes(self, nodes):
        return []

def CConditionalModScanner():
    return SConsCPPConditionalModScannerWrapper("CConditionalModScanner", "CPPPATH")
