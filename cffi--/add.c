#include <stdlib.h>

#include "add.h"

int add(int a, int b){
    a += b;
    return a;
}

Point add2(Point a, Point b){
    a.x += b.x;
    a.y += b.y;
    return a;
}

