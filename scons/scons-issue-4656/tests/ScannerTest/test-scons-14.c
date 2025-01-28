/* #define COMMENT1 */

/*
#define COMMENT2
*/

/* */ #define COMMENT3 /* */

/*
*/ #define COMMENT4

// FALSE
#if defined(COMMENT1)
#include "if-true-1.h"
#else
#include "if-false-1.h"
#endif

// FALSE
#if defined(COMMENT2)
#include "if-true-2.h"  // CConditionalScanner
#else
#include "if-false-2.h"
#endif

// TRUE
#if defined(COMMENT3)
#include "if-true-3.h"
#else
#include "if-false-3.h"
#endif

// TRUE
#if defined(COMMENT4)
#include "if-true-4.h"
#else
#include "if-false-4.h"  // CConditionalScanner
#endif

int main(void);
int main(void) {}

