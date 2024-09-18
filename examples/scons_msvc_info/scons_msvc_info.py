import json
import os
import re
import subprocess
from collections import namedtuple

class _Util:

    @classmethod
    def normalize_path(cls, p):
        p = os.path.normpath(p)
        p = os.path.normcase(p)
        return p

    @classmethod
    def _decode_cmd_output(cls, buffer, encoding):
        if not buffer:
            return ""
        try:
            return buffer.decode(encoding, errors="strict")
        except UnicodeDecodeError as e:
            pass
        except Exception as e:
            raise
        return buffer.decode(encoding, errors="replace")

    @classmethod
    def subprocess_run(cls, cmd, env=None, encoding=None, check=False, shell=False):

        if env is None:
            env = os.environ

        if encoding is None:
            encoding = "oem"

        cp = subprocess.run(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
            shell=shell,
        )

        retcode = cp.returncode

        outstr = cls._decode_cmd_output(cp.stdout, encoding) if cp.stdout else ""
        errstr = cls._decode_cmd_output(cp.stderr, encoding) if cp.stderr else ""

        return outstr, errstr, retcode

    @classmethod
    def system_paths(cls, env):
        rval = []
        if not env:
            return rval
        env_ENV = env.get("ENV")
        if not env_ENV:
            return rval
        syspaths = env_ENV.get("PATH", "")
        if not syspaths:
            return rval
        rval.extend(syspaths.split(os.pathsep))
        return rval

    @classmethod
    def system_pathexts(cls, env):
        rval = []
        if not env:
            return rval
        env_ENV = env.get("ENV")
        if not env_ENV:
            return rval
        syspathexts = env_ENV.get("PATHEXT", "")
        if not syspathexts:
            return rval
        rval.extend(syspathexts.split(os.pathsep))
        return rval

    @classmethod
    def find_program(cls, env, program_or_list):
        rval = None
        if not program_or_list:
            return rval
        sys_paths = cls.system_paths(env)
        if not sys_paths:
            return rval
        # program name list
        if isinstance(program_or_list, str):
            program_list = [program_or_list]
        else:
            program_list = program_or_list
        # (basename, ext_list) list
        sys_pathexts = None
        search_list = []
        for program in program_list:
            _, tail = os.path.split(program)
            basename, ext = os.path.splitext(tail)
            if ext:
                ext_list = [ext]
            else:
                if sys_pathexts is None:
                    sys_pathexts = cls.system_pathexts(env)
                ext_list = sys_pathexts
                if not ext_list:
                    continue
            search_list.append((basename, ext_list))
        # search (basename, ext_list)
        for sys_path in sys_paths:
            for basename, ext_list in search_list:
                for ext in ext_list:
                    filename = basename + ext
                    candidate = os.path.join(sys_path, filename)
                    if os.path.exists(candidate):
                        return candidate
        return rval

