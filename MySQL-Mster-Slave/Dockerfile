FROM alpine-py3:latest

COPY requireuments.txt /tmp/

RUN pip install -U pip || pip install --break-system-packages -U pip \
&& pip install --break-system-packages -r /tmp/requireuments.txt \
&& pip install --break-system-packages mycli


