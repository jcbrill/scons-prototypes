
#define COND_INCLUDE_1
#include "cond-include.h"
#undef COND_INCLUDE_1

#define COND_INCLUDE_2
#include "cond-include.h"
#undef COND_INCLUDE_2

int main(void);
int main(void) {}
