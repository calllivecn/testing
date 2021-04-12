# python 常见web服务器性能对比 (都是使用一个进程 单核 进行测试) 还有 nginx， 之后还会添上 golang

- 都是使用的 http echo 服务器做的测试
- CPU：     Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz
- MEM:      8G
- kernel:   5.4.0-31-generic
- python:   3.8
- 但注意设置高点的 ulimit -n 1048576 这防止 "OSError: [Errno 24] Too many open files"
- ~~不行，处理量一大，系统端口消耗完，会直接卡死。(太多closed、timewait)~~
- ~~大量 closed 和 timewait 状态连接的处理，（系统处理方式，这种方式感觉不是太好）~~

- ~~closed 和 timewait 10月 在测试。linux 5.4.0-51-generic 又没有了。到了一万多个的时候，就不会在涨了。。。也不会卡了。~~

## python 自带 http.HTTPServer 服务器

- 为 HTTPServer 添加了多线程处理的（HTTPServer 默认的一次只能处理一个请求。）

- 关闭 http.server.HTTPServer log_message() 和 http.server.BaseRquestHandler log_message() 函数，

    能关闭stderr输出，提高性能。

- ~~下次在测试 closed、timewait 优化后的并发结果~~

- 并发处理结果，差距很大。在ab -c 2000 -n 10000 时： 1.8k 2.2k 3.4k 都有。

- 这。。。添加上这3个优化后, 并发稳定在了 3.2k： (原因好像是：net.ipv4.tcp_syncookies = 0, 把内核的防流水攻击关了。)

  httpd.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)

  这样可以关闭：TCP 的40ms 延迟？？？好像是，但我还不能确定。

- 代码： http1.py

### 一次测试结果:

```shell
root@ba0c52284ffa:/# ab -c 2000 -n 10000 http://192.168.0.3:6789/callivecn
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

Document Path:          /callivecn
Document Length:        13 bytes

Concurrency Level:      2000
Time taken for tests:   3.040 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      1430000 bytes
HTML transferred:       130000 bytes
Requests per second:    3289.32 [#/sec] (mean)
Time per request:       608.028 [ms] (mean)
Time per request:       0.304 [ms] (mean, across all concurrent requests)
Transfer rate:          459.35 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    3  47.7      0    1035
Processing:     1    2   6.8      2     414
Waiting:        1    2   6.6      2     414
Total:          1    5  51.3      2    1437

Percentage of the requests served within a certain time (ms)
  50%      2
  66%      2
  75%      2
  80%      2
  90%      2
  95%      2
  98%      3
  99%     53
 100%   1437 (longest request)

```

## aiohttp server

- 结果稳定在: ab -c 2000 -n 10000 时 3.4k

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

## uwsgi server(1c 20t) 这是 net.ipv4.tcp_syncookies = 0 关闭之后的测试: 居然有14.4k 的并发量

- 代码： echo-flask.py echo-uwsgi.ini

```shell
root@ba0c52284ffa:/# ab -c 2000 -n 10000 http://192.168.0.3:9999/callivecn
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


Server Software:        
Server Hostname:        192.168.0.3
Server Port:            9999

Document Path:          /callivecn
Document Length:        21 bytes

Concurrency Level:      2000
Time taken for tests:   0.690 seconds
Complete requests:      10000
Failed requests:        0
Non-2xx responses:      10000
Total transferred:      1040000 bytes
HTML transferred:       210000 bytes
Requests per second:    14484.78 [#/sec] (mean)
Time per request:       138.076 [ms] (mean)
Time per request:       0.069 [ms] (mean, across all concurrent requests)
Transfer rate:          1471.11 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        2    4   5.4      3      61
Processing:     1    3   0.5      3       5
Waiting:        0    2   0.7      2       5
Total:          4    7   5.4      6      64

Percentage of the requests served within a certain time (ms)
  50%      6
  66%      6
  75%      6
  80%      6
  90%      7
  95%      7
  98%      7
  99%     57
 100%     64 (longest request)
```


## nginx 下 ab 是性能瓶颈 😆

- 结果很稳定 在 ab -c 2000 -n 10000 时 9.2k ()

- net.ipv4.tcp_syncookies = 0 关闭之后： 14.4k

- net.ipv4.tcp_syncookies = 0 关闭之后： 14.4k ab -c 4000 -n 20000 18.9K

- 配置：

```nginx
server {
    listen 8888;
    location /calllivecn {
            return 200 "test 成功, calllivecn";
        }
}
```

