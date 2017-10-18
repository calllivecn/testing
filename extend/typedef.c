#include<stdio.h>


typedef struct {
	int x;
	int y;
}pointer;

pointer * P=NULL;

int main(){
	int *p;
	const char *ch;
	pointer a;
	a.x = 123;
	a.y = 456;
	p = &a.x;
	printf("a.x %d a.y %d\n",a.x,a.y);
	printf("int p address 0x%p\n&a.x address %p\n",p,&a.x);
	P=&a;
	ch="a string";
	ch="2";
	printf("const char *ch -> %s\n",ch);
	printf("&ch -> 0x%p\n",&ch);
	printf("pointer ch address %p\n",&ch);
	P->y = 56;
	printf("P->x:%d,P->y%d\n",P->x,P->y);

return 0;
}

