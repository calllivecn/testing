#include <stdio.h>
#include <sys/prctl.h>

int main() {
  //prctl(PR_SET_NAME, "MyCustomProcessName", 0, 0, 0);
  prctl(PR_SET_NAME, "MyCustomProcessName");
  char name[16];
  prctl(PR_GET_NAME, (unsigned long) name, 0, 0);
  printf("Process name set to: %s\n", name);
  printf("按回车退出\n");
  getchar();
  return 0;
}