```shell
root@ba0c52284ffa:/# ab -c 2000 -n 10000 http://192.168.0.3:8888/calllivecn
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


Server Software:        
Server Hostname:        192.168.0.3
Server Port:            8888

Document Path:          /calllivecn
Document Length:        0 bytes

Concurrency Level:      2000
Time taken for tests:   0.674 seconds
Complete requests:      10000
Failed requests:        10000
   (Connect: 0, Receive: 0, Length: 9008, Exceptions: 992)
Non-2xx responses:      9008
Total transferred:      2729424 bytes
HTML transferred:       1378224 bytes
Requests per second:    14828.57 [#/sec] (mean)
Time per request:       134.875 [ms] (mean)
Time per request:       0.067 [ms] (mean, across all concurrent requests)
Transfer rate:          3952.49 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:       26   40   8.5     38      74
Processing:    14   52  12.8     52      90
Waiting:        0   37  15.8     43      61
Total:         49   92  11.9     93     119

Percentage of the requests served within a certain time (ms)
  50%     93
  66%     96
  75%     98
  80%     99
  90%    107
  95%    115
  98%    117
  99%    118
 100%    119 (longest request)

```


## 这之后添加测试golang标准库。

- golang net/http

- 很快呀，单核也没跑满。 17k

- 代码： http-echo.go

```shell
root@xiaomi:/# ab -c 1000 -n 20000 http://127.0.0.1:8080/calllivecn
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
Completed 2000 requests
Completed 4000 requests
Completed 6000 requests
Completed 8000 requests
Completed 10000 requests
Completed 12000 requests
Completed 14000 requests
Completed 16000 requests
Completed 18000 requests
Completed 20000 requests
Finished 20000 requests


Server Software:        
Server Hostname:        127.0.0.1
Server Port:            8080

Document Path:          /calllivecn
Document Length:        12 bytes

Concurrency Level:      1000
Time taken for tests:   1.121 seconds
Complete requests:      20000
Failed requests:        0
Total transferred:      2580000 bytes
HTML transferred:       240000 bytes
Requests per second:    17844.51 [#/sec] (mean)
Time per request:       56.040 [ms] (mean)
Time per request:       0.056 [ms] (mean, across all concurrent requests)
Transfer rate:          2247.99 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   13   6.2     13      46
Processing:     4   30  15.2     29     250
Waiting:        0   26  15.2     24     240
Total:          7   43  15.3     42     262

Percentage of the requests served within a certain time (ms)
  50%     42
  66%     44
  75%     47
  80%     49
  90%     55
  95%     59
  98%     65
  99%     70
 100%    262 (longest request)

```

## 这里使用极简的 http-echo.py。

- 使用 selectors ： 这个在 linux 上底层使用的是 epoll。

- 这个也可以达到， 14k 😆

```shell
root@hthl:/# ab -c 1000 -n 10000 http://192.168.11.245:6789/
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 192.168.11.245 (be patient)
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


Server Software:        py
Server Hostname:        192.168.11.245
Server Port:            6789

Document Path:          /
Document Length:        13 bytes

Concurrency Level:      1000
Time taken for tests:   0.714 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      900000 bytes
HTML transferred:       130000 bytes
Requests per second:    14001.97 [#/sec] (mean)
Time per request:       71.418 [ms] (mean)
Time per request:       0.071 [ms] (mean, across all concurrent requests)
Transfer rate:          1230.64 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   26   5.0     26      39
Processing:    14   33   8.6     33      58
Waiting:        0   24   7.7     24      41
Total:         36   60   8.2     59      77

Percentage of the requests served within a certain time (ms)
  50%     59
  66%     64
  75%     67
  80%     68
  90%     71
  95%     74
  98%     75
  99%     76
 100%     77 (longest request)
```

## 这里使用极简的 http-echo-threadpool.py。

- 使用线程池 (thread 10个)

- 这个也可以达到， 12k 

