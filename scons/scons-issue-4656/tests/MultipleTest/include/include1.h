#ifndef INCLUDE1_H
#define INCLUDE1_H
/* #pragma message("include1.h") */

#define PATH_1
#include "include2.h"
#undef PATH_1

#define PATH_2
#include "include2.h"
#undef PATH_2

#endif
