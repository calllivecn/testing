FROM ubuntu-core:25.10

ARG AV_VERSION

COPY run.sh /tmp/

ENV LANG=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8

RUN bash /tmp/run.sh \
&& rm -f /tmp/run.sh

CMD ["bash"]

