function checkSupportedCodecs() {
    const testCodecs = [
        { type: 'video/mp4', codec: 'avc1.640029' }, // H.264 基线
        { type: 'video/webm', codec: 'vp8' },
        { type: 'video/webm', codec: 'vp9' },
        { type: 'video/mp4', codec: 'hev1.1.6.L93.B0' }, // H.265/HEVC 示例配置
        { type: 'video/mp4', codec: 'hvc1.1.6.L93.B0' }, // H.265/HEVC 另一示例配置
        { type: 'video/webm', codec: 'av01.0.05M.08' }, // AV1 示例配置
        // 添加更多你感兴趣的编解码器测试
    ];

    const video = document.createElement('video');
    let supportedCodecs = [];

    testCodecs.forEach(test => {
        const mimeType = `${test.type}; codecs="${test.codec}"`;
        const canPlay = video.canPlayType(mimeType);
        if (canPlay === 'probably' || canPlay === 'maybe') {
            supportedCodecs.push(mimeType);
        }
    });

    console.log("支持的视频编解码器:");
    console.log(supportedCodecs.join("\n"));
}

checkSupportedCodecs();

