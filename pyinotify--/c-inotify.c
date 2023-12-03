#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/inotify.h>


int main() {
  int fd;
  char *path = "/tmp";

  // 创建 inotify 文件描述符
  fd = inotify_init();
  if (fd < 0) {
    perror("inotify_init");
    return -1;
  }

  // 添加监控点
  // inotify_add_watch(fd, path, IN_CREATE);
  inotify_add_watch(fd, path, IN_ALL_EVENTS);

  // 等待事件
  while (1) {
    // struct inotify_event *event;
    struct inotify_event event;
    int len;

    // 读取事件
    len = read(fd, &event, sizeof(struct inotify_event));
    if (len < 0) {
      perror("read");
      return -1;
    }

    // 处理事件
    switch (event.mask) {
      case IN_CREATE:
        // 文件创建
        printf("create: %s\n", event.name);
        break;
      case IN_DELETE:
        // 文件删除
        printf("delete: %s\n", event.name);
        break;
    }
  }

  return 0;
}

