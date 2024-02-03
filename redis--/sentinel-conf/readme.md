# 配置redis sentinel

## 需要注意 requirepass: 一致, 还有masterauth: 

- podman run -d --name redis-sentinelX -v <dir/redis/sentinel26379.conf>:/etc/redis/ docker.io/library/redis:latest redis-sentinel /etc/redis/sentinel26379.conf --sentinel

