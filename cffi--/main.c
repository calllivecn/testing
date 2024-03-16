#include <stdio.h>

#include "add.h"

int main(){

    Point a, b;
    a.x = 4;
    a.y = 5;

    b.x = 6;
    b.y = 7;

    a = add2(a, b);
    printf("a.x=%d, a.y=%d\n", a.x, a.y);

    return 0;
}
