
a.out:
	gcc -o $@ main.c -I . -L . -l add

libadd.so:
	gcc -shared -fPIC -o $@ add.c

all:
	echo "开始编译..."
	#$(MAKE) clean
	$(MAKE) *.c

%.so:
	echo "SO: $*.so C: $*.c"
	gcc -shared -fPIC -o $@ $*.c


clean:
	rm -v $@.so
