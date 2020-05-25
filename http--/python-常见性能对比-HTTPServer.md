# python 常见web服务器性能对比 (都是使用一进程 单核 进行测试) 之后还会添上 nginx，go

- CPU：     Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
- MEM:      8G
- kernel:	5.4.0-31-generic

## python 自带 HTTP 服务器， 不行，处理量一大，系统端口消耗完，会直接卡死。(太多closed、timewait)

- 为 HTTPServer 添加了多线程处理的（HTTPServer 默认的一次只能处理一个请求。）

- 关闭 http.server.HTTPServer log_message() 和 http.server.BaseRquestHandler log_message() 函数，

    能关闭stderr输出，提高性能。

- 下次在测试 closed、timewait 优化后的并发结果，

- 并发处理结果，差距很大。在ab -c 2000 -n 10000 时： 1.8k 2.2k 3.4k 都有。

```shell
root@ba0c52284ffa:/# ab -c 2000 -n 10000 "http://192.168.0.3:6789/info"
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 192.168.0.3 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        server/0.2
Server Hostname:        192.168.0.3
Server Port:            6789

Document Path:          /info
Document Length:        13 bytes

Concurrency Level:      2000
Time taken for tests:   5.346 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1430000 bytes
HTML transferred:       130000 bytes
Requests per second:    1870.46 [#/sec] (mean)
Time per request:       1069.254 [ms] (mean)
Time per request:       0.535 [ms] (mean, across all concurrent requests)
Transfer rate:          261.21 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   10 138.2      0    3053
Processing:     1    4  11.4      3     412
Waiting:        0    3  10.6      2     412
Total:          1   14 143.8      3    3270

Percentage of the requests served within a certain time (ms)
  50%      3
  66%      3
  75%      3
  80%      3
  90%      4
  95%      9
  98%     62
  99%     71
 100%   3270 (longest request)

```

## aiohttp server，但注意设置高点的 ulimit -n 1048576 这防止 "OSError: [Errno 24] Too many open files"

- 结果稳定，在: ab -c 2000 -n 10000 时 3.4k

```shell
root@ba0c52284ffa:/# ab -c 2000 -n 10000 "http://192.168.0.3:8080/calllivecn"
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 192.168.0.3 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        Python/3.8
Server Hostname:        192.168.0.3
Server Port:            8080

Document Path:          /calllivecn
Document Length:        14 bytes

Concurrency Level:      2000
Time taken for tests:   2.912 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1650000 bytes
HTML transferred:       140000 bytes
Requests per second:    3434.65 [#/sec] (mean)
Time per request:       582.301 [ms] (mean)
Time per request:       0.291 [ms] (mean, across all concurrent requests)
Transfer rate:          553.44 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0  117 316.3      3    1030
Processing:    37   87  42.1     81     312
Waiting:       25   73  39.0     65     309
Total:         41  204 331.8     85    1319

Percentage of the requests served within a certain time (ms)
  50%     85
  66%    105
  75%    111
  80%    134
  90%   1089
  95%   1121
  98%   1140
  99%   1268
 100%   1319 (longest request)

```

## uwsgi server, 

```shell
下次在测试
```


## nginx 

- 结果很稳定 在 ab -c 2000 -n 10000 时 9.2k

- 配置：

    location /info {
            return 200 "test 成功";
        }

```shell
root@ba0c52284ffa:/# ab -c 2000 -n 10000 "http://192.168.0.3:8888/info"
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 192.168.0.3 (be patient)
Completed 1000 requests
Completed 2000 requests
Completed 3000 requests
Completed 4000 requests
Completed 5000 requests
Completed 6000 requests
Completed 7000 requests
Completed 8000 requests
Completed 9000 requests
Completed 10000 requests
Finished 10000 requests


Server Software:        nginx/1.16.0
Server Hostname:        192.168.0.3
Server Port:            8888

Document Path:          /info
Document Length:        11 bytes

Concurrency Level:      2000
Time taken for tests:   1.085 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1680000 bytes
HTML transferred:       110000 bytes
Requests per second:    9216.22 [#/sec] (mean)
Time per request:       217.009 [ms] (mean)
Time per request:       0.109 [ms] (mean, across all concurrent requests)
Transfer rate:          1512.04 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   18  12.6     14      65
Processing:     7   43 101.0     18     490
Waiting:        6   38 101.7     14     486
Total:         10   61 105.9     32     520

Percentage of the requests served within a certain time (ms)
  50%     32
  66%     33
  75%     34
  80%     35
  90%     85
  95%    503
  98%    513
  99%    517
 100%    520 (longest request)
```


