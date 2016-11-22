

import sys

n=int(sys.argv[1])
#print(sys.argv)
try:
	s=sys.argv[2]
except Exception as e:
	s='#'

j=n

# 输出上三角形
print('-'*10,'输出上三角形','-'*10)
for t in range(1,n+1):

	print(' '*(j-t),sep='',end='')

	
	print(s*t,sep='',end='')
	print(s*(t-1),sep='',end='')

	print()


# 输出空心三角
print('-'*10,'输出空心三角形','-'*10)  
for t in range(1,n):
	
	print(' '*(j-t),s,sep='',end='')

	if t-1 >0:
		print(' '*(t-1),sep='',end='')

		print(' '*(t-2),s,sep='',end='')
	print()
print(s*(n*2-1),sep='')
		


