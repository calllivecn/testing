
master="mysql57-m"
slave="mysql57-s"

if [ "$1"x = "rm"x ];then
	podman rm -f $master
	podman rm -f $slave

	podman volume prune

else

	podman run -d --name $master --network mysql -e MYSQL_ROOT_PASSWORD="mysql80" -v $(pwd)/57-m.cnf:/etc/my.cnf docker.io/library/mysql:5.7
	
	podman run -d --name $slave --network mysql -e MYSQL_ROOT_PASSWORD="mysql80" -v $(pwd)/57-s.cnf:/etc/my.cnf docker.io/library/mysql:5.7
fi