```shell
root@hthl:/# ab -c 1000 -n 20000 http://localhost:6786/calllivecn
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 2000 requests
Completed 4000 requests
Completed 6000 requests
Completed 8000 requests
Completed 10000 requests
Completed 12000 requests
Completed 14000 requests
Completed 16000 requests
Completed 18000 requests
Completed 20000 requests
Finished 20000 requests


Server Software:        py
Server Hostname:        localhost
Server Port:            6786

Document Path:          /calllivecn
Document Length:        13 bytes

Concurrency Level:      1000
Time taken for tests:   1.657 seconds
Complete requests:      20000
Failed requests:        0
Total transferred:      1800000 bytes
HTML transferred:       260000 bytes
Requests per second:    12067.42 [#/sec] (mean)
Time per request:       82.868 [ms] (mean)
Time per request:       0.083 [ms] (mean, across all concurrent requests)
Transfer rate:          1060.61 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    4   6.8      0      33
Processing:    18   76  11.6     80      90
Waiting:        1   75  13.6     80      90
Total:         34   80   5.5     81      91

Percentage of the requests served within a certain time (ms)
  50%     81
  66%     82
  75%     83
  80%     83
  90%     85
  95%     86
  98%     87
  99%     88
 100%     91 (longest request)

```
## 这里使用 http-echo-asyncio.py。

- 这个，8.6k 

```shell
# 第一次
root@xiaomi:/# ab -c 2000 -n 10000 http://127.0.0.1:6785/calllivecn
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
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


Server Software:        py
Server Hostname:        127.0.0.1
Server Port:            6785

Document Path:          /calllivecn
Document Length:        13 bytes

Concurrency Level:      2000
Time taken for tests:   2.791 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      900000 bytes
HTML transferred:       130000 bytes
Requests per second:    3582.64 [#/sec] (mean)
Time per request:       558.248 [ms] (mean)
Time per request:       0.279 [ms] (mean, across all concurrent requests)
Transfer rate:          314.88 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0  121 325.9      2    1036
Processing:    13   67 205.5     16    1733
Waiting:        1   63 205.6     14    1729
Total:         15  188 486.4     17    2765

Percentage of the requests served within a certain time (ms)
  50%     17
  66%     18
  75%     22
  80%     38
  90%   1063
  95%   1492
  98%   1878
  99%   1909
 100%   2765 (longest request)


# 第二次
root@xiaomi:/# ab -c 200 -n 10000 http://127.0.0.1:6785/calllivecn
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking 127.0.0.1 (be patient)
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


Server Software:        py
Server Hostname:        127.0.0.1
Server Port:            6785

Document Path:          /calllivecn
Document Length:        13 bytes

Concurrency Level:      200
Time taken for tests:   1.176 seconds
Complete requests:      10000
Failed requests:        0
Total transferred:      900000 bytes
HTML transferred:       130000 bytes
Requests per second:    8503.67 [#/sec] (mean)
Time per request:       23.519 [ms] (mean)
Time per request:       0.118 [ms] (mean, across all concurrent requests)
Transfer rate:          747.39 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    6  64.8      2    1026
Processing:    11   17   2.7     16      32
Waiting:        1   14   3.0     13      29
Total:         11   23  65.1     18    1042

Percentage of the requests served within a certain time (ms)
  50%     18
  66%     18
  75%     18
  80%     19
  90%     19
  95%     24
  98%     32
  99%     33
 100%   1042 (longest request)
```


## linux 优化选项 (在新内核里，好多选项都没有了，还有选项发生了变化)

```shell
#表示开启重用。允许将TIME_WAIT sockets重新用于新的TCP连接，默认为0，表示关闭
1、net.ipv4.tcp_tw_reuse = 1

#表示开启TCP连接中TIME_WAIT sockets的快速回收，默认为0，表示关闭
#ubuntu 20.04 kernel 5.4 没有这个了
2、net.ipv4.tcp_tw_recycle = 1

#表示如果套接字由本端要求关闭，这个参数决定了它保持在FIN_WAIT_2状态的时间
#（可改为30，一般来说FIN_WAIT_2的连接也极少）
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

#同样有3个值,意思是:低于第一个值，TCP没有内存压力；在第二个值下，进入内存压力阶段；高于第三个值，TCP拒绝分配socket（内存单位是页）。
16、net.ipv4.tcp_mem = 94500000 915000000 927000000

#系统中最多有多少个TCP套接字不被关联到任何一个用户文件句柄上。
17、net.ipv4.tcp_max_orphans = 3276800

#每个网络接口接收数据包的速率比内核处理这些包的速率快时，允许送到队列的数据包的最大数目。
18、net.core.netdev_max_backlog = 8096

#表示开启SYNCookies。当出现SYN等待队列溢出时，启用cookies来处理，可防范少量SYN攻击，默认为1，表示开启。
19、net.ipv4.tcp_syncookies = 1
```
