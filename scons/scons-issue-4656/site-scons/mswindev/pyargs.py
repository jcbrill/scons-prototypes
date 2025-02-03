# Copyright 2025 Joseph C. Brill
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Command-line argument utilities."""

from typing import Callable, List

__all__: List[str] = [
    "nonposix_join_args",
    "nonposix_quote_arg",
    "nonposix_quote_args",
    "nonposix_split_args",
    "platform_join_args",
    "platform_quote_arg",
    "platform_quote_args",
    "platform_split_args",
    "posix_join_args",
    "posix_quote_arg",
    "posix_quote_args",
    "posix_split_args",
    "windows_join_args",
    "windows_quote_arg",
    "windows_split_args",
    "windows_split_args_commandline",
    "windows_split_args_commandlinetoargv",
    "windows_split_args_string",
]

import re
import shlex

from . import pyinfo

# windows

class _Windows:

    # https://learn.microsoft.com/en-us/cpp/c-language/parsing-c-command-line-arguments?view=msvc-170
    #
    # Microsoft C startup code uses the following rules when interpreting arguments given on the operating
    # system command line:
    #
    # * Arguments are delimited by whitespace characters, which are either spaces or tabs.
    #
    # * The first argument (argv[0]) is treated specially. It represents the program name.
    #   Because it must be a valid pathname, parts surrounded by double quote marks (") are allowed.
    #   The double quote marks aren't included in the argv[0] output. The parts surrounded by double
    #   quote marks prevent interpretation of a space or tab character as the end of the argument.
    #   The later rules in this list don't apply.
    #
    # * A string surrounded by double quote marks is interpreted as a single argument, whether it contains
    #   whitespace characters or not. A quoted string can be embedded in an argument. The caret (^) isn't
    #   recognized as an escape character or delimiter. Within a quoted string, a pair of double quote marks
    #   is interpreted as a single escaped double quote mark. If the command line ends before a closing double
    #   quote mark is found, then all the characters read so far are output as the last argument.
    #
    # * A double quote mark preceded by a backslash (\") is interpreted as a literal double quote mark (").
    #
    # * Backslashes are interpreted literally, unless they immediately precede a double quote mark.
    #
    # * If an even number of backslashes is followed by a double quote mark, then one backslash (\) is placed
    #   in the argv array for every pair of backslashes (\\), and the double quote mark (") is interpreted as a
    #   string delimiter.
    #
    # * If an odd number of backslashes is followed by a double quote mark, then one backslash (\) is placed in
    #   the argv array for every pair of backslashes (\\). The double quote mark is interpreted as an escape sequence
    #   by the remaining backslash, causing a literal double quote mark (") to be placed in argv.
    #

    # https://daviddeley.com/autohotkey/parameters/parameters.htm
    #
    # 5.  The C/C++ Parameter Parsing Rules
    #
    # 5.2  The Microsoft C/C++ Parameter Parsing Rules Rephrased
    #      These are the rules for parsing a command line passed by CreateProcess() to a program written in C/C++:
    #      1. Parameters are always separated by a space or tab (multiple spaces/tabs OK)
    #      2. If the parameter does not contain any spaces, tabs, or double quotes, then all the characters in the
    #         parameter are accepted as is (there is no need to enclose the parameter in double quotes).
    #      3. Enclose spaces and tabs in a double quoted part
    #      4. A double quoted part can be anywhere within a parameter
    #      5. 2n backslashes followed by a " produce n backslashes + start/end double quoted part
    #      6. 2n+1 backslashes followed by a " produce n backslashes + a literal quotation mark
    #      7. n backslashes not followed by a quotation mark produce n backslashes
    #      8. undocumented rules regarding double quotes:
    #         * Prior to 2008:
    #           * A " outside a double quoted block starts a double quoted block
    #           * A " inside a double quoted block ends the double quoted block
    #           * If a closing " is followed immediately by another ", the 2nd " is accepted literally and added to the
    #             parameter.
    #         * Post 2008:
    #           * Outside a double quoted block a " starts a double quoted block.
    #           * Inside a double quoted block a " followed by a different character (not another ")
    #             ends the double quoted block.
    #           * Inside a double quoted block a " followed immediately by another " (i.e. "") causes a single " to be
    #             added to the output, and the double quoted block continues.
    #
    # 5.3  Summary of rules 5,6,7:
    #      Use " to start/end a double quoted part
    #      Use \" to insert a literal "
    #      Use \\" to insert a \ then start or end a double quoted part
    #      Use \\\" to insert a literal \"
    #      Use \ to insert a literal \

    # Implementation Notes:
    #     ***Empirical evidence suggests the undocumented behavior above changed between 2003 and 2005***
    #     Python/C argv appears to be consistent with 2005 and later behavior (ge2005=True)
    #     CommandLineToArgv appears to be consistent with 2003 and earlier behavior (ge2005=False)

    _whitespace_chars = " \t"

    @classmethod
    def split_string(cls, argstr: str, *, ge2005: bool = False) -> List[str]:

        args: List[str] = []

        if not argstr:
            return args

        in_quoted_block = False
        n_backslash = 0

        have_arg = False
        arg = ""

        nchar = len(argstr)
        argstr += " " * 2  # lookahead padding

        indx = 0
        while indx < nchar:
            c = argstr[indx]
            indx += 1

            if c == "\\":
                # backslash
                have_arg = True
                n_backslash += 1
                continue

            if c == '"':
                # double quote
                have_arg = True
                if n_backslash:
                    if n_backslash % 2 == 0:
                        # 2n backslashes followed by "
                        arg += (n_backslash // 2) * "\\"
                        in_quoted_block = not in_quoted_block
                    else:
                        # 2n+1 backslashes followed by "
                        arg += (n_backslash // 2) * "\\" + '"'
                    n_backslash = 0
                elif in_quoted_block:
                    # indx is lookahead character
                    peek_quote = bool(argstr[indx] == '"')
                    if peek_quote:
                        arg += '"'
                        indx += 1
                    if not ge2005 or not peek_quote:
                        # in a quoted block
                        #    LE 2003: a " ends the block
                        #    GE 2005: a " followed by a different character ends the block
                        in_quoted_block = False
                else:
                    in_quoted_block = True
                continue

            if n_backslash:
                # add backslashes
                arg += n_backslash * "\\"
                n_backslash = 0

            if not in_quoted_block and c in cls._whitespace_chars:
                # whitespace ends token for non-quoted block
                if have_arg or arg:
                    # add argument
                    args.append(arg)
                    have_arg = False
                    arg = ""
                continue

            # add character
            have_arg = True
            arg += c

        # end-of-input: finalize last argument

        if n_backslash:
            # add backslashes
            arg += n_backslash * "\\"
            n_backslash = 0

        if have_arg or arg:
            # add argument
            args.append(arg)
            have_arg = False
            arg = ""

        return args

    @classmethod
    def split_string_commandline(cls, argstr: str) -> List[str]:
        rval = cls.split_string(argstr, ge2005=True)
        return rval

    @classmethod
    def split_string_commandlinetoargv(cls, argstr: str) -> List[str]:
        rval = cls.split_string(argstr, ge2005=False)
        return rval

    _needquotes_chars = '"' + _whitespace_chars
    _needquotes_re = re.compile("[" + _needquotes_chars + "]")

    @classmethod
    def quote_string(cls, argstr: str) -> str:

        if not argstr:
            return '""'

        if not cls._needquotes_re.search(argstr):
            return argstr

        n_backslash = 0
        arg = '"'  # opening quote

        for c in argstr:

            if c == "\\":
                n_backslash += 1
                continue

            if c == '"':
                # 2n+1 backslashes followed by a " produce n backslashes + a literal quotation mark
                n_backslash *= 2  # escape backslashes (2n)
                n_backslash += 1  # escape doublequote (+1)

            if n_backslash:
                arg += n_backslash * "\\"
                n_backslash = 0

            arg += c

        if n_backslash:
            # 2n backslashes followed by a " produce n backslashes + start/end double quoted part
            n_backslash *= 2  # escape backslashes (2n)
            arg += n_backslash * "\\"
            n_backslash = 0

        arg += '"'  # closing quote

        return arg

    @classmethod
    def quote_list(cls, args: List[str]) -> List[str]:
        rval = [cls.quote_string(arg) for arg in args]
        return rval

    @classmethod
    def join_list(cls, args: List[str]) -> str:
        rval = " ".join(cls.quote_list(args))
        return rval

windows_split_args_string = _Windows.split_string
windows_split_args_commandline = _Windows.split_string_commandline
windows_split_args_commandlinetoargv = _Windows.split_string_commandlinetoargv

windows_split_args = _Windows.split_string_commandline
windows_quote_arg = _Windows.quote_string
windows_quote_args = _Windows.quote_list
windows_join_args = _Windows.join_list

# posix

class _Posix:

    @classmethod
    def split_string(cls, argstr: str) -> List[str]:
        rval = shlex.split(argstr, posix=True)
        return rval

    @classmethod
    def quote_string(cls, argstr: str) -> str:
        rval = shlex.quote(argstr)
        return rval

    @classmethod
    def quote_list(cls, args: List[str]) -> List[str]:
        rval = [cls.quote_string(arg) for arg in args]
        return rval

    @classmethod
    def join_list(cls, args: List[str]) -> str:
        rval = " ".join(cls.quote_list(args))
        return rval

posix_split_args = _Posix.split_string
posix_quote_arg = _Posix.quote_string
posix_quote_args = _Posix.quote_list
posix_join_args = _Posix.join_list

# non-posix

class _NonPosix(_Posix):

    @classmethod
    def split_string(cls, argstr: str) -> List[str]:
        rval = shlex.split(argstr, posix=False)
        return rval

nonposix_split_args = _NonPosix.split_string
nonposix_quote_arg = _NonPosix.quote_string
nonposix_quote_args = _NonPosix.quote_list
nonposix_join_args = _NonPosix.join_list

# platform: windows, posix, None

platform_split_args: Callable
platform_quote_arg: Callable
platform_quote_args: Callable
platform_join_args: Callable

if pyinfo.pyplatform_cfg.IS_WINDOWS:

    platform_split_args = windows_split_args
    platform_quote_arg = windows_quote_arg
    platform_quote_args = windows_quote_args
    platform_join_args = windows_join_args

elif pyinfo.pyplatform_cfg.IS_POSIX:

    platform_split_args = posix_split_args
    platform_quote_arg = posix_quote_arg
    platform_quote_args = posix_quote_args
    platform_join_args = posix_join_args

else:

    platform_split_args = nonposix_split_args
    platform_quote_arg = nonposix_quote_arg
    platform_quote_args = nonposix_quote_args
    platform_join_args = nonposix_join_args
