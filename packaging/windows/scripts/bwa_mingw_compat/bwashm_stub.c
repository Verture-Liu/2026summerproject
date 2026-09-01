#include <stdio.h>
#include "bwa.h"

/* POSIX shared-memory index staging is unavailable on native Windows.
 * Regular BWA indexing and alignment do not depend on this optional command. */
int bwa_shm_stage(bwaidx_t *idx, const char *hint, const char *tmpfn)
{
    (void)idx; (void)hint; (void)tmpfn;
    return -1;
}

bwaidx_t *bwa_idx_load_from_shm(const char *hint)
{
    (void)hint;
    return 0;
}

int bwa_shm_test(const char *hint)
{
    (void)hint;
    return 0;
}

int bwa_shm_list(void) { return -1; }
int bwa_shm_destroy(void) { return -1; }

int main_shm(int argc, char *argv[])
{
    (void)argc; (void)argv;
    fprintf(stderr, "bwa shm is not available in the native Windows build.\n");
    return 1;
}