class VSWhere:

    vswhere_once = False
    vswhere_json = {}

    vsroots = []
    vsroots_regex = None

    vsroot_instance = {}

    @classmethod
    def _process_json(cls):
        if cls.vswhere_json:
            for instance in cls.vswhere_json:
                installation_path = instance.get("installationPath")
                if not installation_path or not os.path.exists(installation_path):
                    continue
                vs_root = _Util.normalize_path(installation_path)
                cls.vsroots.append(vs_root)
                cls.vsroot_instance[vs_root] = instance
            # vsroots: longest to shortest (i.e., longest match first)
            vsroots = sorted(cls.vsroots, key=len)
            vsroots.reverse()
            vsroots = "|".join([re.escape(vsroot) for vsroot in vsroots])
            cls.vsroots_regex = re.compile(f"^(?P<vsroot>(?:{vsroots}))", re.IGNORECASE)

    @classmethod
    def _query_env(cls, env, known_executable=False):
        rval = {}
        if not cls.vsroots:
            return rval
        sys_paths = _Util.system_paths(env)
        if not sys_paths:
            return rval
        if known_executable:
            known_path = None
            for sys_path in sys_paths:
                candidate = os.path.join(sys_path, "errlook.exe")
                if os.path.exists(candidate):
                    known_path = sys_path
                    break
            if known_path:
                sys_paths.insert(0, known_path)
        instance = None
        instance_path = None
        for sys_path in sys_paths:
            m = cls.vsroots_regex.match(sys_path)
            if not m:
                continue
            vs_path = m.group("vsroot")
            vs_root = _Util.normalize_path(vs_path)
            instance = cls.vsroot_instance[vs_root]
            instance_path = sys_path
            break
        if not instance:
            return rval
        rval["ENV_path"] = instance_path
        catalog = instance.get("catalog", {})
        for key, mapping in [
            ("installationPath", instance),
            ("installationVersion", instance),
            ("displayName", instance),
            ("productId", instance),
            ("productPath", instance),
            ("buildVersion", catalog),
            ("productDisplayVersion", catalog),
            ("productSemanticVersion", catalog),
        ]:
            rval[key] = mapping.get(key, "")
        return rval

    @classmethod
    def _vswhere_setup(cls, vswhere_exe):
        # DO NOT add -legacy option:
        # * limited information
        # * adds VS2015 roots which can be a problem when v140 toolset compiler path is first
        # * if legacy option is added: change known_executable=True in _query_env call below
        vswhere_cmd = [vswhere_exe, "-all", "-products", "*", "-prerelease", "-format", "json", "-utf8"]
        try:
            stdout, _, _ = _Util.subprocess_run(vswhere_cmd, env=None, encoding="utf-8")
        except OSError as e:
            return
        except Exception as e:
            raise
        if not stdout:
            return
        try:
            vswhere_json = json.loads(stdout)
        except json.decoder.JSONDecodeError:
            return
        cls.vswhere_json = vswhere_json
        cls._process_json()

    @classmethod
    def vswhere_info_env(cls, env):
        if not cls.vswhere_once:
            cls.vswhere_once = True
            vswhere_exe = env.subst("$VSWHERE")
            if vswhere_exe and os.path.exists(vswhere_exe):
                cls._vswhere_setup(vswhere_exe)
        rval = cls._query_env(env, known_executable=False)
        return rval

