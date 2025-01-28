// #include <stdio.h>

#define SUPPRESS_UNREFERENCED_PARAMETER(P) {(P)=(P);}

int main(int argc, char** argv) {

    SUPPRESS_UNREFERENCED_PARAMETER(argc);
    SUPPRESS_UNREFERENCED_PARAMETER(argv);

    /* 
    printf("Hello, World!\n");
    */

    return 0;
}