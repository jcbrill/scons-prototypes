# SPDX-FileCopyrightText: Copyright (c) 2025 Joseph C. Brill
# SPDX-License-Identifier: MIT

# C++ raw strings are not supported
# trigraphs are not supported

import enum
import re
from collections import deque
from typing import NamedTuple

import SCons.Util

from ._common import ScanError

_DISPLAY = True
_VERBOSE = False

class PP1TokenKind(enum.IntEnum):
    EOF = -1
    EOL = 0
    SINGLE_QUOTED = 1
    DOUBLE_QUOTED = 2
    CHUNK = 3
    DIRECTIVE = 4

class PP1TokenRange(NamedTuple):
    kind: PP1TokenKind
    beg_indx: int
    end_indx: int

class PP1TokenText(NamedTuple):
    kind: PP1TokenKind
    text: str

class PP1State(enum.IntEnum):
    NORMAL_CODE = 1
    AFTER_SLASH = 2
    SINGLE_QUOTED = 3
    DOUBLE_QUOTED = 4
    CPP_COMMENT = 5
    C_COMMENT = 6
    C_COMMENT_ASTERISK = 7

class _PreProcessor:

    identifier = r"[a-zA-Z0-9_]+"
    re_directive = re.compile(fr"^\s*#\s*(?P<directive>{identifier})(?P<chunk>.*)$")

    def __call__(self, file):
        self.current_file = file
        return self.process_file(file)

    def read_file(self, file) -> str:
        text = ""
        with open(file, "rb") as f:
            text = SCons.Util.to_Text(f.read())
        return text

    _re_fragment_cont = r"(?P<cont>\\)"  # "\\"
    _re_fragment_eol = r"(?P<eol>\r?\n|\r)"  # "\n", "\r\n", "\r"
    _re_fragment_optcont_eol = f"{_re_fragment_cont}?{_re_fragment_eol}"

    _re_transform_eol = re.compile(_re_fragment_optcont_eol, re.M)
    _re_transform_eos = re.compile(f"{_re_fragment_optcont_eol}$")

    # _re_string_literal = re.compile(r'[^"\\]*(?:\\.[^"\\]*)*')

    @staticmethod
    def _re_transform_eol_sub(m):
        # print(m, m.groupdict())
        rval = "" if m.group("cont") else "\n"
        return rval

    def transform_endoflines(self, text):

        # Notes:
        #  * Trigraphs are NOT transformed.

        if text:

            # Definitions:
            #   CONTINUATION == "\\"
            #   ENDOFLINE == ("\n", "\r\n", "\r")
            #   ZEROLENSTR == ""
            #   NEWLINE == "\n"

            # c++: A source file that is not empty and that does not end in a new-line character,
            # or that ends in a new-line character immediately preceded by a backslash character
            # before any such splicing takes place, shall be processed as if an additional new-line
            # character were appended to the file.

            # Transformations (end-of-string):
            #   CONTINUATION => CONTINUATION NEWLINE NEWLINE
            #   NOT ENDOFLINE => NEWLINE
            #   CONTINUATION ENDOFLINE => CONTINUATION ENDOFLINE NEWLINE

            m = self._re_transform_eos.search(text)
            if not m:
                # no ENDOFLINE at end of string
                if text[-1] == "\\":
                    # error: CONTINUATION => CONTINUATION NEWLINE NEWLINE
                    text += "\n\n"
                else:
                    # add NEWLINE
                    text += "\n"
            elif m['cont']:
                # CONTINUATION ENDOFLINE => CONTINUATION ENDOFLINE NEWLINE
                text += "\n"

            # Transformations:
            #   * splice lines ending with continuation-endofline sequence:
            #       CONTINUATION ENDOFLINE => ZEROLENSTR
            #   * normalize end-of-line sequence:
            #       ENDOFLINE => NEWLINE

            text = self._re_transform_eol.sub(self._re_transform_eol_sub, text)

        return text

    def transform_comments(self, text):

        # Inspired by:
        #   https://cboard.cprogramming.com/c-programming/151818-removing-comments.html

        output = ""

        token_ranges = []

        single_quoted_begindx = 0
        double_quoted_begindx = 0

        prev_char = ""
        prev_char_count = 0

        state = PP1State.NORMAL_CODE
        for indx, char in enumerate(text):

            if state == PP1State.NORMAL_CODE:

                if char == "/":
                    state = PP1State.AFTER_SLASH
                elif char == "'":
                    output += char
                    state = PP1State.SINGLE_QUOTED
                    single_quoted_begindx = len(output) - 1
                elif char == '"':
                    output += char
                    state = PP1State.DOUBLE_QUOTED
                    double_quoted_begindx = len(output) - 1
                else:
                    output += char

            elif state == PP1State.AFTER_SLASH:

                if char == "'":
                    output += "/"
                    output += char
                    state = PP1State.SINGLE_QUOTED
                    single_quoted_begindx = len(output) - 1
                elif char == '"':
                    output += "/"
                    output += char
                    state = PP1State.DOUBLE_QUOTED
                    double_quoted_begindx = len(output) - 1
                elif char == "/":
                    state = PP1State.CPP_COMMENT
                elif char == "*":
                    state = PP1State.C_COMMENT
                else:
                    output += "/"
                    output += char
                    state = PP1State.NORMAL_CODE

            elif state == PP1State.SINGLE_QUOTED:

                output += char
                if char == "'":
                    if not prev_char == "\\" or prev_char_count % 2 == 0:
                        state = PP1State.NORMAL_CODE
                        token_range = PP1TokenRange(
                            kind = PP1TokenKind.SINGLE_QUOTED,
                            beg_indx=single_quoted_begindx,
                            end_indx=len(output),
                        )
                        token_ranges.append(token_range)
                elif char == "\n":
                    msg = "unterminated literal: single quote"
                    raise ScanError(msg)

            elif state == PP1State.DOUBLE_QUOTED:

                output += char
                if char == '"':
                    if not prev_char == "\\" or prev_char_count % 2 == 0:
                        state = PP1State.NORMAL_CODE
                        token_range = PP1TokenRange(
                            kind = PP1TokenKind.DOUBLE_QUOTED,
                            beg_indx=double_quoted_begindx,
                            end_indx=len(output),
                        )
                        token_ranges.append(token_range)
                elif char == "\n":
                    msg = "unterminated literal: double quote"
                    raise ScanError(msg)

            elif state == PP1State.CPP_COMMENT:

                if char == "\n":
                    output += " "  # single space
                    output += char  # keep newline
                    state = PP1State.NORMAL_CODE

            elif state == PP1State.C_COMMENT:

                if char == "*":
                    state = PP1State.C_COMMENT_ASTERISK

            elif state == PP1State.C_COMMENT_ASTERISK:

                if char == "/":
                    output += " "  # single space
                    state = PP1State.NORMAL_CODE
                elif char == "*":
                    state = PP1State.C_COMMENT_ASTERISK
                else:
                    state = PP1State.C_COMMENT

            else:

                msg = f"Internal Error: {state!r}"
                raise ScanError(msg)

            if char != prev_char:
                prev_char = char
                prev_char_count = 1
            else:
                prev_char_count += 1

            if char == "\n" and state != PP1State.C_COMMENT:
                token_range = PP1TokenRange(
                    kind = PP1TokenKind.EOL,
                    beg_indx=len(output) - 1,
                    end_indx=len(output),
                )
                token_ranges.append(token_range)
                if output[token_range.beg_indx: token_range.end_indx] != "\n":
                    msg = f"Internal Error: expected newline, found={output[token_range.beg_indx: token_range.end_indx]!r}"
                    raise ScanError(msg)

        if state == PP1State.C_COMMENT:
            msg = "unterminated comment"
            raise ScanError(msg)

        if output and output[-1] != "\n":
            msg = "missing EOL at end of file"
            raise ScanError(msg)

        token_range = PP1TokenRange(
            kind = PP1TokenKind.EOF,
            beg_indx=len(output),
            end_indx=len(output),
        )
        token_ranges.append(token_range)

        if _VERBOSE:
            print(f"{self.__class__.__name__}:output:beg\n{'-' * 25}")
            print(output)
            print(f"{'-' * 25}\n{self.__class__.__name__}:output:end")

        return output, token_ranges

    def transform_token_ranges(self, output, token_ranges):

        # build token list
        token_list = []
        lo_indx = 0
        for token_range in token_ranges:
            nchars = token_range.beg_indx - lo_indx
            if _DISPLAY:
                print("indices 1", token_range.beg_indx, lo_indx, nchars)
            if nchars > 0:
                hi_indx = lo_indx + nchars
                token = PP1TokenText(
                    kind=PP1TokenKind.CHUNK,
                    text=output[lo_indx:hi_indx]
                )
                token_list.append(token)
            if _DISPLAY:
                print("token", repr(output[lo_indx:hi_indx]))
            nchars = token_range.end_indx - token_range.beg_indx
            if _DISPLAY:
                print("indices 2", token_range.end_indx, token_range.beg_indx, nchars)
            if nchars > 0:
                token = PP1TokenText(
                    kind=token_range.kind,
                    text=output[token_range.beg_indx:token_range.end_indx]
                )
                token_list.append(token)
            if _DISPLAY:
                print("token", repr(output[token_range.beg_indx:token_range.end_indx]))
            lo_indx = token_range.end_indx

        # filter out empty lines
        lines = []
        line_tokens = deque()
        for token in token_list:
            if token.kind != PP1TokenKind.EOL:
                line_tokens.append(token)
            elif line_tokens:
                lines.append(line_tokens)
                line_tokens = deque()

        pass2_lines = []
        for line_tokens in lines:

            one_token = bool(len(line_tokens) == 1)

            if _DISPLAY:
                print(line_tokens)

            first_token = line_tokens.popleft()

            m = self.re_directive.match(first_token.text)
            if not m:
                if _DISPLAY:
                    print("NOT A DIRECTIVE", repr(first_token.text))
                continue

            directive = m.group("directive")
            chunk = m.group("chunk")

            if one_token:
                chunk = chunk.strip()
            else:
                chunk = chunk.lstrip()

            # TODO(JCB): eats single space
            if chunk:
                chunk = " " + chunk # single space
                chunk_token = PP1TokenText(kind=first_token.kind, text=chunk)
                line_tokens.appendleft(chunk_token)

            directive_token = PP1TokenText(kind=PP1TokenKind.DIRECTIVE, text=directive)
            line_tokens.appendleft(directive_token)

            if not one_token:
                # TODO(JCB): find reference for whitespace handling
                last_token = line_tokens.pop()
                last_content = last_token.text.rstrip()
                if last_content:
                    if last_content != last_token.text:
                        last_token = PP1TokenText(kind=last_token.kind, text=last_content)
                    line_tokens.append(last_token)
                else:
                    # TODO(JCB): trailing whitespace (keep single space?)
                    pass

            pass2_lines.append(line_tokens)

        return pass2_lines

    def process_text(self, text):
        text = self.transform_endoflines(text)
        text, _ = self.transform_comments(text)
        return text

    def process_file(self, file):
        text = self.read_file(file)
        text = self.transform_endoflines(text)
        text, token_ranges = self.transform_comments(text)
        lines = self.transform_token_ranges(text, token_ranges)
        if _DISPLAY:
            print("DIRECTIVE LINES:")
            for indx, line_tokens in enumerate(lines):
                print(f"    Directive[{indx}] Tokens:")
                for token in line_tokens:
                    print(f"        {token!r}")
            print("\nSCONS COMPATIBLE LINES:")
            for indx, line_tokens in enumerate(lines):
                content = "|#" + "".join([token.text for token in line_tokens]) + "|"
                print(f"    Directive[{indx}]: {content}")
        return lines

_PREPROCESSOR = _PreProcessor()

preprocess_sourcefile = _PREPROCESSOR.process_file
preprocess_text = _PREPROCESSOR.process_text

