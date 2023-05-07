import os
import subprocess
import json
import re
import textwrap

### Hard-coded paths: adapt as necessary 

COMSPEC = r'C:\Windows\system32\cmd.exe'
POWERSHELL = r'C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe'
WHERE = r'C:\Windows\system32\where.exe'

for MSVC_BATCH in [
    # VS2022 Community default location
    r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat',
    # VS2022 BuildTools default location
    r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat',
    # VS2022 Preview default location
    r'C:\Program Files\Microsoft Visual Studio\2022\Preview\VC\Auxiliary\Build\vcvarsall.bat',
    # VS2022 Community custom location
    r'c:\software\msvs-2022-143-com\vc\auxiliary\build\vcvarsall.bat',
    # VS2022 Preview custom location
    r'c:\software\msvs-2022-143-com-pre\vc\auxiliary\build\vcvarsall.bat',
 ]:
    if os.path.exists(MSVC_BATCH):
        break

# subprocess method:
#     run:   subprocess.run
#     popen: subprocess.Popen
#     all:   subprocess.run, subprocess.Popen
SUBPROCESS_METHOD = 'popen'

### Subprocess support

_WINDOWS_SUBPROCESS_RUN = False

_re_decode_byte_0x00 = re.compile('decode byte 0x00', re.IGNORECASE)

def _decode_cmd_output(buffer, encoding=None):

    if not buffer:
        # TODO: '' or buffer if buffer is not None else ''
        return '' if buffer is not None else None

    if encoding is None:
        encoding = json.detect_encoding(buffer)

    try:
        return buffer.decode(encoding, errors='strict')
    except UnicodeDecodeError as e:
        errmsg = str(e)
        # TODO: debug logging
    except Exception as e:
        errmsg = str(e)
        # TODO: debug logging
        raise

    if _re_decode_byte_0x00.search(errmsg):
        # batch echo to stderr and reg query error resulted in decoding error
        # "can't decode byte 0x00" (characters followed by nuls) when using /U
        # stripping nuls *may* result in utf-8 than can be properly decoded
        stripnul = buffer.replace(b'\x00', b'')
        encoding = json.detect_encoding(stripnul)
        try:
            return stripnul.decode(encoding, errors='strict')
        except UnicodeDecodeError as e:
            errmsg = str(e)
            # TODO: debug logging
        except Exception as e:
            errmsg = str(e)
            # TODO: debug logging
            raise
        # fallback to replacing errors on stripped buffer
        buffer = stripnul

    # TODO: !!! decoding errors !!!

    # fallback to replacing errors
    return buffer.decode(encoding, errors='replace')

