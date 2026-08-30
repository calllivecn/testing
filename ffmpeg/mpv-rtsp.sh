
mpv --hwdec=nvdec --container-fps-override=30 --demuxer-lavf-o=use_wallclock_as_timestamps=1,rtsp_transport=tcp \
    --profile=low-latency \
    --no-cache \
    rtsp://192.168.1.5:5554
