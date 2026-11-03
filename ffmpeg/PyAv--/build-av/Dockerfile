FROM ffmpeg-pyav-base:latest

ARG AV_VERSION

COPY run.sh /tmp/

RUN bash /tmp/run.sh \
&& rm -f /tmp/run.sh

CMD ["bash"]