def windows_subprocess_run(cmd, env=None, encoding=None):

    try:
        cp = subprocess.run(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except Exception as e:
        errmsg = str(e)
        # TODO: debug logging
        raise

    outstr = _decode_cmd_output(cp.stdout, encoding=encoding) if cp.stdout else ''
    errstr = _decode_cmd_output(cp.stderr, encoding=encoding) if cp.stderr else ''

    retcode = cp.returncode
    if retcode != 0:
        if errstr:
            errmsg = 'subprocess error (returncode = {}): {}'.format(retcode, errstr)
        else:
            errmsg = 'subprocess error (returncode = {})'.format(retcode)
        # TODO: exception type
        raise OSError(errmsg)

    return outstr, errstr

def windows_subprocess_popen(cmd, env=None, encoding=None):

    try:
        # pylint: disable=consider-using-with
        # TODO: rework using context manager?
        popen = subprocess.Popen(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except Exception as e:
        errmsg = str(e)
        # TODO: debug logging
        raise

    outraw = popen.stdout.read()
    outstr = _decode_cmd_output(outraw, encoding=encoding)

    errraw = popen.stderr.read()
    errstr = _decode_cmd_output(errraw, encoding=encoding)

    retcode = popen.wait()
    if retcode != 0:
        if errstr:
            errmsg = 'subprocess error (returncode = {}): {}'.format(retcode, errstr)
        else:
            errmsg = 'subprocess error (returncode = {})'.format(retcode)
        # TODO: exception type
        raise OSError(errmsg)

    return outstr, errstr

windows_subprocess = windows_subprocess_run if _WINDOWS_SUBPROCESS_RUN else windows_subprocess_popen

### Error checking 

subprocess_methods = {
    'run': [
        (windows_subprocess_run, 'subprocess.run'),    
    ],
    'popen': [
        (windows_subprocess_popen, 'subprocess.Popen'),
    ],
    'all': [
        (windows_subprocess_run, 'subprocess.run'),    
        (windows_subprocess_popen, 'subprocess.Popen'),
    ],
}

if not os.path.exists(COMSPEC):
    errmsg = f'COMSPEC path not found: {repr(COMSPEC)}'
    raise RuntimeError(errmsg)

if not os.path.exists(POWERSHELL):
    errmsg = f'POWERSHELL path not found: {repr(POWERSHELL)}'
    raise RuntimeError(errmsg)

if not os.path.exists(WHERE):
    errmsg = f'WHERE path not found: {repr(WHERE)}'
    raise RuntimeError(errmsg)

if not os.path.exists(MSVC_BATCH):
    errmsg = f'MSVC_BATCH path not found: {repr(MSVC_BATCH)}'
    raise RuntimeError(errmsg)

if SUBPROCESS_METHOD.lower() not in subprocess_methods:
    errmsg = f'SUBPROCESS_METHOD is not supported: {repr(SUBPROCESS_METHOD)}'
    raise RuntimeError(errmsg)

### Run test

def call_subprocess(cmd, env, test='Test', prefix='', subprocess_method=None):

    if subprocess_method is None:
        subprocess_method = windows_subprocess

    indent0 = prefix
    indent1 = prefix + ' '*4
    indent2 = prefix + ' '*8

    print()
    print(textwrap.indent(test, prefix=indent0))
    print(textwrap.indent('CONFIGURATION:', prefix=indent1))
    print(textwrap.indent("os.environ['COMSPEC'] = {}".format(os.environ.get('COMSPEC')), prefix=indent2))
    print(textwrap.indent("env['COMSPEC'] = {}".format(env.get('COMSPEC')), prefix=indent2))
    print(textwrap.indent("where.exe = {}".format(WHERE), prefix=indent2))
    print(textwrap.indent('COMMAND:', prefix=indent1))
    print(textwrap.indent(cmd, prefix=indent2))
    print(textwrap.indent('METHOD:', prefix=indent1))
    print(textwrap.indent(subprocess_method.__name__, prefix=indent2))

    try:
        outstr, errstr = subprocess_method(cmd, env)
    except OSError as e:
        excstr = str(e)
        outstr = ''
        errstr = ''
    else:
        excstr = ''
    
    print(textwrap.indent('STDOUT:', prefix=indent1))
    print(textwrap.indent(outstr, prefix=indent2))
    print(textwrap.indent('STDERR:', prefix=indent1))
    print(textwrap.indent(errstr, prefix=indent2))
    print(textwrap.indent('EXCSTR:', prefix=indent1))
    print(textwrap.indent(excstr, prefix=indent2))

### Run all tests

cmd = f'"{MSVC_BATCH}" amd64 & set COMSPEC & where cl.exe'

env = dict(os.environ)

count = 0
for subprocess_method, kind in subprocess_methods[SUBPROCESS_METHOD.lower()]:
    for os_comspec, env_comspec, label in [

        (None,       None,       'TEST {} {} (os=None, env=None):'),
        (None,       COMSPEC,    'TEST {} {} (os=None, env=cmd):'),
        (None,       POWERSHELL, 'TEST {} {} (os=None, env=ps):'),

        (COMSPEC,    None,       'TEST {} {} (os=cmd, env=None):'),
        (COMSPEC,    COMSPEC,    'TEST {} {} (os=cmd, env=cmd):'),
        (COMSPEC,    POWERSHELL, 'TEST {} {} (os=cmd, env=ps):'),

        (POWERSHELL, None,       'TEST {} {} (os=ps, env=None):'),
        (POWERSHELL, COMSPEC,    'TEST {} {} (os=ps, env=cmd):'),
        (POWERSHELL, POWERSHELL, 'TEST {} {} (os=ps, env=ps):'),

    ]:
        count += 1
        test = label.format(count, kind)
        if os_comspec:
            os.environ['COMSPEC'] = os_comspec
        elif 'COMSPEC' in os.environ:
            del os.environ['COMSPEC']
        if env_comspec:
            env['COMSPEC'] = env_comspec
        elif 'COMSPEC' in env:
            del env['COMSPEC']
        call_subprocess(cmd, env, test=test, subprocess_method=subprocess_method)
