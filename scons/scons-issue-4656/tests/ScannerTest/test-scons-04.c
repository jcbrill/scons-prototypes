/* Detect if symbol is defined.
 *
 *   SYMBOL_ISDEFINED(SYMBOL) 
 *      True:  when SYMBOL is <no value>, 0, or 1
 *      False: o.w.
 *
 *   SYMBOL_ISDEFINED(SYMBOL) examples:
 *     undefined   False (undefined)
 *     -DSYMBOL=   True  (no value)
 *     -DSYMBOL    True  (default 1)
 *     -DSYMBOL=0  True  (0)
 *     -DSYMBOL=1  True  (1)
 *     -DSYMBOL=2  False (value not supported)
 *
 * Detect if symbol is enabled.
 *
 *   SYMBOL_ISENABLED(SYMBOL)
 *      True:  when SYMBOL is: 1
 *      False: o.w.
 *
 *   SYMBOL_ISENABLED(SYMBOL) examples:
 *     undefined   False (undefined)
 *     -DSYMBOL=   False (no value)
 *     -DSYMBOL    True  (default 1)
 *     -DSYMBOL=0  False (0)
 *     -DSYMBOL=1  True  (1)
 *     -DSYMBOL=2  False (unsupported value)
 *
 */

#define SYMBOL_ISDEFINED_PLACEHOLDER_ 0,
#define SYMBOL_ISDEFINED_PLACEHOLDER_0 0,
#define SYMBOL_ISDEFINED_PLACEHOLDER_1 0,

#define SYMBOL_ISENABLED_PLACEHOLDER_
#define SYMBOL_ISENABLED_PLACEHOLDER_0
#define SYMBOL_ISENABLED_PLACEHOLDER_1 0,

#if defined(_MSC_VER) && _MSVC_VER < 1400
    /* MSVC 6.0 - 7.1 */

    #define SYMBOL_ISDEFINED_SECONDARG(ignore, x) x
    #define SYMBOL_ISDEFINED___(x) SYMBOL_ISDEFINED_SECONDARG x
    #define SYMBOL_ISDEFINED__(x) SYMBOL_ISDEFINED___((x 1, 0))
    #define SYMBOL_ISDEFINED_(x) SYMBOL_ISDEFINED__(SYMBOL_ISDEFINED_PLACEHOLDER_ ## x)
    #define SYMBOL_ISDEFINED(x) SYMBOL_ISDEFINED_(x,0)

    #define SYMBOL_ISENABLED_SECONDARG(ignore, x) x
    #define SYMBOL_ISENABLED___(x) SYMBOL_ISENABLED_SECONDARG x
    #define SYMBOL_ISENABLED__(x) SYMBOL_ISENABLED___((x 1, 0))
    #define SYMBOL_ISENABLED_(x) SYMBOL_ISENABLED__(SYMBOL_ISENABLED_PLACEHOLDER_ ## x)
    #define SYMBOL_ISENABLED(x) SYMBOL_ISENABLED_(x,0)

#elif defined(_MSC_VER)
    /* MSVC 8.0 and later */

    #define SYMBOL_ISDEFINED____(a, b, ...) b
    #define SYMBOL_ISDEFINED___(a) SYMBOL_ISDEFINED____ a
    #define SYMBOL_ISDEFINED__(x) SYMBOL_ISDEFINED___((x 1, 0))
    #define SYMBOL_ISDEFINED_(...) SYMBOL_ISDEFINED__(SYMBOL_ISDEFINED_PLACEHOLDER_ ## __VA_ARGS__)
    #define SYMBOL_ISDEFINED(x,...) SYMBOL_ISDEFINED_(x)

    #define SYMBOL_ISENABLED____(a, b, ...) b
    #define SYMBOL_ISENABLED___(a) SYMBOL_ISENABLED____ a
    #define SYMBOL_ISENABLED__(x) SYMBOL_ISENABLED___((x 1, 0))
    #define SYMBOL_ISENABLED_(...) SYMBOL_ISENABLED__(SYMBOL_ISENABLED_PLACEHOLDER_ ## __VA_ARGS__)
    #define SYMBOL_ISENABLED(x,...) SYMBOL_ISENABLED_(x)

#else

    #define SYMBOL_ISDEFINED_SECONDARG(ignore, x, ...) x
    #define SYMBOL_ISDEFINED__(x) SYMBOL_ISDEFINED_SECONDARG(x 1, 0)
    #define SYMBOL_ISDEFINED_(x) SYMBOL_ISDEFINED__(SYMBOL_ISDEFINED_PLACEHOLDER_ ## x)
    #define SYMBOL_ISDEFINED(x) SYMBOL_ISDEFINED_(x)

    #define SYMBOL_ISENABLED_SECONDARG(ignore, x, ...) x
    #define SYMBOL_ISENABLED__(x) SYMBOL_ISENABLED_SECONDARG(x 1, 0)
    #define SYMBOL_ISENABLED_(x) SYMBOL_ISENABLED__(SYMBOL_ISENABLED_PLACEHOLDER_ ## x)
    #define SYMBOL_ISENABLED(x) SYMBOL_ISENABLED_(x)

#endif

/* Expected includes:
 *   undefined   "if-false-1.h" "if-false-2.h" (undefined)
 *   -DSYMBOL=   "if-true-1.h"  "if-false-2.h" (no value)
 *   -DSYMBOL    "if-true-1.h"  "if-true-2.h"  (default 1)
 *   -DSYMBOL=0  "if-true-1.h"  "if-false-2.h" (0)
 *   -DSYMBOL=1  "if-true-1.h"  "if-true-2.h"  (1)
 *   -DSYMBOL=2  "if-false-1.h" "if-false-2.h" (unsupported value)
 *
 */

#if SYMBOL_ISDEFINED(FEATURE_A_ENABLED)
#pragma message("SYMBOL_ISDEFINED(FEATURE_A_ENABLED) is True")
#include "if-true-1.h"
#else
#pragma message("SYMBOL_ISDEFINED(FEATURE_A_ENABLED) is False")
#include "if-false-1.h"
#endif

#if SYMBOL_ISENABLED(FEATURE_A_ENABLED)
#pragma message("SYMBOL_ISENABLED(FEATURE_A_ENABLED) is True")
#include "if-true-2.h"
#else
#pragma message("SYMBOL_ISENABLED(FEATURE_A_ENABLED) is False")
#include "if-false-2.h"
#endif

int main(void);
int main(void) {}