class _Programs:

    # MSVS 2005+:    XX.YY.ZZZZZ(.N+)?
    # MSVS 6.0-2003: XX.YY.ZZZZ

    # token starts with cl version number
    _cl_version_number = re.compile(r"^([0-9]{2}[.][0-9]{2}[.][0-9]{4,}(?:[.][0-9]+)?)")

    # extract toolset version from cl_exe path
    _cl_toolset_version_number = re.compile(r"MSVC\\([0-9]{2,}[.][0-9]{2,}[.][0-9]{5,})\\bin", re.IGNORECASE)

    _VC_VERSIONS_NT = namedtuple("_VC_VERSIONS_NT", [
        "vc_buildseries",
        "vc_buildtools",
        "vs_version",
        "unique",
    ])

    _cl_version_prefix_map = {
        # clver (buildseries, buildtools, vsver, unique)
        "19.4": _VC_VERSIONS_NT("14.4", "14.3", "17.0", False),  # 2022
        "19.3": _VC_VERSIONS_NT("14.3", "14.3", "17.0", False),  # 2022
        "19.2": _VC_VERSIONS_NT("14.2", "14.2", "16.0", False),  # 2019
        "19.1": _VC_VERSIONS_NT("14.1", "14.1", "15.0", False),  # 2017
        "19.0": _VC_VERSIONS_NT("14.0", "14.0", "14.0", False),  # 2015
        "18.0": _VC_VERSIONS_NT("12.0", "12.0", "12.0", True),  # 2013
        "17.0": _VC_VERSIONS_NT("11.0", "11.0", "11.0", True),  # 2012
        "16.0": _VC_VERSIONS_NT("10.0", "10.0", "10.0", True),  # 2010
        "15.0": _VC_VERSIONS_NT("9.0", "9.0", "9.0", True),  # 2008
        "14.0": _VC_VERSIONS_NT("8.0", "8.0", "8.0", True),  # 2005
        "13.1": _VC_VERSIONS_NT("7.1", "7.1", "7.1", True),  # 2003
        "13.0": _VC_VERSIONS_NT("7.0", "7.0", "7.0", True),  # 2002
        "12.0": _VC_VERSIONS_NT("6.0", "6.0", "6.0", True),  # 1998
    }

    # cl version
    _vc_buildseries_map = {}

    # vc legacy version (not worth the effort)
    _vs_version_major_map = {}

    _seen_vcbuildtools_vsversion = set()
    for temp_nt in _cl_version_prefix_map.values():
        _vc_buildseries_map[temp_nt.vc_buildseries] = temp_nt
        # vc legacy version
        key = (temp_nt.vc_buildtools, temp_nt.vs_version)
        if key not in _seen_vcbuildtools_vsversion:
            vs_major, _ = temp_nt.vs_version.split(".")
            _vs_version_major_map.setdefault(vs_major, []).append(key)
            _seen_vcbuildtools_vsversion.add(key)

    dev_executables = ["devenv.com", "msdev.com"]
    exp_executables = ["wdexpress.exe", "vcexpress.exe"]
    all_executables = dev_executables + exp_executables

    @classmethod
    def _version_prefix(cls, version):
        version_comps = version.split('.')
        if len(version_comps) < 2:
            return ""
        version_prefix = ".".join([version_comps[0], version_comps[1][0]])
        return version_prefix

    @classmethod
    def vs_version_buildtools(cls, vs_version):
        vc_buildtools = None
        version_prefix = cls._version_prefix(vs_version)
        vs_major, _ = version_prefix.split('.')
        vcbuildtools_vsversion_list = cls._vs_version_major_map.get(vs_major)
        if vcbuildtools_vsversion_list:
            if len(vcbuildtools_vsversion_list) == 1:
                vc_buildtools, _ = vcbuildtools_vsversion_list[0]
            else:
                for tmp_vc_buildtools, tmp_vs_version in vcbuildtools_vsversion_list:
                    if tmp_vs_version == version_prefix:
                        vc_buildtools = tmp_vc_buildtools
                        break
        return vc_buildtools

    @classmethod
    def cl_info_env(cls, env):
        rval = {}
        cl_path = _Util.find_program(env, "cl")
        if not cl_path:
            return rval
        _, errstr, _ = _Util.subprocess_run([cl_path], env=env["ENV"])
        if not errstr:
            return rval
        cl_version = None
        errline = errstr.splitlines()[0]
        for token in errline.split(' '):
            m = cls._cl_version_number.match(token)
            if m:
                cl_version = token
                break
        if not cl_version:
            return rval
        vc_toolset = ""
        vc_buildseries = ""
        vc_buildtools = ""
        vs_version = ""
        vs_version_provisional = ""
        # process cl_version
        cl_version_prefix = cls._version_prefix(cl_version)
        if cl_version_prefix:
            versions_nt = cls._cl_version_prefix_map.get(cl_version_prefix)
            if versions_nt:
                vs_version_provisional = versions_nt.vs_version
                if versions_nt.unique:
                    vs_version = vs_version_provisional
                vc_toolset = versions_nt.vc_buildseries
                vc_buildseries = versions_nt.vc_buildseries
                vc_buildtools = versions_nt.vc_buildtools
        # process cl_path
        m = cls._cl_toolset_version_number.search(cl_path)
        if not m:
           vs_version = vs_version_provisional
        else:
            vc_toolset = m.group(1)
            vc_toolset_prefix = cls._version_prefix(vc_toolset)
            if vc_toolset_prefix:
                vc_buildseries = vc_toolset_prefix
                if vc_buildseries in cls._vc_buildseries_map:
                    vc_buildtools = cls._vc_buildseries_map[vc_buildseries].vc_buildtools
        # results
        rval = {
            "cl_path": cl_path,
            "cl_version": cl_version,
            "vc_toolset": vc_toolset,
            "vc_buildseries": vc_buildseries,
            "vc_buildtools": vc_buildtools,
            "vs_version": vs_version,
        }
        return rval

    @classmethod
    def msbuild_info_env(cls, env):
        rval = {}
        msbuild_path = _Util.find_program(env, "msbuild.exe")
        if not msbuild_path:
            return rval
        try:
            outstr, _, _ = _Util.subprocess_run([msbuild_path, "/nologo", "/version"], env=env["ENV"])
        except OSError:
            # VS2022 BT on 32-bit Windows attempt to run 64-bit msbuild.exe
            outstr = ""
        outstr = outstr.strip()
        if not outstr:
            return rval
        rval["msbuild_path"] = msbuild_path
        rval["msbuild_version"] = outstr
        return rval

    @classmethod
    def dev_info_env(cls, env):
        rval = {}
        dev_path = _Util.find_program(env, cls.all_executables)
        if not dev_path:
            return rval
        _, executable = os.path.split(dev_path)
        executable = executable.lower()
        rval["dev_path"] = dev_path
        rval["dev_isdevelop"] = bool(executable in cls.dev_executables)
        rval["dev_isexpress"] = bool(executable in cls.exp_executables)
        return rval

