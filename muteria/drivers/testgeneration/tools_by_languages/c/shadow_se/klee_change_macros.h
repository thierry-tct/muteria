#ifndef KLEE_CHANGE_MACROS_H_
#define KLEE_CHANGE_MACROS_H_

//#include <stdio.h>  // DBG
#include <stdlib.h>

//This is very important, as it is used by MFI (when RESOLVE_KLEE_CHANGE is not passed to the compiler, compile the NEW version)
#ifndef RESOLVE_KLEE_CHANGE
#define RESOLVE_KLEE_CHANGE 0
#endif

#if RESOLVE_KLEE_CHANGE == 0
  #ifdef ENFORCE_STATIC_KLEE_CHANGE
  static
  #endif
   int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_true(void);
  #ifdef ENFORCE_STATIC_KLEE_CHANGE
  static
  #endif
   int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_false(void);
  int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_true(void) { return 1; }
  int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_false(void) { return 0; }
  
  //if 64 bits system. We use this because uintptr_t is defined as such in stdint.h, which cannot be included as the file to include to is already pre-processed
  // IMPORTANT: this function is actually not called but klee run a special function when klee_change is encountered in the program: This is just used for compilation-linking purpose.
  #if defined __x86_64__ && !defined __ILP32__  
    //static unsigned long int __attribute__ ((noinline)) klee_change(unsigned long int x, unsigned long int y)
    typedef unsigned long long my_klee_change_large_type;
  #else
    typedef unsigned long my_klee_change_large_type;
  #endif

  #ifdef MUTERIA_FOR_SEMU_TEST_GENERATION
    extern unsigned int klee_semu_GenMu_Mutant_ID_Selector = 2;
    void __attribute__ ((noinline)) __attribute__(( unused )) klee_semu_GenMu_Mutant_ID_Selector_Func(
                                                                unsigned int start, unsigned int end) {}
    void __attribute__ ((noinline)) __attribute__(( unused )) klee_semu_GenMu_Post_Mutation_Point_Func(
                                                                unsigned int start, unsigned int end) {}
    #ifdef ENFORCE_STATIC_KLEE_CHANGE
    static
    #endif
     my_klee_change_large_type __attribute__ ((noinline)) klee_change(my_klee_change_large_type x, my_klee_change_large_type y)
    {
      my_klee_change_large_type ret;
      klee_semu_GenMu_Mutant_ID_Selector_Func(1, 1);
      switch (klee_semu_GenMu_Mutant_ID_Selector) {
        case 1:
          ret = x;
          break;
        default:
          ret = y;
          break;
      }
      klee_semu_GenMu_Post_Mutation_Point_Func(0, 1);
      //printf ("(DBG) in klee change!!!");
      return ret;
    }
  #else
    #ifdef ENFORCE_STATIC_KLEE_CHANGE
    static
    #endif
     my_klee_change_large_type __attribute__ ((noinline)) klee_change(my_klee_change_large_type x, my_klee_change_large_type y)
    {
      static char * version_str;
      version_str = getenv("KLEE_CHANGE_RUNTIME_SET_OLD_VERSION");
      if (version_str == NULL)
        return y;
      else
        return x;
    }
  #endif
#endif

// RESOLVE_KLEE_CHANGE: 
// case -1: use old version
// case  1: use new version
// case  0: use both when ran with KLEE (for future use)
#if RESOLVE_KLEE_CHANGE == -1
  //Here we use the function but not the macro for klee_get_<true,false> because for the old version the code controled by klee_get_false will be removed by compiler, 
  //thus the diff considered not covered by any test (case were a change consists of adding code.). This is mainly used for the coverage
  #ifdef ENFORCE_STATIC_KLEE_CHANGE
  static
  #endif
   int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_true(void);
  #ifdef ENFORCE_STATIC_KLEE_CHANGE
  static
  #endif
   int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_false(void);
  int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_true(void) { return 1; }
  int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_false(void) { return 0; } 
  #define klee_change(x,y)    (x)
    
#elif RESOLVE_KLEE_CHANGE == 1
  //Here we use the function but not the macro for klee_get_<true,false> because for the old version the code controled by klee_get_false will be removed by compiler, 
  //thus the diff considered not covered by any test (case were a change consists of adding code.). This is mainly used for the coverage
  #ifdef ENFORCE_STATIC_KLEE_CHANGE
  static
  #endif
   int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_true(void);
  #ifdef ENFORCE_STATIC_KLEE_CHANGE
  static
  #endif
   int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_false(void);
  int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_true(void) { return 1; }
  int __attribute__ ((noinline)) __attribute__(( unused )) klee_get_false(void) { return 0; } 
  #define klee_change(x,y)    (y) 
    
#elif RESOLVE_KLEE_CHANGE == 11
  // Here we use macro for klee_get_<true, false> because the code will be mutated later on. better have nothing related to klee
  #define klee_get_true() (1)
  #define klee_get_false() (0)
  #define klee_change(x,y)    (y) 
#endif

#endif /* KLEE_CHANGE_MACROS_H_ */
