import os
import os.path
import warnings

DEBUG = True

if DEBUG:
    def debug(message, *args):
        if args:
            print(message % args)
        else:
            print(message)
else:
    def debug(message, *args):
        pass

###

_CACHE_FILENAME_WARN_NOEXTENSION = False

_CACHE_FILENAME_DEFAULT = '.scons_msvc_cache.json'

def config_cache_filename(cache_config):

    # A non-None return value does not mean that the file can be succesfully opened
    # as the user-defined request may contain characters that are illegal in a windows
    # path and/or filename.  It simply means there is a candidate file name to attempt
    # to open.

    cache_filename = None

    if cache_config:

        # two passes at most to strip leading spaces and/or double quotes
        for n in range(2):

            # save starting string
            cache_orig = cache_config

            # remove leading/trailing spaces
            cache_config = cache_config.strip()
            if not cache_config:
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
        return cache_filename

    # check if cache configuration is a recognized boolean symbol
    symbol = cache_config.lower()

    if symbol in ('1', 'true'):
        # cache enabled via boolean value: use default path and filename
        cache_filename = os.path.join(os.path.expanduser('~'), _CACHE_FILENAME_DEFAULT)
        debug('cache_config=%s [boolean true], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return cache_filename

    if symbol in ('0', 'false'):
        # cache disabled via boolean value: prevent creating 0 or False cache filename
        debug('cache_config=%s [boolean false], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return cache_filename

    if os.path.exists(cache_config):
        # existing directory or file

        if os.path.isfile(cache_config):
            # existing filename
            cache_filename = cache_config
            debug('cache config=%s [file exists], cache_filename=%s', repr(cache_config), repr(cache_filename))
            return cache_filename

        # existing path: use default filename
        cache_filename = os.path.join(cache_config, _CACHE_FILENAME_DEFAULT)
        debug('cache config=%s [path exists], cache_filename=%s', repr(cache_config), repr(cache_filename))
        return cache_filename

    # specified directory or file does not exist
    head, tail = os.path.split(cache_config)

    if tail:
        # use tail as filename

        if _CACHE_FILENAME_WARN_NOEXTENSION:
            # warn if no extension: directory intended?
            _, ext = os.path.splitext(tail)
            if not ext:
                # NOT AN SCONS WARNING: need to change
                warnings.warn("cache file name does not have an extension {} ({})".format(repr(tail), repr(cache_config)))

        if head and not os.path.exists(head):
            # head does not exist: missing path components
            debug('cache config=%s [head invalid=%s, tail=%s], cache_filename=%s', repr(cache_config), repr(head), repr(tail), repr(cache_filename))
            return cache_filename

        # head (undefined or exists)
        cache_filename = cache_config
        debug('cache config=%s [head valid=%s, tail=%s], cache_filename=%s', repr(cache_config), repr(head), repr(tail), repr(cache_filename))
        return cache_filename

    # head defined and tail not defined: directory that does not exist
    debug('cache config=%s [head invalid=%s, tail=%s], cache_filename=%s', repr(cache_config), repr(head), repr(tail), repr(cache_filename))
    return cache_filename

CONFIG_CACHE = config_cache_filename(os.environ.get('SCONS_CACHE_MSVC_CONFIG'))

###

if __name__ == '__main__':

    for test_value in [

        None, '', '  "  "  ',

        '|*<>', # cache file is an illegal filename

        '1', 'True', 'true', 'TRUE', '"1"', ' "True" ', ' " TRUE " ',      # enabled via boolean symbol
        '0', 'False', 'false', 'FALSE', '"0"', ' "False" ', ' " False " ', # disabled via boolean symbol

        os.path.expanduser('~'),
        os.path.join(os.path.join(os.path.expanduser('~'), _CACHE_FILENAME_DEFAULT)),

        '.',
        '..\\..\\..\\..\\..', # this works even though too many directories (abspath reports root)

        '.\\.mycachefile', '.\\mycachefile', # head exists, tail defined: cache file (warning no extension) 
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
        print("")
        print("INPUT: {}".format(repr(test_value)))
        print("OUTPUT: {}".format(repr(config_cache_filename(test_value))))

