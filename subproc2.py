
import subprocess
import fcntl, os
import time
import select

pipe = subprocess.Popen("sh", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

flags = fcntl.fcntl(pipe.stdout, fcntl.F_GETFL)
fcntl.fcntl(pipe.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

pipe.stdin.write("sleep 3; ls \n".encode())
pipe.stdin.flush()

poll = select.epoll()
poll.register(pipe.stdout.fileno())
epoll_list = poll.poll()
for fd, events in epoll_list:
    if fd == pipe.stdout.fileno() and select.EPOLLIN & events:
        out = pipe.stdout.read()
        print(out.decode())
