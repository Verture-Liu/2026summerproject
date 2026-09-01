#ifndef PALEORIGOR_BWA_MINGW_SYS_RESOURCE_H
#define PALEORIGOR_BWA_MINGW_SYS_RESOURCE_H

#include <string.h>
#include <sys/time.h>
#include <time.h>

#define RUSAGE_SELF 0

struct rusage {
    struct timeval ru_utime;
    struct timeval ru_stime;
    long ru_maxrss;
};

static inline int getrusage(int who, struct rusage *usage)
{
    clock_t ticks;
    (void)who;
    memset(usage, 0, sizeof(*usage));
    ticks = clock();
    if (ticks != (clock_t)-1) {
        usage->ru_utime.tv_sec = (long)(ticks / CLOCKS_PER_SEC);
        usage->ru_utime.tv_usec =
            (long)(((ticks % CLOCKS_PER_SEC) * 1000000L) / CLOCKS_PER_SEC);
    }
    return 0;
}

#endif
