#include <stdio.h>


int main(){
    float i=0.1;
    int c;
    for(c=0;c<10000000;c++){
        i+=0.2;
    }
    printf("result: %f\n", i);
    return 0;
}

// result: 2175874.250000 差的真多

