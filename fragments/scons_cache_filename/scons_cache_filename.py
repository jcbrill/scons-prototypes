import os
import os.path
from pathlib import Path
import json
import sys
import warnings

class SConsWarning(Warning):
    pass

class SCons:

    class Warnings:

        def warn(kind, msg):
            #e = kind(msg)
            print('%s: %s' % (kind.__name__, msg), file=sys.stderr)

def debug_on(message, *args):
    if args:
        print(message % args)
    else:
        print(message)

def debug_off(message, *args):
    pass

# there is a debug call during file initialization before main runs
debug = debug_off

def _set_debug(debugging):
    global debug
    debug = debug_on if debugging else debug_off


### BEGIN SCONS COMPATIBLE CODE ###

class FileNameWarning(SConsWarning):
    pass

_CACHE_FILENAME_DOUBLEQUOTES_ALLOWED = True

_CACHE_FILENAME_DEFAULT = '.scons_msvc_cache.json'

def _config_cache_filename_helper(cache_config):

    # A non-None return value does not mean that the file can be succesfully opened
    # as the user-defined request may contain characters that are illegal in a windows
    # path and/or filename, the destination may not be readable and/or writable (permissions,
    # read-only, etc.).  It simply means there is a candidate file name to attempt to
    # open for reading and writing.

    cache_intended = False
    cache_filename = None

    debug('cache_config=%s [input]', repr(cache_config))

    if cache_config:

        # at most two passes to strip leading spaces and/or double quotes
        for n in range(2):

            # save starting string
            cache_orig = cache_config

            # remove leading/trailing spaces
            cache_config = cache_config.strip()
            if not cache_config:
                break

            # exit loop if double quotes not supported
            if not _CACHE_FILENAME_DOUBLEQUOTES_ALLOWED:
                break

            # remove leading/trailing double quotes
            cache_config = cache_config.strip('"')
            if not cache_config:
                break

            # exit loop if string didn't change
            if cache_config == cache_orig:
                break

    if not cache_config:
        debug('cache_config=%s [undefined], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return cache_intended, cache_filename

    cache_intended = True

    # check if cache configuration is a recognized boolean symbol
    symbol = cache_config.lower()

    if symbol in ('1', 'true'):
        # cache enabled via boolean value: use default path and filename
        cache_filename = os.path.join(os.path.expanduser('~'), _CACHE_FILENAME_DEFAULT)
        debug('cache_config=%s [boolean true], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return cache_intended, cache_filename

    if symbol in ('0', 'false'):
        # cache disabled via boolean value: prevent creating 0 or False cache filename
        debug('cache_config=%s [boolean false], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return False, cache_filename

    # process path: resolve home path and symlinks (necessary?)
    cache_config = os.path.expanduser(cache_config)
    cache_config = os.path.realpath(cache_config)

    if os.path.exists(cache_config):
        # existing directory or file

        if os.path.isfile(cache_config):
            # existing filename
            cache_filename = cache_config
            debug('cache_config=%s [file exists], cache_filename=%s', repr(cache_config), repr(cache_filename))
            return cache_intended, cache_filename

        # existing path: use default filename
        cache_filename = os.path.join(cache_config, _CACHE_FILENAME_DEFAULT)
        debug('cache_config=%s [path exists], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return cache_intended, cache_filename

    # specified directory or file does not exist
    head, tail = os.path.split(cache_config)

    if tail:
        # use tail as filename

        if head and not os.path.exists(head):
            # head does not exist: missing path components
            debug('cache_config=%s [head invalid=%s, tail=%s], cache_filename=%s', repr(cache_config), repr(head), repr(tail), repr(cache_filename))
            return cache_intended, cache_filename

        # head (undefined or exists)
        cache_filename = cache_config
        debug('cache_config=%s [head valid=%s, tail=%s], cache_filename=%s', repr(cache_config), repr(head), repr(tail), repr(cache_filename))
        return cache_intended, cache_filename

    # head defined and tail not defined: directory that does not exist
    debug('cache_config=%s [head invalid=%s, tail=%s], cache_filename=%s', repr(cache_config), repr(head), repr(tail), repr(cache_filename))
    return cache_intended, cache_filename

def _config_cache_filename(cache_config):

    cache_intended, cache_filename = _config_cache_filename_helper(cache_config)

    if cache_filename:

        try:
            p = Path(cache_filename)
            p.is_file()
        except OSError as e:
            if e.errno in (22,):
                # Errno 22:
                #    OSError: [Errno 22] Invalid argument
                #    OSError: [WinError 123] The filename, directory name, or volume label syntax is incorrect
                cache_filename = None
            else:
                debug('config cache filename:%s exception (errno=%s), cache_filename: %s', type(e).__name__, e.errno, repr(cache_filename))

    if cache_intended and not cache_filename:
        SCons.Warnings.warn(FileNameWarning, 'SCONS_CACHE_MSVC_CONFIG file name is not valid: %s' % repr(cache_config))

    return cache_filename

CONFIG_CACHE = _config_cache_filename(os.environ.get('SCONS_CACHE_MSVC_CONFIG'))


def read_script_env_cache():
    """ fetch cached msvc env vars if requested, else return empty dict """
    envcache = {}
    if CONFIG_CACHE:
        try:
            p = Path(CONFIG_CACHE)
            with p.open('r') as f:
                envcache = json.load(f)
        except FileNotFoundError:
            # don't fail if no cache file, just proceed without it
            pass
    return envcache


def write_script_env_cache(cache):
    """ write out cache of msvc env vars if requested """
    if CONFIG_CACHE:
        try:
            p = Path(CONFIG_CACHE)
            with p.open('w') as f:
                json.dump(cache, f, indent=2)
        except TypeError:
            # data can't serialize to json, don't leave partial file
            with suppress(FileNotFoundError):
                p.unlink()
        except IOError as e:
            # can't write the file, just skip
            debug('write cache:%s exception (errno=%s), cache_filename=%s', type(e).__name__, e.errno, repr(CONFIG_CACHE))

### END SCONS COMPATIBLE CODE ###

def test_config_cache_filename():
    global CONFIG_CACHE

    unhandled_exceptions = 0

    print("test_config_cache_filename:")

    indent = ' ' * 4
    for cache_config in [

        os.environ.get('SCONS_CACHE_MSVC_CONFIG'),

        '~', # use default file name
        '~\\scons_msvc_cache.json', # use specified file name
        '~\\.mycachefile', # use specified file name
        '~\\folderdoesnotexist\\.mycachefile', # head does not exist

        None, '', '  "  "  ',

        '|*<>', # cache file is an illegal filename
        '~\\|*<>', # cache file is an illegal filename
        'C:\\Windows\\Temp\\|*<>', # cache file is an illegal filename

        '1', 'True',  'true',  'TRUE',  '"1"', ' "True" ',  ' " TRUE " ',  # enabled via boolean symbol
        '0', 'False', 'false', 'FALSE', '"0"', ' "False" ', ' " False " ', # disabled via boolean symbol

        os.path.expanduser('~'),
        os.path.join(os.path.join(os.path.expanduser('~'), _CACHE_FILENAME_DEFAULT)),

        '.',
        '..\\..\\..\\..\\..', # this works even though too many directories (abspath reports root)

        '.\\.mycachefile', '.\\mycachefile', # head exists, tail defined: cache file
        '.\\mycachefile.txt', # head exists, tail defined: cache file

        '.\\folderdoesnotexist\\subdir\\', # head does not exist, tail undefined
        '.\\folderdoesnotexist\\subdir', # head does not exist, tail defined
        'L:\\', # head does not exist, tail undefined - invalid local drive
        'filedoesnotexist', # head does not exist, tail defined: cache_filename

        '"  ' + r'C:\Windows\Temp\Temp' + '  "',      # C:\Windows\Temp\Temp folder does not exist, cache filename = C:\Windows\Temp\Temp
        '  "  ' + r'C:\Windows\Temp\Temp' + '  "  ',  # C:\Windows\Temp\Temp folder does not exist, cache filename = C:\Windows\Temp\Temp
        '"  ' + r'C:\Windows\Temp' + '  "',           # C:\Windows\Temp folder exists, cache filename = C:\Windows\Temp\.scons_msvc_cache.json
        '  "  ' + r'C:\Windows\Temp' + '  "  ',       # C:\Windows\Temp folder exists, cache filename = C:\Windows\Temp\.scons_msvc_cache.json

    ]:

        inpval = cache_config
        print("\n{}INPUT: {}".format(indent, repr(inpval)))

        outval = _config_cache_filename(inpval)
        print("{}OUTPUT: {}".format(indent, repr(outval)))

        if not outval:
            continue

        # overwrite for testing
        CONFIG_CACHE = outval

        try:
            envcache = read_script_env_cache()
        except Exception as e:
            print("unhandled exception:", str(e))
            unhandled_exceptions += 1

    if unhandled_exceptions:
        raise RuntimeError('%d unhandled exceptions' % unhandled_exceptions)

if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()

    debug_group = parser.add_mutually_exclusive_group()
    debug_group.add_argument('--debug', action='store_const', dest='debugging', const=True, help='display debugging messages')
    debug_group.add_argument('--nodebug', action='store_const', dest='debugging', const=False, help='suppress debugging messages')

    parser.set_defaults(debugging=True)

    args = parser.parse_args()

    _set_debug(args.debugging)

    test_config_cache_filename()

