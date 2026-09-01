#ifndef PALEORIGOR_SEQTK_MINGW_COMPAT_H
#define PALEORIGOR_SEQTK_MINGW_COMPAT_H

#if defined(__MINGW32__) || defined(__MINGW64__)
#include <stdint.h>
#include <string.h>

#ifndef index
#define index strchr
#endif

static uint64_t paleorigor_drand48_state = UINT64_C(0x1234abcd330e);

static uint64_t paleorigor_drand48_next(void)
{
    paleorigor_drand48_state =
        (UINT64_C(0x5deece66d) * paleorigor_drand48_state + UINT64_C(0xb)) &
        UINT64_C(0xffffffffffff);
    return paleorigor_drand48_state;
}

static void srand48(long seed)
{
    paleorigor_drand48_state =
        (((uint64_t)(uint32_t)seed << 16) | UINT64_C(0x330e)) &
        UINT64_C(0xffffffffffff);
}

static long lrand48(void)
{
    return (long)(paleorigor_drand48_next() >> 17);
}

static double drand48(void)
{
    return (double)paleorigor_drand48_next() / 281474976710656.0;
}
#endif

#endif
