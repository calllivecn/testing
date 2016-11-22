#include<stdio.h>


unsigned long nn(int m)
{
	unsigned long s=1,i;
	//if(m==1) return s;
	for(i=2;i<=m;i++){s*=i;}
return s;
}



int main()
{
	unsigned long sum,t,i,n;
	n=10;
	for(i=1;i<=n;i++)
	{
		sum=nn(i);
		printf("%ld 的介乘= %ld\n",i,sum);
	}
return 0;
}
