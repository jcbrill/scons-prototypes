import os
import re
from typing import Optional, Tuple

import SCons.Warnings  # type: ignore[import-not-found, import-untyped]

class WindowsFileNameWarning(SCons.Warnings.WarningOnByDefault):
    pass

class _WindowsFileName:

    # Known Issues:
    # * NTFS filenames with a colon are reported as invalid (false positive)
    #   given a file named "colonbeg:colonend.txt":
    #     * file "colonbeg" is created and appears empty
    #     * hidden alternate data stream file "colonbeg:colonend.txt:$DATA" is created
    #     * use "dir /R colonbeg" to display alternate data streams of files

    drive_prefix = r"([a-zA-Z][:])[\\]?(?P<suffix>.*)$"
    re_drive_spec = re.compile(drive_prefix)

    unc_prefix = r"(\\\\[^\\]+)[\\](?P<suffix>.*)$"
    re_unc_spec = re.compile(unc_prefix)

    re_illegal_chars = re.compile(
        r'[<>:"/\\|?*\r\t\n]',
        re.IGNORECASE
    )

    re_reserved_names = re.compile(
        r"^(?P<reserved>CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)",
        re.IGNORECASE,
    )

    @classmethod
    def is_filename_invalid(cls, fileorig: str) -> Tuple[str, str]:

        filename = fileorig
        if not filename:
            reason = "file name is empty"
            return reason, filename

        filename = os.fspath(filename)
        filename = os.path.abspath(filename)

        pathspec, filespec = os.path.split(filename)

        if filespec and not filespec.strip():
            reason = f"file name is whitespace only: {filespec!r}"
            return reason, filename

        suffix = ""

        do_once = True
        while do_once:
            do_once = False

            m = cls.re_drive_spec.match(filename)
            if m:
                # filename: r"c:\dir\filename.txt"
                #   prefix: r"c:"
                #   suffix: r"dir\filename.txt"
                suffix = m.group("suffix")
                break

            m = cls.re_unc_spec.match(filename)
            if m:
                # filename: r"\\server\share\filename.txt"
                #   prefix: r"\\server"
                #   suffix: r"share\filename.txt"
                suffix = m.group("suffix")
                break

            reason = "unrecognized path prefix"
            return reason, filename

        if suffix:

            comps = suffix.split(os.path.sep)
            for name in comps:

                if not name:
                    reason = "file name component is empty"
                    return reason, filename

                if name and not name.strip():
                    reason = f"file name component is whitespace-only ({name!r})"
                    return reason, filename

                illegal_chars = cls.re_illegal_chars.findall(name)
                if illegal_chars:
                    seen_chars = ', '.join(list(
                        {repr(s): s for s in illegal_chars}.keys()
                    ))
                    reason = f"file name contains illegal characters ({seen_chars})"
                    return reason, filename

                match = cls.re_reserved_names.match(name)
                if match:
                    reserved = match.group("reserved")
                    reason = f"file name contains a reserved name ({reserved!r})"
                    return reason, filename

        if not os.path.exists(pathspec):
            reason = "path to file name does not exist"
            return reason, filename

        if os.path.exists(filename) and os.path.isdir(filename):
            reason = "file name is a directory"
            return reason, filename

        return "", filename

    @classmethod
    def check_filename_invalid(
        cls,
        filename: str,
        description: Optional[str] = None
    ) -> bool:
        reason, abspath = cls.is_filename_invalid(filename)
        if reason:
            if description:
                msg_description = description + " "
            else:
                msg_description = ""
            msg = (
                f"{msg_description}file name is invalid:\n"
                f"  filename: {filename!r}\n"
                f"   abspath: {abspath!r}\n"
                f"    reason: {reason}"
            )
            SCons.Warnings.warn(WindowsFileNameWarning, msg)
        return bool(reason)

    @classmethod
    def process_filename(
        cls,
        filename: Optional[str],
        description: Optional[str] = None
    ) -> Optional[str]:
        if filename is None:
            return filename
        if len(filename) < 2:
            return filename
        if filename[0] == '"' and filename[-1] == '"':
            fileorig = filename
            filename = filename[1:-1]
            if description:
                msg_description = description + " "
            else:
                msg_description = ""
            msg = (
                f"{msg_description}file name is invalid:\n"
                f"  filename: {fileorig!r}\n"
                f"  modified: {filename!r}\n"
                f"    action: leading and trailing double quotes removed"
            )
            SCons.Warnings.warn(WindowsFileNameWarning, msg)
        return filename

    @classmethod
    def get_filename_environ(
        cls,
        evar: str,
    ) -> Optional[str]:
        filename = cls.process_filename(os.environ.get(evar), description=evar)
        return filename

check_filename_invalid = _WindowsFileName.check_filename_invalid
get_filename_environ = _WindowsFileName.get_filename_environ
