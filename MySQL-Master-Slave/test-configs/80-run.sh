
master="mysql80-m"
slave1="mysql80-s1"
slave2="mysql80-s2"

m_cnf="$(pwd)/80-m.cnf"
s1_cnf="$(pwd)/80-s1.cnf"
s2_cnf="$(pwd)/80-s2.cnf"

image="docker.io/library/mysql:8.0"

if [ "$1"x = "rm"x ];then

	podman rm -f $slave1
	podman rm -f $slave2

	podman rm -f $master

else

	podman run -d --name $master --network mysql -e MYSQL_ROOT_PASSWORD="mysql80" -v "$m_cnf":/etc/my.cnf "$image"
	
	podman run -d --name $slave1 --network mysql -e MYSQL_ROOT_PASSWORD="mysql80" -v "$s1_cnf":/etc/my.cnf "$image"

	podman run -d --name $slave2 --network mysql -e MYSQL_ROOT_PASSWORD="mysql80" -v "$s2_cnf":/etc/my.cnf "$image"
fi
