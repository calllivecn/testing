FROM docker.io/library/postgres:17

RUN apt update \
&& apt -y install locales \
&& echo 'zh_CN.UTF-8 UTF-8' > /etc/locale.gen \
&& locale-gen

ENV LANG=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8
