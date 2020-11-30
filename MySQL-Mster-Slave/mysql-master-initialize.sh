#!/bin/bash
# date 2020-11-30 17:16:44
# author calllivecn <c-all@qq.com>

# 自动配置 MySQL GTID 主从

newpw=
slave_user=
slave_passwd=

mycnf="/etc/my.cnf"

start_mysql(){
	#setenforce 0
	systemctl start mysqld
	echo "skip-grant-tables" >> /etc/my.cnf
	systemctl restart mysqld
	genpwd=$(grep -oE "password is generated for root@localhost: (.*)" /var/log/mysqld.log | awk -F':' '{print $2}') || genpwd=""
	
	
	mysql -uroot -e "update mysql.user set password_expired='N'";
	sed -i 's/skip-grant-tables/#skip-grant-tables/g' /etc/my.cnf
	systemctl restart mysqld
}


master_mycnf(){
echo "server-id=1" >> "$mycnf"
echo "log-bin=mysql-bin" >> "$mycnf"
echo "gtid-mode=on" >> "$mycnf"
echo "enforce-gtid-consistency=on" >> "$mycnf"
echo "log-slave-updates=on" >> "$mycnf"

systemctl start mysqld.service
sleep 5
}

slave_mycnf(){
echo "server-id=10" >> /etc/my.cnf
echo "log-bin=mysql-bin" >> "$mycnf"
echo "gtid-mode=on" >> "$mycnf"
echo "enforce-gtid-consistency=on" >> "$mycnf"
echo "log-slave-updates=on" >> "$mycnf"

systemctl start mysqld.service
sleep 5
}


# 拿到初始化的 root 密码
genpw=$(grep -oE "password is generated for root@localhost: (.*)" /var/log/mysqld.log | awk -F': ' '{print $2}')

changerootpw(){
    mysql -uroot -p${genpw} --connect-expired-password -e "alter user user() identified by \"${newpw}\"";
}

master_config(){

master_mycnf

echo '授权'

mysql  -uroot -p${newpwd} <<EOF
create user '${slave_user}' identified by '${slave_passwd}';
GRANT REPLICATION SLAVE ON *.* to '${slave_user}'@'%';
use mysql;
update user set host='%' where user='root';
flush privileges;
EOF
}


# slave 

slave_config(){

slave_mycnf

echo '授权'

mysql  -uroot -p${newpwd}  <<EOF
change master to master_host='${master_ip}',master_port=3306,master_user='${slave_user}',master_password='${slave_passwd}', master_auto_postition=1;
start slave;
use mysql;
update user set host='%' where user='root';
flush privileges;
EOF
}


check_ok(){
#检查主从复制是否搭建成功
running_num=$(mysql -uroot -p${newpwd} -e "show slave status\G" 2>/dev/null |grep "Running:"|wc -l)

if [ $running_num -eq 2 ];then
    echo "mysql主从复制搭建成功"
else
    echo  "mysql主从搭建失败"
fi
}