class _Versions:

    _MSVC_INFO_NT = namedtuple("_MSVC_INFO_NT", [
        "version_info",
        "vswhere_info",
        "cl_info",
        "msbuild_info",
        "dev_info",
        "scons_info",
    ])

    @classmethod
    def _vs_version(cls, env_info, vswhere_info, cl_info):
        # vs batch file VSCMD_VER
        vs_version = vswhere_info.get("productSemanticVersion", "")
        if vs_version:
            vs_version = vs_version.split("+")[0]
            return vs_version
        vs_version = vswhere_info.get("installationVersion", "")
        if vs_version:
            return vs_version
        vs_version = cl_info.get("vs_version", "")
        if vs_version:
            return vs_version
        return ""

    @classmethod
    def _version_info(cls, env_info, vswhere_info, cl_info, msbuild_info, dev_info):

        vc_legacy = ""
        vs_version = cls._vs_version(env_info, vswhere_info, cl_info)
        vc_buildtools = cl_info.get("vc_buildtools", "")

        if not vc_legacy:
            vs_buildtools = _Programs.vs_version_buildtools(vs_version)
            if vs_buildtools:
                vc_legacy = vs_buildtools

        if not vc_legacy:
            if vc_buildtools:
                vc_legacy = vc_buildtools

        if vc_legacy:
            if dev_info.get("dev_isexpress", False):
                vc_legacy += "Exp"

        rval = {}
        rval["VS_VERSION"] = vs_version
        rval["VC_TOOLSET"] = cl_info.get("vc_toolset", "")
        rval["VC_BUILDSERIES"] = cl_info.get("vc_buildseries", "")
        rval["VC_BUILDTOOLS"] = vc_buildtools
        rval["VC_LEGACY"] = vc_legacy
        rval["CL_VERSION"] = cl_info.get("cl_version", "")
        rval["MSBUILD_VERSION"] = msbuild_info.get("msbuild_version", "")
        return rval

    @classmethod
    def msvc_info_env(cls, env):

        scons_info = {"MSVC_VERSION": env["MSVC_VERSION"]}
        vswhere_info = VSWhere.vswhere_info_env(env)
        cl_info = _Programs.cl_info_env(env)
        msbuild_info = _Programs.msbuild_info_env(env)
        dev_info = _Programs.dev_info_env(env)

        version_info = cls._version_info(scons_info, vswhere_info, cl_info, msbuild_info, dev_info)

        msvc_info = cls._MSVC_INFO_NT(
            version_info=version_info,
            vswhere_info=vswhere_info,
            cl_info=cl_info,
            msbuild_info=msbuild_info,
            dev_info=dev_info,
            scons_info=scons_info,
        )

        return msvc_info

def msvc_info_env(env):
    rval = None
    if env and "MSVC_VERSION" in env:
        rval = _Versions.msvc_info_env(env)
    return rval
