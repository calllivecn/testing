function isAV1Supported() {
    const video = document.createElement('video');
    return video.canPlayType('video/webm; codecs="av01.0.05M.08"') === "probably";
}

function isHEVCSupported() {
    const video = document.createElement('video');
    return !!video.canPlayType('video/mp4; codecs="hev1.1.6.L93.B0"') || 
           !!video.canPlayType('video/mp4; codecs="hvc1.1.6.L93.B0"');
}


if (isHEVCSupported()) {
    console.log("此浏览器支持H.265(HEVC)解码");
} else {
    console.log("此浏览器不支持H.265(HEVC)解码");
}

if (isAV1Supported()) {
    console.log("此浏览器支持AV1解码");
} else {
    console.log("此浏览器不支持AV1解码");
}
