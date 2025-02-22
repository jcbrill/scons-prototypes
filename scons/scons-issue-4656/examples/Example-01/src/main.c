#include <stdio.h>
#include "macros.h"

#if IS_ENABLED(FEATURE_A_ENABLED)
#include "feature_a.h"
#endif

int main(void);
int main(void) {}

