ARG TAG=latest
FROM ubuntu-base:${TAG}

RUN apt update \
&& apt -y install pgpool2

CMD ["pgpool", "-n", "-f", "/etc/pgpool2/pgpool.conf", "-F", "/etc/pgpool2/pcp.conf"]