# 大量 closed 和 timewait 状态连接的处理，（系统处理方式，这种方式感觉不是太好）

```shell
#表示开启重用。允许将TIME_WAIT sockets重新用于新的TCP连接，默认为0，表示关闭
1、net.ipv4.tcp_tw_reuse = 1

#表示开启TCP连接中TIME_WAIT sockets的快速回收，默认为0，表示关闭
2、net.ipv4.tcp_tw_recycle = 1

#表示如果套接字由本端要求关闭，这个参数决定了它保持在FIN_WAIT_2状态的时间（可改为30，一般来说FIN_WAIT_2的连接也极少）
3、net.ipv4.tcp_fin_timeout = 30

#控制 TCP/IP 尝试验证空闲连接是否完好的频率
4、net.ipv4.tcp_keepalive_time = 600

#表示SYN队列的长度，默认为1024，加大队列长度为8192，可以容纳更多等待连接的网络连接数。
5、net.ipv4.tcp_max_syn_backlog = 8192 

#表示系统同时保持TIME_WAIT的最大数量，如果超过这个数字，TIME_WAIT将立刻被清除并打印警告信息。默认为180000，改为60000。
6、net.ipv4.tcp_max_tw_buckets = 60000

#记录的那些尚未收到客户端确认信息的连接请求的最大值。对于有128M内存的系统而言，缺省值是1024，小内存的系统则是128。
7、net.ipv4.tcp_max_syn_backlog = 65536

#每个网络接口接收数据包的速率比内核处理这些包的速率快时，允许送到队列的数据包的最大数目。
8、net.core.netdev_max_backlog = 32768

#web应用中listen函数的backlog默认会给我们内核参数的net.core.somaxconn限制到128，而nginx定义的NGX_LISTEN_BACKLOG默认为511，所以有必要调整这个值。
9、net.core.somaxconn = 32768

#定义默认的发送窗口大小;对于更大的 BDP 来说,这个大小也应该更大。
10、net.core.wmem_default = 8388608

#该文件指定了接收套接字缓冲区大小的缺省值(以字节为单位)。
11、net.core.rmem_default = 8388608

#最大socket读buffer。
12、net.core.rmem_max = 16777216

#最大socket写buffer。
13、net.core.wmem_max = 16777216

#为了打开对端的连接，内核需要发送一个SYN并附带一个回应前面一个SYN的ACK。也就是所谓三次握手中的第二次握手。这个设置决定了内核放弃连接之前发送SYN+ACK包的数量。
14、net.ipv4.tcp_synack_retries = 2

#对于一个新建连接，内核要发送多少个 SYN 连接请求才决定放弃。不应该大于255，默认值是5，对应于180秒左右时间。
15、net.ipv4.tcp_syn_retries = 2

#表示开启TCP连接中TIME-WAITsockets的快速回收，默认为0，表示关闭
16、net.ipv4.tcp_tw_recycle = 1

#开启重用。允许将TIME-WAITsockets重新用于新的TCP连接。
17、net.ipv4.tcp_tw_reuse = 1

#同样有3个值,意思是:低于第一个值，TCP没有内存压力；在第二个值下，进入内存压力阶段；高于第三个值，TCP拒绝分配socket（内存单位是页）。
18、net.ipv4.tcp_mem = 94500000 915000000 927000000

#系统中最多有多少个TCP套接字不被关联到任何一个用户文件句柄上。
19、net.ipv4.tcp_max_orphans = 3276800

#每个网络接口接收数据包的速率比内核处理这些包的速率快时，允许送到队列的数据包的最大数目。
20、net.core.netdev_max_backlog = 8096

#表示开启SYNCookies。当出现SYN等待队列溢出时，启用cookies来处理，可防范少量SYN攻击，默认为1，表示开启。
21、net.ipv4.tcp_syncookies = 1
```
