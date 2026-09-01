#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef O_BINARY
#define O_BINARY 0
#endif

typedef struct {
    int fd;
} koaux_t;

/* Native Windows packaging supports stdin and local files. BWA's optional
 * Unix shell-pipe and HTTP/FTP input paths are intentionally unavailable. */
void *kopen(const char *fn, int *fd)
{
    koaux_t *aux;
    *fd = -1;
    if (strcmp(fn, "-") == 0) {
        *fd = STDIN_FILENO;
    } else if (fn[0] != '<' && strstr(fn, "://") == 0) {
        *fd = open(fn, O_RDONLY | O_BINARY);
    }
    if (*fd < 0) return 0;
    aux = (koaux_t *)calloc(1, sizeof(koaux_t));
    if (aux == 0) return 0;
    aux->fd = *fd;
    return aux;
}

int kclose(void *handle)
{
    free(handle);
    return 0;
}
