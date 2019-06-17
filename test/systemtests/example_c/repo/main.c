#include "stdio.h"
#include "stdlib.h"
#include "assert.h"
#include "lib/lib.h"

int main(int argc, char **argv) {
    if (argc != 3) {
        printf("expect 2 arguments: values a and b\n");
        assert(0);
    }
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);
    int res = compute(a, b);
    printf("The result is: %d\n", res);
    return 0;
}