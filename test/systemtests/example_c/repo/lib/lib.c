#include "lib.h"

#ifdef ENABLE_SHADOW_SE
#include "klee_change_macros.h"
#endif

#ifdef JUST_CHECK_CRASH

int compute(int a, int b){return a+b;}
int get_even_total(int a, int b){return a+b;}
int get_odd_total(int a, int b){return a+b;}

#else

int compute(int a, int b){
    int oddtotal = get_odd_total(a,b);
    int eventotal = get_even_total(a,b);
    if (oddtotal < -100000)
        oddtotal = 0;
    return (oddtotal + eventotal);
}

int get_even_total(int a, int b){
    int arr[2] = {a,b};
#ifdef ENABLE_SHADOW_SE
    int t;
    t = klee_change(-1, 0);
#else
    int t = 0;
#endif
    int i;
    for (i=0; i < 2; ++i)
        if (arr[i] % 2 == 0)
            t += arr[i];
    return t;
}

int get_odd_total(int a, int b){
    int t = 0;
    if (a % 2 != 0)
        t += a;
    if (b % 2 != 0)
        t += b;
    return t;
}

#endif