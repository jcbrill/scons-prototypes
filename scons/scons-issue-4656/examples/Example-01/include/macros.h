#ifndef MACROS_H
#define MACROS_H

    #if defined(_MSC_VER) && _MSVC_VER < 1400

        /* MSVC 7.1 [2003] and earlier */
        #define IS_ENABLED(config_macro) _IS_ENABLED1(config_macro,0)
        #define _IS_ENABLED1(val) _IS_ENABLED2(_XXXX ## val)
        #define _XXXX1 _YYYY,
        #define _IS_ENABLED2(one_or_two_args) _IS_ENABLED3((one_or_two_args 1, 0))
        #define _IS_ENABLED3(arglist) _IS_ENABLED4 arglist
        #define _IS_ENABLED4(ignore_this, val) val

    #elif defined(_MSC_VER)

        /* MSVC 8.0 [2005] and later */
        #define IS_ENABLED(config_macro,...) _IS_ENABLED1(config_macro)
        #define _IS_ENABLED1(...) _IS_ENABLED2(_XXXX ## __VA_ARGS__)
        #define _XXXX1 _YYYY,
        #define _IS_ENABLED2(one_or_two_args) _IS_ENABLED3((one_or_two_args 1, 0))
        #define _IS_ENABLED3(arglist) _IS_ENABLED4 arglist
        #define _IS_ENABLED4(ignore_this, val, ...) val

    #elif defined(__MINGW32__) || defined(__MINGW64__) || defined (__GNUC__) || defined(__GNUG__)

        /**
         * SCons issue 4656:
         *     comment: https://github.com/SCons/scons/issues/4656#issue-2694850829
         *     author: relfock
         */ 

        /**
         * @brief Macro for checking if the specified identifier is defined and it has
         *        a non-zero value.
         *
         * Normally, preprocessors treat all undefined identifiers as having the value
         * zero. However, some tools, like static code analyzers, can issue a warning
         * when such identifier is evaluated. This macro gives the possibility to suppress
         * such warnings only in places where this macro is used for evaluation, not in
         * the whole analyzed code.
         */
        #define IS_ENABLED(config_macro) _IS_ENABLED1(config_macro)
        /* IS_ENABLED() helpers */

        /* This is called from IS_ENABLED(), and sticks on a "_XXXX" prefix,
         * it will now be "_XXXX1" if config_macro is "1", or just "_XXXX" if it's
         * undefined.
         *   ENABLED:   IS_ENABLED2(_XXXX1)
         *   DISABLED   IS_ENABLED2(_XXXX)
         */
        #define _IS_ENABLED1(config_macro) _IS_ENABLED2(_XXXX##config_macro)

        /* Here's the core trick, we map "_XXXX1" to "_YYYY," (i.e. a string
         * with a trailing comma), so it has the effect of making this a
         * two-argument tuple to the preprocessor only in the case where the
         * value is defined to "1"
         *   ENABLED:    _YYYY,    <--- note comma!
         *   DISABLED:   _XXXX
         */
        #define _XXXX1 _YYYY,

        /* Then we append an extra argument to fool the gcc preprocessor into
         * accepting it as a varargs macro.
         *                         arg1   arg2  arg3
         *   ENABLED:   IS_ENABLED3(_YYYY,    1,    0)
         *   DISABLED   IS_ENABLED3(_XXXX 1,  0)
         */
        #define _IS_ENABLED2(one_or_two_args) _IS_ENABLED3(one_or_two_args 1, 0)

        /* And our second argument is thus now cooked to be 1 in the case
         * where the value is defined to 1, and 0 if not:
         */
        #define _IS_ENABLED3(ignore_this, val, ...) val
    
    #else

        #error "Unsupported compiler!"

    #endif

#endif
