#if defined (__GNUC__) || defined(__GNUG__)
    #include "compiler_gcc.h"
#elif defined(__MINGW32__) || defined(__MINGW64__)
    #include "compiler_mingw.h"
#elif defined(_MSC_VER)
    #include "compiler_msvc.h"
#else
    #error "Unsupported compiler!"
#endif

#if defined(__amd64__) || defined(__amd64) || defined(__x86_64__) || defined(__x86_64) || defined(_M_X64) || defined(_M_AMD64)
    #include "arch_x64.h"
#elif defined(i386) || defined(__i386) || defined(__i386__) || defined(_M_IX86) || defined(_X86_)
    #include "arch_x86.h"
#else
    #error "Unsupported architecture!"
#endif

int main(void);
int main(void) {}

