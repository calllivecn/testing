#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <poll.h>
#include <string.h>
#include <unistd.h>

/*
 * Monitor memory partial stall with 1s tracking window size
 * and 150ms threshold.
 */
int main() {
      const char trig[] = "some 150000 1000000";
      const char cpu[] = "/proc/pressure/cpu";
      struct pollfd fds;
      int n;

      fds.fd = open(cpu, O_RDWR | O_NONBLOCK);
      if (fds.fd < 0) {
              printf("%s open error: %s\n", cpu, strerror(errno));
              return 1;
      }
      fds.events = POLLPRI;

      if (write(fds.fd, trig, strlen(trig) + 1) < 0) {
              printf("%s write error: %s\n", cpu, strerror(errno));
              return 1;
      }

      printf("waiting for events...\n");
      while (1) {
              n = poll(&fds, 1, -1);
              if (n < 0) {
                      printf("poll error: %s\n", strerror(errno));
                      return 1;
              }
              if (fds.revents & POLLERR) {
                      printf("got POLLERR, event source is gone\n");
                      return 0;
              }
              if (fds.revents & POLLPRI) {
                      printf("event triggered!\n");
              } else {
                      printf("unknown event received: 0x%x\n", fds.revents);
                      return 1;
              }
      }

      return 0;
}

