/*

# define COMMENTED_OUT 1
# define STRLIT1 "/* hello */"
# define STRLIT2 "// hello"
# define STRMACRO(a) "/*" a "*/"

*/

#define FEATURE_A_ENABLED 0

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

#if IS_ENABLED(FEATURE_A_ENABLED)
#include "if-true.h"
#else
#include "if-false.h"
#endif

int main()
{
}

